import React from 'react'

export default function MyJourney({ user, conversations, favorites, loadConversation }) {
  return (
    <div className="chat-conversation">
      <h2>My Journey</h2>
      {user ? conversations.map((conversation) => (
        <button key={conversation.id} className="quick-chip" onClick={() => loadConversation(conversation.id)}>
          {conversation.title || 'Untitled conversation'}
        </button>
      )) : <p>Sign in to view saved conversations and favorites.</p>}
      {user && favorites.length > 0 && (
        <>
          <h3>Favorites</h3>
          {favorites.map((favorite) => (
            <p key={favorite.id}>{favorite.item_type}: {favorite.item_key}</p>
          ))}
        </>
      )}
    </div>
  )
}
