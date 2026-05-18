import { useState, useEffect, useContext } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import CsrfContext from './CsrfContext';
import AuthContext from './AuthContext';
import ChatContext from './ChatContext';
import { getPost, deletePost, startChat } from './AppApi';

const PostDetail = () => {
  const { id } = useParams<{ id: string }>();
  const csrf = useContext(CsrfContext);
  const userInfo = useContext(AuthContext);
  const { dispatch } = useContext(ChatContext);
  const navigate = useNavigate();

  const [post, setPost] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await getPost(id!);
        setPost(result);
      } catch (e: any) {
        if (e?.response?.status === 404) {
          setNotFound(true);
        } else {
          console.error(e);
        }
      }
      setLoading(false);
    };
    fetchData();
  }, [id]);

  const onStartChat = async () => {
    if (!post) return;
    setChatLoading(true);
    try {
      const room = await startChat(csrf, post.author.id);
      dispatch({ type: 'ADD_ROOMS', payload: { rooms: [room] } });
      navigate(`/chat/rooms/${room.id}`);
    } catch (e) {
      console.error(e);
    }
    setChatLoading(false);
  };

  const onDelete = async () => {
    if (!post) return;
    if (!window.confirm('Delete this listing?')) return;
    setDeleteLoading(true);
    try {
      await deletePost(csrf, post.id);
      navigate('/posts/my');
    } catch (e) {
      console.error(e);
    }
    setDeleteLoading(false);
  };

  if (loading) {
    return <div className="post-loading">Loading...</div>;
  }

  if (notFound || !post) {
    return (
      <div className="post-not-found">
        <p>Listing not found.</p>
        <Link to="/posts">Back to listings</Link>
      </div>
    );
  }

  return (
    <div id="post-detail">
      <div className="post-detail-header">
        <Link to="/posts" className="back-link">← All listings</Link>
      </div>

      <div className="post-detail-card">
        <h2 className="post-detail-title">{post.title}</h2>
        <span className="post-detail-skill">{post.skill}</span>
        <p className="post-detail-description">{post.description}</p>

        <div className="post-detail-meta">
          <span className="post-detail-author">by {post.author.username}</span>
          <span className="post-detail-date">
            {new Date(post.created_at).toLocaleDateString()}
          </span>
        </div>

        <div className="post-detail-actions">
          {!post.is_owner && (
            <button
              className={`btn-primary ${chatLoading ? 'loading' : ''}`}
              disabled={chatLoading}
              onClick={onStartChat}
            >
              {chatLoading ? 'Opening chat...' : 'Message author'}
            </button>
          )}
          {post.is_owner && (
            <>
              <Link to={`/posts/${post.id}/edit`} className="btn-edit">Edit</Link>
              <button
                className={`btn-danger ${deleteLoading ? 'loading' : ''}`}
                disabled={deleteLoading}
                onClick={onDelete}
              >
                {deleteLoading ? 'Deleting...' : 'Delete'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default PostDetail;
