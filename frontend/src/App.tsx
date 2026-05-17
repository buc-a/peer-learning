import React, { useState, useEffect, useReducer } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import axios from 'axios';

import ChatLogin from './ChatLogin';
import ChatRoomList from './ChatRoomList';
import ChatRoomDetail from './ChatRoomDetail';
import ChatLayout from './ChatLayout';
import CsrfContext from './CsrfContext';
import AuthContext from './AuthContext';
import ChatContext from './ChatContext';
import ChatSearch from './ChatSearch';
import {
  getConnectionToken, getSubscriptionToken, getCSRFToken,
  logout, addMessage, getRooms, getMessages, getRoom,
} from './AppApi';
import { WS_ENDPOINT, LOCAL_STORAGE_AUTH_INFO_KEY } from './AppSettings';

import {
  Centrifuge, type PublicationContext, type SubscriptionStateContext,
  type SubscribedContext, SubscriptionState
} from 'centrifuge';

const initialChatState = {
  rooms: [], // room IDs array for room sorting during rendering.
  roomsById: {},
  messagesByRoomId: {}
};

function reducer(state: any, action: any) {
  switch (action.type) {
    case 'CLEAR_CHAT_STATE': {
      return initialChatState;
    }
    case 'ADD_ROOMS': {
      const newRooms = action.payload.rooms;

      // Update roomsById with new rooms, avoiding duplicates.
      const updatedRoomsById = { ...state.roomsById };
      newRooms.forEach((room: any) => {
        if (!updatedRoomsById[room.id]) {
          updatedRoomsById[room.id] = room;
        }
      });

      // Merge new room IDs with existing ones, filtering out duplicates.
      const mergedRoomIds = [...new Set([...newRooms.map((room: any) => room.id), ...state.rooms])];

      // Sort mergedRoomIds based on bumped_at field in updatedRoomsById.
      const sortedRoomIds = mergedRoomIds.sort((a, b) => {
        const roomA = updatedRoomsById[a];
        const roomB = updatedRoomsById[b];
        // Compare RFC 3339 date strings is possible without transforming to Date.
        return roomB.bumped_at.localeCompare(roomA.bumped_at);
      });

      return {
        ...state,
        roomsById: updatedRoomsById,
        rooms: sortedRoomIds
      };
    }
    case 'DELETE_ROOM': {
      const roomId = action.payload.roomId;

      // Set the specified room to null instead of deleting it.
      const newRoomsById = {
        ...state.roomsById,
        [roomId]: null
      };

      // Remove the room from the rooms array.
      const newRooms = state.rooms.filter((id: any) => id !== roomId);

      // Remove associated messages.
      const { [roomId]: _deletedMessages, ...newMessagesByRoomId } = state.messagesByRoomId;

      return {
        ...state,
        roomsById: newRoomsById,
        rooms: newRooms,
        messagesByRoomId: newMessagesByRoomId
      };
    }
    case 'ADD_MESSAGES': {
      const roomId = action.payload.roomId;
      const newMessages = action.payload.messages;
      let currentMessages = state.messagesByRoomId[roomId] || [];

      // Combine current and new messages, then filter out duplicates.
      const combinedMessages = [...currentMessages, ...newMessages].filter(
        (message, index, self) =>
          index === self.findIndex(m => m.id === message.id)
      );

      // Sort the combined messages by id in ascending order.
      combinedMessages.sort((a, b) => a.id - b.id);

      // Find the message with the highest ID.
      const maxMessageId = combinedMessages.length > 0 ? combinedMessages[combinedMessages.length - 1].id : null;

      let needSort = false;

      // Update the roomsById object with the new last_message if necessary.
      const updatedRoomsById = { ...state.roomsById };
      if (maxMessageId !== null && updatedRoomsById[roomId] && (!updatedRoomsById[roomId].last_message || maxMessageId > updatedRoomsById[roomId].last_message.id)) {
        const newLastMessage = combinedMessages.find(message => message.id === maxMessageId);
        updatedRoomsById[roomId] = {
          ...updatedRoomsById[roomId],
          last_message: newLastMessage,
          bumped_at: newLastMessage.room.bumped_at,
        };
        needSort = true;
      }

      let updatedRooms = [...state.rooms];
      if (needSort) {
        updatedRooms = updatedRooms.sort((a: any, b: any) => {
          const roomA = updatedRoomsById[a];
          const roomB = updatedRoomsById[b];
          return roomB.bumped_at.localeCompare(roomA.bumped_at);
        });
      }

      return {
        ...state,
        messagesByRoomId: {
          ...state.messagesByRoomId,
          [roomId]: combinedMessages
        },
        roomsById: updatedRoomsById,
        rooms: updatedRooms,
      };
    }
    default:
      return state;
  }
}

