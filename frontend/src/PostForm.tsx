import { useState, useEffect, useContext } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import CsrfContext from './CsrfContext';
import { getPost, createPost, updatePost } from './AppApi';

const PostForm = () => {
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const csrf = useContext(CsrfContext);
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [skill, setSkill] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetchLoading, setFetchLoading] = useState(isEdit);
  const [notFound, setNotFound] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!isEdit) return;
    const fetchData = async () => {
      try {
        const post = await getPost(id!);
        setTitle(post.title);
        setDescription(post.description);
        setSkill(post.skill);
      } catch (e: any) {
        if (e?.response?.status === 404 || e?.response?.status === 403) {
          setNotFound(true);
        } else {
          console.error(e);
        }
      }
      setFetchLoading(false);
    };
    fetchData();
  }, [id, isEdit]);

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!title.trim()) errs.title = 'Title is required.';
    if (!skill.trim()) errs.skill = 'Skill is required.';
    if (!description.trim()) errs.description = 'Description is required.';
    return errs;
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }
    setErrors({});
    setLoading(true);
    try {
      const data = { title: title.trim(), description: description.trim(), skill: skill.trim() };
      if (isEdit) {
        await updatePost(csrf, id!, data);
        navigate(`/posts/${id}`);
      } else {
        const post = await createPost(csrf, data);
        navigate(`/posts/${post.id}`);
      }
    } catch (e: any) {
      if (e?.response?.data) {
        const serverErrors: Record<string, string> = {};
        for (const [key, val] of Object.entries(e.response.data)) {
          serverErrors[key] = Array.isArray(val) ? (val as string[]).join(' ') : String(val);
        }
        setErrors(serverErrors);
      } else {
        console.error(e);
      }
    }
    setLoading(false);
  };

  if (fetchLoading) {
    return <div className="post-loading">Loading...</div>;
  }

  if (notFound) {
    return (
      <div className="post-not-found">
        <p>Listing not found.</p>
        <Link to="/posts/my">My listings</Link>
      </div>
    );
  }

  return (
    <div id="post-form">
      <div className="post-form-header">
        <Link to={isEdit ? `/posts/${id}` : '/posts'} className="back-link">
          ← {isEdit ? 'Back to listing' : 'All listings'}
        </Link>
        <h2>{isEdit ? 'Edit listing' : 'New listing'}</h2>
      </div>

      <form className="post-form-body" onSubmit={onSubmit}>
        <div className="form-group">
          <label htmlFor="post-title">Title</label>
          <input
            id="post-title"
            type="text"
            value={title}
            onChange={e => setTitle(e.currentTarget.value)}
            placeholder="e.g. Python tutoring for beginners"
            autoComplete="off"
          />
          {errors.title && <span className="form-error">{errors.title}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="post-skill">Skill</label>
          <input
            id="post-skill"
            type="text"
            value={skill}
            onChange={e => setSkill(e.currentTarget.value)}
            placeholder="e.g. Python, Guitar, Spanish..."
            autoComplete="off"
          />
          {errors.skill && <span className="form-error">{errors.skill}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="post-description">Description</label>
          <textarea
            id="post-description"
            value={description}
            onChange={e => setDescription(e.currentTarget.value)}
            placeholder="Describe what you can teach, your experience, availability..."
            rows={5}
          />
          {errors.description && <span className="form-error">{errors.description}</span>}
        </div>

        {errors.non_field_errors && (
          <div className="form-error form-error-global">{errors.non_field_errors}</div>
        )}

        <div className="form-actions">
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Saving...' : isEdit ? 'Save changes' : 'Create listing'}
          </button>
          <Link to={isEdit ? `/posts/${id}` : '/posts'} className="btn-cancel">
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
};

export default PostForm;
