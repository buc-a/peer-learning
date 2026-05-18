import { useState, useEffect, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import CsrfContext from './CsrfContext';
import AuthContext from './AuthContext';
import ChatContext from './ChatContext';
import { getPosts, startChat } from './AppApi';

const PostList = () => {
  const csrf = useContext(CsrfContext);
  const userInfo = useContext(AuthContext);
  const { dispatch } = useContext(ChatContext);
  const navigate = useNavigate();

  const [posts, setPosts] = useState<any[]>([]);
  const [skillFilter, setSkillFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatLoading, setChatLoading] = useState<Record<number, boolean>>({});

  const fetchPosts = async (skill?: string) => {
    setLoading(true);
    try {
      const result = await getPosts(skill ? { skill } : undefined);
      setPosts(result);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  const onSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchPosts(skillFilter || undefined);
  };

  const onStartChat = async (authorId: number) => {
    setChatLoading(prev => ({ ...prev, [authorId]: true }));
    try {
      const room = await startChat(csrf, authorId);
      dispatch({ type: 'ADD_ROOMS', payload: { rooms: [room] } });
      navigate(`/chat/rooms/${room.id}`);
    } catch (e) {
      console.error(e);
    }
    setChatLoading(prev => ({ ...prev, [authorId]: false }));
  };

  return (
    <div id="post-list">
      <div className="post-list-header">
        <h2>Skill Listings</h2>
        <Link to="/posts/new" className="btn-primary">+ New listing</Link>
      </div>

      <form className="post-search-form" onSubmit={onSearch}>
        <input
          type="text"
          placeholder="Filter by skill..."
          value={skillFilter}
          onChange={e => setSkillFilter(e.currentTarget.value)}
          autoComplete="off"
        />
        <button type="submit">Search</button>
        {skillFilter && (
          <button type="button" onClick={() => { setSkillFilter(''); fetchPosts(); }}>
            Clear
          </button>
        )}
      </form>

      {loading ? (
        <div className="post-loading">Loading...</div>
      ) : posts.length === 0 ? (
        <div className="post-empty">No listings found.</div>
      ) : (
        <div className="post-cards">
          {posts.map((post: any) => (
            <div className="post-card" key={post.id}>
              <div className="post-card-body">
                <Link to={`/posts/${post.id}`}>
                  <h3 className="post-card-title">{post.title}</h3>
                </Link>
                <span className="post-card-skill">{post.skill}</span>
                <p className="post-card-description">{post.description}</p>
              </div>
              <div className="post-card-footer">
                <span className="post-card-author">by {post.author.username}</span>
                {post.author.id !== userInfo.id && (
                  <button
                    className={`btn-chat ${chatLoading[post.author.id] ? 'loading' : ''}`}
                    disabled={chatLoading[post.author.id]}
                    onClick={() => onStartChat(post.author.id)}
                  >
                    Message
                  </button>
                )}
                {post.is_owner && (
                  <Link to={`/posts/${post.id}/edit`} className="btn-edit">Edit</Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PostList;