const App: React.FC = () => {
  let localAuth: any = {};
  if (localStorage.getItem(LOCAL_STORAGE_AUTH_INFO_KEY)) {
    localAuth = JSON.parse(localStorage.getItem(LOCAL_STORAGE_AUTH_INFO_KEY)!)
  }
  const [authenticated, setAuthenticated] = useState<boolean>(localAuth.id !== undefined);
  const [userInfo, setUserInfo] = useState<any>(localAuth);
  const [csrf, setCSRF] = useState('');
  const [unrecoverableError, setUnrecoverableError] = useState('')
  const [chatState, dispatch] = useReducer(reducer, initialChatState);
  const [realTimeStatus, setRealTimeStatus] = useState('🔴')
  const [messageQueue, setMessageQueue] = useState<any[]>([]);

  useEffect(() => {
    if (messageQueue.length === 0) {
      return;
    }

    const processMessageAdded = async (body: any) => {
      const roomId = body.room.id
      const newMessage = body

      let room = chatState.roomsById[roomId]
      if (!room) {
        room = await fetchRoom(roomId)
        if (room) {
          dispatch({
            type: "ADD_ROOMS", payload: {
              rooms: [room]
            }
          })
        }
      }

      let messages = chatState.messagesByRoomId[roomId]
      if (!messages) {
        const fetched = await fetchMessages(roomId)
        if (fetched) {
          dispatch({
            type: "ADD_MESSAGES", payload: {
              roomId: roomId,
              messages: fetched
            }
          })
        }
        return;
      }

      dispatch({
        type: "ADD_MESSAGES", payload: {
          roomId: roomId,
          messages: [newMessage]
        }
      })
    }

    const processRoomCreated = async (body: any) => {
      // A new 1-on-1 room was created (the other user initiated it).
      dispatch({
        type: "ADD_ROOMS", payload: {
          rooms: [body]
        }
      })
    }

    const processMessage = async () => {
      const message = messageQueue[0];
      const { type, body } = message
      switch (type) {
        case 'message_added': {
          await processMessageAdded(body);
          break
        }
        case 'room_created': {
          await processRoomCreated(body);
          break
        }
        default:
          console.log('unsupported message type', type, body)
      }

      setMessageQueue(prevQueue => prevQueue.slice(1));
    };

    processMessage();
  }, [messageQueue, chatState]);

  const onPublication = (publication: any) => {
    console.log(publication)
    setMessageQueue(prevQueue => [...prevQueue, publication]);
  };

  useEffect(() => {
    if (!userInfo.id) {
      return;
    }

    let centrifuge: Centrifuge | null = null;

    const init = async () => {
      const rooms = await fetchRooms();
      if (rooms) {
        dispatch({
          type: 'ADD_ROOMS', payload: {
            'rooms': rooms
          }
        })
      }

      const personalChannel = 'personal:' + userInfo.id

      const getPersonalChannelSubscriptionToken = async () => {
        return getSubscriptionToken(personalChannel)
      }

      console.log("new Centrifuge")
      centrifuge = new Centrifuge(WS_ENDPOINT, {
        getToken: getConnectionToken,
        debug: true
      })

      const sub = centrifuge.newSubscription(personalChannel, {
        getToken: getPersonalChannelSubscriptionToken
      })
      sub.on('publication', (ctx: PublicationContext) => {
        onPublication(ctx.data)
      }).on('subscribed', (ctx: SubscribedContext) => {
        if (ctx.wasRecovering && !ctx.recovered) {
          setUnrecoverableError('State LOST - please reload the page')
        }
      })

      sub.on('state', (ctx: SubscriptionStateContext) => {
        if (ctx.newState == SubscriptionState.Subscribed) {
          setRealTimeStatus('🟢')
        } else {
          setRealTimeStatus('🔴')
        }
      })

      sub.subscribe()
      centrifuge.connect()
    }

    init()

    return () => {
      if (centrifuge) {
        console.log("disconnect Centrifuge")
        centrifuge.disconnect()
      }
    }
  }, [userInfo])

  useEffect(() => {
    const fetchCSRF = async () => {
      const token = await getCSRFToken()
      setCSRF(token)
    }
    fetchCSRF();
  }, []);

  const publishMessage = async (roomId: string, content: string) => {
    try {
      const message = await addMessage(csrf, roomId, content)
      return message
    } catch (err) {
      if (axios.isAxiosError(err) && err.response && err.response.status == 403) {
        onLoggedOut()
        return {}
      }
      setUnrecoverableError('Unhandled error - please reload a page')
      return {};
    }
  }

  const fetchMessages = async (roomId: string): Promise<any> => {
    try {
      const messages = await getMessages(roomId)
      // Note, need to reverse since we display old on top, newer on the bottom.
      return messages.reverse()
    } catch (err) {
      if (axios.isAxiosError(err) && err.response) {
        if (err.response.status == 403) {
          onLoggedOut()
          return null;
        } else if (err.response.status == 404) {
          return null;
        }
      }
      setUnrecoverableError('Unhandled error - please reload a page')
      return null;
    }
  };

  const fetchRoom = async (roomId: string): Promise<any> => {
    try {
      const room = await getRoom(roomId)
      return room
    } catch (err) {
      if (axios.isAxiosError(err) && err.response) {
        if (err.response.status == 403) {
          onLoggedOut()
          return null;
        } else if (err.response.status == 404) {
          return null;
        }
      }
      setUnrecoverableError('Unhandled error - please reload a page')
      return null;
    }
  };

  const fetchRooms = async (): Promise<any> => {
    try {
      const rooms = await getRooms()
      return rooms
    } catch (err) {
      if (axios.isAxiosError(err) && err.response) {
        if (err.response.status == 403) {
          onLoggedOut()
          return null;
        } else if (err.response.status == 404) {
          return null;
        }
      }
      setUnrecoverableError('Unhandled error - please reload a page')
      return null;
    }
  };

  const onLoginSuccess = async function (userInfo: any) {
    setUserInfo(userInfo);
    localStorage.setItem(LOCAL_STORAGE_AUTH_INFO_KEY, JSON.stringify(userInfo));
    const token = await getCSRFToken()
    setCSRF(token)
    setAuthenticated(true);
  }

  const onLoggedOut = async () => {
    setAuthenticated(false)
    setUnrecoverableError('')
    setUserInfo({});
    dispatch({
      type: "CLEAR_CHAT_STATE", payload: {}
    })
    localStorage.removeItem(LOCAL_STORAGE_AUTH_INFO_KEY);
  }

  const onLogout = async function () {
    try {
      await logout(csrf)
      await onLoggedOut()
      const token = await getCSRFToken()
      setCSRF(token)
    } catch (err) {
      if (axios.isAxiosError(err) && err.response) {
        if (err.response.status == 403) {
          await onLoggedOut()
          return
        }
      }
      setUnrecoverableError('Unhandled error - please reload a page')
    }
  }

  return (
    <CsrfContext.Provider value={csrf}>
      <AuthContext.Provider value={userInfo}>
        {authenticated ? (
          <ChatContext.Provider value={{ state: chatState, dispatch }}>
            <Router>
              <ChatLayout
                realTimeStatus={realTimeStatus}
                unrecoverableError={unrecoverableError}
                onLogout={onLogout}
              >
                <Routes>
                  <Route path="/" element={<ChatRoomList />} />
                  <Route path="/search" element={<ChatSearch fetchRoom={fetchRoom} />} />
                  <Route path="/rooms/:id" element={
                    <ChatRoomDetail
                      fetchRoom={fetchRoom}
                      fetchMessages={fetchMessages}
                      publishMessage={publishMessage}
                    />
                  } />
                </Routes>
              </ChatLayout>
            </Router>
          </ChatContext.Provider>
        ) : (
          <ChatLogin onSuccess={onLoginSuccess} />
        )}
      </AuthContext.Provider>
    </CsrfContext.Provider>
  );
};

export default App;
