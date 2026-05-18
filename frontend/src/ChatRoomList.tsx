import { useContext } from 'react';
import { Link } from 'react-router-dom';
import AuthContext from './AuthContext';
import ChatContext from './ChatContext'

/**
 * For a 1:1 chat, return the other participant's username.
 * Falls back to room.name if members are not available.
 */
function getChatTitle(room: any, currentUserId: number): string {
  if (room.members && room.members.length > 0) {
    const other = room.members.find((m: any) => m.id !== currentUserId);
    if (other) return other.username;
  }
  return room.name;
}

const ChatRoomList = () => {
  const { state } = useContext(ChatContext);
  const userInfo = useContext(AuthContext);

  return (
    <div id="chat-rooms">
      {state.rooms.map((roomId: number) => {
        const room = state.roomsById[roomId]
        const title = getChatTitle(room, userInfo.id);
        return (
          <div className="chat-room-block" key={room.id}>
            <Link to={`/chat/rooms/${room.id}`}>
              <div className="left-column">
                <span className="name">{title}</span>
                <span className="message-content">
                  {room.last_message ? (
                    <span>
                      <span className="message-content-author">{room.last_message.user.username}:</span>
                      &nbsp;
                      {room.last_message.content}
                    </span>
                  ) : null}
                </span>
              </div>
            </Link>
          </div>
        )
      })}
    </div>
  );
};

export default ChatRoomList;
