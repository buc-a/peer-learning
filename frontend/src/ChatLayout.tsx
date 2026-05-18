import React, { useContext } from 'react';
import { NavLink } from 'react-router-dom';
import AuthContext from './AuthContext';

interface ChatLayoutProps {
  children: any
  realTimeStatus: string
  unrecoverableError: string
  onLogout: () => void
}

const ChatLayout: React.FC<ChatLayoutProps> = ({ children, realTimeStatus, unrecoverableError, onLogout }) => {
  const userInfo = useContext(AuthContext);

  return (
    <div id='chat-layout'>
      <div id='chat-navbar'>
        <NavLink to={`/chat`} className={({ isActive }) => isActive ? "navbar-active-link" : ""}>My chats</NavLink>
        <NavLink to={`/chat/search`} className={({ isActive }) => isActive ? "navbar-active-link" : ""}>New chat</NavLink>
        <NavLink to={`/posts`} className={({ isActive }) => isActive ? "navbar-active-link" : ""}>Listings</NavLink>
        <NavLink to={`/posts/my`} className={({ isActive }) => isActive ? "navbar-active-link" : ""}>My listings</NavLink>
        <span id="logout-container">
          <span id="status" className={'status-'+ realTimeStatus}>{realTimeStatus}</span>
          &nbsp;
          &nbsp;
          <span id="user">{userInfo.username}</span>
          &nbsp;
          <a href='#' id="logout-button" onClick={(e) => { e.preventDefault(); onLogout() }}>
            Logout
          </a>
        </span>
      </div>
      {unrecoverableError != '' ? (
        <div id='chat-state-lost'>
          {unrecoverableError}
        </div>
      ) : (
        <div id='chat-content'>
          {children}
        </div>
      )}
    </div>
  );
}

export default ChatLayout;
