import { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import CsrfContext from './CsrfContext';
import { getMyPosts, deletePost } from './AppApi';

const MyPosts = () => {
  const csrf = useContext(CsrfContext);

  const [posts, setPosts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteLoading, setDeleteLoading] = useState<Record<number, boolean>>({});

  const fetchPosts = async () => {
    setLoading(true);
    try {
      const result = await getMyPosts();
      setPosts(result);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  const onDelete = async (postId: number) => {
    if (!window.confirm('Delete this listing?')) return;
    setDeleteLoading(prev => ({ ...prev, [postId]: true }));
    try {
      await deletePost(csrf, postId);
      setPosts(prev => prev.filter(p => p.id !== postId));
    } catch (e) {
      console.error(e);
    }
    setDeleteLoading(prev => ({ ...prev, [postId]: false }));
  };

  return (
    <div id="my-posts">
      <div className="post-list-header">
        <h2>My listings</h2>
        <Link to="/posts/new" className="btn-primary">+ New listing</Link>
      </div>

      {loading ? (
        <div className="post-loading">Loading...</div>
      ) : posts.length === 0 ? (
        <div className="post-empty">
          You have no listings yet. <Link to="/posts/new">Create one</Link>.
        </div>
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
                <span className="post-card-date">
                  {new Date(post.created_at).toLocaleDateString()}
                </span>
                <Link to={`/posts/${post.id}/edit`} className="btn-edit">Edit</Link>
                <button
                  className={`btn-danger ${deleteLoading[post.id] ? 'loading' : ''}`}
                  disabled={deleteLoading[post.id]}
                  onClick={() => onDelete(post.id)}
                >
                  {deleteLoading[post.id] ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MyPosts;
