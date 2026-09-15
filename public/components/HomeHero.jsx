import React from 'react'
import { Mic, Send } from 'lucide-react'

export default function HomeHero({
  t,
  isListening,
  toggleVoice,
  handleTabChange,
  handleSend,
  beginPilgrimagePlanning,
  query,
  setQuery
}) {
  return (
    <div className="center-hero home-hero">
      <div className="center-om">ॐ</div>
      <h1 className="hero-heading">{t.heading}</h1>
      <p className="hero-subtext">Your AI companion for temples, darshan, travel, stays, rituals, and pilgrimage planning.</p>

      <button
        className={`mic-circle-btn ${isListening ? 'listening' : ''}`}
        onClick={toggleVoice}
        title="Voice Search"
      >
        <Mic size={28} />
      </button>
      <span className="home-voice-label">Speak your pilgrimage question</span>

      <div className="quick-chips-row">
        <button
          className="quick-chip"
          onClick={() => handleTabChange('Temples')}
        >
          Explore Sacred Telangana
        </button>
        <button
          className="quick-chip"
          onClick={beginPilgrimagePlanning}
        >
          Plan My Pilgrimage
        </button>
        <button
          className="quick-chip"
          onClick={() => {
            handleTabChange('Darshan Booking')
            handleSend('Find darshan and rituals')
          }}
        >
          Find Darshan &amp; Rituals
        </button>
      </div>

      <div className="input-shell">
        <input
          type="text"
          className="chat-input"
          placeholder={t.inputPlaceholder}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          autoFocus
        />
        <button className="send-btn" onClick={() => handleSend()} title="Send">
          <Send size={20} />
        </button>
      </div>

      <div className="home-plan-cta">
        <button className="home-plan-button" type="button" onClick={beginPilgrimagePlanning}>
          <span>✦ Plan My Trip</span><span aria-hidden="true">→</span>
        </button>
      </div>
      <p className="home-capability-strip">🛕 Temples · 🙏 Darshan · 🗺️ Travel · 🏨 Stay · 🪔 Rituals · 🧭 Trip Planning</p>
    </div>
  )
}
