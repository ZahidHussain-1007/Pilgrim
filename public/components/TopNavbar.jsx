import React from 'react'
import { Home, Info, Settings } from 'lucide-react'

function GoogleMark() {
  return (
    <svg className="google-mark" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#4285F4" d="M21.8 12.23c0-.71-.06-1.39-.18-2.05H12v3.88h5.5a4.7 4.7 0 0 1-2.04 3.08v2.51h3.32c1.94-1.79 3.02-4.42 3.02-7.42Z" />
      <path fill="#34A853" d="M12 22c2.75 0 5.05-.91 6.74-2.35l-3.32-2.51c-.92.62-2.1.99-3.42.99-2.64 0-4.88-1.78-5.68-4.18H2.89v2.59A10.18 10.18 0 0 0 12 22Z" />
      <path fill="#FBBC05" d="M6.32 13.95A6.11 6.11 0 0 1 6 12c0-.68.12-1.34.32-1.95V7.46H2.89A10 10 0 0 0 1.8 12c0 1.62.39 3.15 1.09 4.54l3.43-2.59Z" />
      <path fill="#EA4335" d="M12 5.87c1.5 0 2.85.52 3.91 1.54l2.93-2.93C17.04 2.8 14.75 2 12 2a10.18 10.18 0 0 0-9.11 5.46l3.43 2.59C7.12 7.65 9.36 5.87 12 5.87Z" />
    </svg>
  )
}

export default function TopNavbar({ user, t, signInWithGoogle, signOut, handleTabChange, startNewConversation }) {
  return (
    <header className="top-navbar">
      <div className="nav-brand">
        <span className="brand-om">ॐ</span>
        <span className="brand-title">PilgrimAI</span>
      </div>
      <div className="nav-links">
        <button className="nav-link nav-action" onClick={startNewConversation}>
          <Home size={15} /> Home
        </button>
        <button className="nav-link nav-action" onClick={() => handleTabChange('About')}>
          <Info size={15} /> {t.navAbout}
        </button>
        {user ? (
          <div className="signed-in-account">
            {user.avatarUrl ? (
              <img className="signed-in-avatar" src={user.avatarUrl} alt="" referrerPolicy="no-referrer" />
            ) : (
              <span className="signed-in-avatar signed-in-avatar-fallback" aria-hidden="true">{user.name?.charAt(0) || 'P'}</span>
            )}
            <span className="signed-in-name">{user.name}</span>
            <button className="sign-out-button" onClick={signOut} title="Sign out">Sign out</button>
          </div>
        ) : (
          <button className="google-login-button" onClick={signInWithGoogle}>
            <GoogleMark />
            <span>Continue with Google</span>
          </button>
        )}
        <button className="settings-nav-button" onClick={() => handleTabChange('Settings')} title="Settings" aria-label="Settings">
          <Settings size={18} />
        </button>
      </div>
    </header>
  )
}
