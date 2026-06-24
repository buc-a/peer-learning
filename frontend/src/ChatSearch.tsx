import { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import CsrfContext from './CsrfContext';
import ChatContext from './ChatContext';
import { searchUsers, startChat } from './AppApi';

const ChatSearch: React.FC = () => {
  const csrf = useContext(CsrfContext);
  const { dispatch } = useContext(ChatContext);
  const navigate = useNavigate();
  const [users, setUsers] = useState<any[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState<Record<number, boolean>>({});

  useEffect(() => {
    const fetchUsers = async () => {
      const result = await searchUsers(query || undefined);
      setUsers(result);
    };
    fetchUsers();
  }, [query]);

  const setLoadingFlag = (userId: number, value: boolean) => {
    setLoading(prev => ({ ...prev, [userId]: value }));
  };

  const onStartChat = async (userId: number) => {
    setLoadingFlag(userId, true);
    try {
      const room = await startChat(csrf, userId);
      dispatch({
        type: 'ADD_ROOMS',
        payload: { rooms: [room] }
      });
      navigate(`/chat/rooms/${room.id}`);
    } catch (e) {
      console.error(e);
    }
    setLoadingFlag(userId, false);
  };

  return (
    <div id="chat-rooms">
      <div id="user-search-bar">
        <input
          type="text"
          placeholder="Search users..."
          value={query}
          onChange={e => setQuery(e.currentTarget.value)}
          autoComplete="off"
        />
      </div>
      {users.map((user: any) => (
        <div className="chat-room-block" key={user.id}>
          <div className="room-search-item">
            <span>{user.username}</span>
            <span className="room-actions">
              <button
                disabled={loading[user.id] === true}
                className={loading[user.id] ? 'loading' : ''}
                onClick={() => onStartChat(user.id)}
              >
                {loading[user.id] ? '...' : 'Message'}
              </button>
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ChatSearch;
