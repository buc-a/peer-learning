import React, { useState, useContext } from 'react';
import CsrfContext from './CsrfContext';
import { login } from './AppApi';

interface ChatLoginProps {
  onSuccess: (userInfo: any) => void;
}

const ChatLogin: React.FC<ChatLoginProps> = ({ onSuccess }) => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const csrf = useContext(CsrfContext)

  const handleLogin = async () => {
    setLoading(true)
    try {
      const resp = await login(csrf, username, password)
      onSuccess(resp);
    } catch (err) {
      console.error('Login failed:', err);
    }
    setLoading(false)
  };

  return (
    <form id="chat-login" onSubmit={(e) => {
      e.preventDefault()
      handleLogin()
    }}>
      <div id="chat-login-logo-container">
        <h1 id="chat-login-title">Peer Learning</h1>
        <p id="chat-login-subtitle">Find someone to learn from or teach</p>
      </div>
      <div className="input-container">
        <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
      </div>
      <div className="input-container">
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" autoComplete='currentPassword' />
      </div>
      <div className='login-button-container'>
        <button disabled={loading} className={`${(loading) ? 'loading' : ''}`}>Login</button>
      </div>
    </form>
  );
};

export default ChatLogin;
