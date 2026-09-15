import React from 'react'
import { Landmark } from 'lucide-react'
import { TEMPLES_LIST, CONSTELLATION_POSITIONS } from '../features/temples.js'

export default function TempleDiscovery({
  templeSearch,
  setTempleSearch,
  selectedDiscoveryTemple,
  selectDiscoveryTemple,
  openTempleExperience,
  openPurpose,
  onAskAI
}) {
  return (
    <section className="temple-discovery" aria-label="Interactive Sacred Telangana">
      <div className="temple-discovery-hero">
        <span className="temple-discovery-kicker">THE SACRED CIRCUIT</span>
        <h1>DISCOVER<br />SACRED TELANGANA</h1>
        <p>23 sacred destinations. One journey through Telangana's spiritual heritage.</p>
        <label className="temple-discovery-search" htmlFor="temple-search">
          <Landmark size={20} aria-hidden="true" />
          <input id="temple-search" type="search" placeholder="Search temples, deities, districts or places..." value={templeSearch} onChange={(event) => setTempleSearch(event.target.value)} />
        </label>
      </div>

      <div className="temple-discovery-section-heading temple-discovery-map-heading">
        <div><span className="temple-discovery-eyebrow">THE SACRED MAP</span><h2>Explore Telangana's temples and discover your next pilgrimage.</h2></div>
        <span className="temple-discovery-count">23 TEMPLES / ONE JOURNEY</span>
      </div>
      <div className="temple-discovery-map-layout">
        <div className="temple-discovery-map" aria-label="Stylized sacred temple map">
          <div className="temple-discovery-map-outline" aria-hidden="true"><span /><span /><span /><span /></div>
          <div className="temple-discovery-map-label">TELANGANA<br /><small>SACRED CONSTELLATION</small></div>
          <div className="temple-discovery-map-stars" aria-hidden="true" />
          <div className="temple-discovery-map-markers">
            {TEMPLES_LIST.map((temple) => <button type="button" key={temple.slug} className={`temple-discovery-marker ${selectedDiscoveryTemple.slug === temple.slug ? 'selected' : ''}`} style={CONSTELLATION_POSITIONS[temple.slug]} onClick={() => selectDiscoveryTemple(temple)} aria-label={`Explore ${temple.name}`}><span className="temple-discovery-marker-dot" /><span className="temple-discovery-marker-name">{temple.name}</span><span className="temple-discovery-marker-tooltip"><strong>{temple.name}</strong><small>Telangana</small><em>Explore Temple <span aria-hidden="true">→</span></em></span></button>)}
          </div>
          <div className="temple-discovery-map-legend"><span><i /> Selected destination</span><span><i /> 23 sacred records</span></div>
        </div>
        <aside className="temple-discovery-selected" aria-live="polite">
          <span className="temple-discovery-eyebrow">SELECTED DESTINATION</span>
          <span className="temple-discovery-selected-number">{String(TEMPLES_LIST.indexOf(selectedDiscoveryTemple) + 1).padStart(2, '0')} / 23</span>
          <h3>{selectedDiscoveryTemple.name}</h3>
          <p>{selectedDiscoveryTemple.full}</p>
          <span className="temple-discovery-selected-location">Telangana</span>
          {selectedDiscoveryTemple.slug === 'yadadri' && <span className="temple-discovery-selected-badge">✦ DRONE EXPERIENCE</span>}
          <div className="temple-discovery-selected-actions"><button type="button" className="temple-discovery-primary" onClick={() => openTempleExperience(selectedDiscoveryTemple)}>Explore Temple <span aria-hidden="true">→</span></button><button type="button" onClick={() => onAskAI ? onAskAI(selectedDiscoveryTemple) : openPurpose('Darshan')}>Ask AI</button></div>
        </aside>
      </div>

      <div className="temple-discovery-section-heading temple-discovery-purpose-heading"><div><span className="temple-discovery-eyebrow">PLAN YOUR DAY</span><h2>Explore by Purpose</h2></div></div>
      <div className="temple-discovery-purpose-grid">{[['🙏', 'Darshan'], ['🪔', 'Rituals'], ['🗺️', 'Travel'], ['🏨', 'Accommodation'], ['🍽️', 'Restaurants'], ['🚑', 'Emergency']].map(([icon, label]) => <button type="button" className="temple-discovery-purpose" key={label} onClick={() => openPurpose(label)}><span>{icon}</span><strong>{label}</strong><small>Discover more <span aria-hidden="true">↗</span></small></button>)}</div>
    </section>
  )
}
