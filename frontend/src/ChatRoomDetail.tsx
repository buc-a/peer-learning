import { useState, useEffect, useContext, useRef, type UIEvent } from 'react';
import { useParams } from 'react-router-dom';
import AuthContext from './AuthContext';
import ChatContext from './ChatContext';

/**
 * For a 1:1 chat, return the other participant's username.
 * Falls back to room.name if members are not available.
 */
function getChatTitle(room: any, currentUserId: number): string {
  if (room.members && room.members.length > 0) {
    const other = room.members.find((m: any) => m.id !== currentUserId);
    if (other) return other.username;
  }
  return room.name || '';
}

interface ChatRoomDetailProps {
  fetchRoom: (roomId: string) => Promise<any>
  fetchMessages: (roomId: string) => Promise<any[]>
  publishMessage: (roomId: string, content: string) => Promise<any>
}

const ChatRoomDetail: React.FC<ChatRoomDetailProps> = ({ fetchRoom, fetchMessages, publishMessage }) => {
  const { id } = useParams() as { id: string };
  const userInfo = useContext(AuthContext);
  const { state, dispatch } = useContext(ChatContext);
  const [content, setContent] = useState('')
  const [messagesLoading, setMessagesLoading] = useState(false)
  const [roomLoading, setRoomLoading] = useState(false)
  const [sendLoading, setSendLoading] = useState(false)
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (messagesLoading) return
    const init = async () => {
      setMessagesLoading(true)
      if (!state.messagesByRoomId[id]) {
        const messages = await fetchMessages(id)
        if (messages === null) {
          setNotFound(true);
        } else {
          setNotFound(false);
          dispatch({
            type: "ADD_MESSAGES", payload: {
              roomId: id,
              messages: messages
            }
          })
        }
      }
      setMessagesLoading(false)
    }
    init()
  }, [id, state.messagesByRoomId, fetchMessages]);

  useEffect(() => {
    if (roomLoading) return
    const init = async () => {
      setRoomLoading(true)
      if (!state.roomsById[id]) {
        const room = await fetchRoom(id)
        if (room === null) {
          setNotFound(true);
        } else {
          setNotFound(false);
          dispatch({
            type: "ADD_ROOMS", payload: {
              rooms: [room],
            }
          })
        }
      }
      setRoomLoading(false)
    }
    init()
  }, [id, state.roomsById, fetchRoom]);

  const room = state.roomsById[id] || {};
  const messages = state.messagesByRoomId[id] || [];

  const messagesEndRef = useRef<any>(null);

  const scrollToBottom = () => {
    const container = messagesEndRef.current;
    if (container) {
      container.scrollTo({ top: container.scrollHeight, behavior: 'auto' });
    }
  };

  const getTime = (timeString: string) => {
    const date = new Date(timeString);
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
  }

  const onFormSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (sendLoading) return;
    setSendLoading(true)
    try {
      const message = await publishMessage(id!, content)
      dispatch({
        type: "ADD_MESSAGES", payload: {
          roomId: id,
          messages: [message]
        }
      })
      setContent('')
    } catch (e) {
      console.log(e)
    }
    setSendLoading(false)
  }

  const handleScroll = (e: UIEvent<HTMLDivElement>) => {
    const container = (e.target as HTMLElement);
    if (!container) return;
    const threshold = 40;
    const position = container.scrollTop + container.offsetHeight;
    const height = container.scrollHeight;
    setIsAtBottom(position + threshold >= height)
  };

  const [isAtBottom, setIsAtBottom] = useState(true);

  useEffect(() => {
    if (isAtBottom) {
      scrollToBottom();
    }
  }, [messages, isAtBottom]);

  return (
    <div id="chat-room">
      {notFound ? (
        <div id="room-not-found">
          NOT A MEMBER OF THIS ROOM
        </div>
      ) : (
        <>
          <div id="room-description">
            <span id="room-name">{getChatTitle(room, userInfo.id)}</span>
          </div>
          <div id="room-messages" onScroll={handleScroll} ref={messagesEndRef}>
            {messages.map((message: any) => (
              <div key={message.id} className={`room-message ${(userInfo.id == message.user.id) ? 'room-message-mine' : 'room-message-not-mine'}`}>
                <div className='message-avatar'>
                  <div className='message-avatar-initial'>
                    {message.user.username.charAt(0).toUpperCase()}
                  </div>
                </div>
                <div className='message-bubble'>
                  <div className='message-meta'>
                    <div className='message-author'>
                      {message.user.username}
                    </div>
                    <div className='message-time'>
                      {getTime(message.created_at)}
                    </div>
                  </div>
                  <div className='message-content'>
                    {message.content}
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div id="chat-input-container" className={`${sendLoading ? 'loading' : ''}`}>
            <form onSubmit={onFormSubmit}>
              <input
                type="text"
                autoComplete="off"
                value={content}
                placeholder="Enter message..."
                onChange={e => setContent(e.currentTarget.value)}
                required
              />
            </form>
          </div>
        </>
      )}
    </div>
  );
};

export default ChatRoomDetail;
