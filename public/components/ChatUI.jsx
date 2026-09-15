import React from 'react'
import { Volume2, Loader2, Send } from 'lucide-react'

export default function ChatUI({
  messages,
  query,
  isLoading,
  user,
  selectedTemple,
  favorites,
  t,
  setQuery,
  handleSend,
  speakText,
  submitFeedback,
  toggleFavorite,
  threadEndRef
}) {
  return (
    <div className="chat-conversation">
      <div className="message-stream">
        {messages.map((m, idx) => (
          <div key={idx} className={`chat-bubble ${m.who}`}>
            {m.text}
            {m.who === 'bot' && (
              <>
                <button
                  onClick={() => speakText(m.text)}
                  className="listen-btn"
                >
                  <Volume2 size={14} /> {t.listen}
                </button>
                {m.id && (
                  <div className="feedback-actions">
                    {[1, 2, 3, 4, 5].map((rating) => (
                      <button
                        key={rating}
                        onClick={() => submitFeedback(m.id, rating)}
                        title={`Rate ${rating} out of 5`}
                      >
                        {rating}
                      </button>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="chat-bubble bot loading-bubble">
            <Loader2 size={16} className="animate-spin" />
            <span>Searching verified records...</span>
          </div>
        )}
        <div ref={threadEndRef} />
      </div>

      <div className="input-shell chat-input-shell">
        <input
          type="text"
          className="chat-input"
          placeholder={t.followUpPlaceholder}
          value={query}
          disabled={isLoading}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <button className="send-btn" onClick={() => handleSend()} disabled={isLoading}>
          <Send size={20} />
        </button>
      </div>
      {user && selectedTemple && (
        <button className="quick-chip" onClick={toggleFavorite}>
          {favorites.some((favorite) => favorite.item_type === 'temple' && favorite.item_key === selectedTemple)
            ? 'Remove temple from favorites'
            : 'Save temple to favorites'}
        </button>
      )}
    </div>
  )
}
