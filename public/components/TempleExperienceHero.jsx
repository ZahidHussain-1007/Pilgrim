import React from 'react'

export default function TempleExperienceHero({
  selectedDiscoveryTemple,
  videoUrl,
  setSelectedTemple,
  handleTabChange,
  onBackToTemples,
  onAskAI
}) {
  return (
    <section className="yadadri-hero" aria-label="Yadadri temple hero">
      {videoUrl ? (
        <iframe
          className="yadadri-video"
          src={videoUrl}
          title={`${selectedDiscoveryTemple.name} temple drone video`}
          tabIndex={-1}
          aria-hidden="true"
          allow="autoplay; encrypted-media"
          allowFullScreen={false}
        />
      ) : <div className="yadadri-fallback" aria-hidden="true" />}
      <div className="yadadri-video-shield" aria-hidden="true" />
      <div className="yadadri-overlay" />
      <button className="yadadri-back" type="button" onClick={onBackToTemples}>← Back to Temples</button>
      <div className="yadadri-content">
        <span className="yadadri-label">{selectedDiscoveryTemple.name.toUpperCase()}</span>
        <h1>{selectedDiscoveryTemple.full}</h1>
        <p>Telangana</p>
        <div className="yadadri-actions">
          <button type="button">Explore Temple</button>
          <button type="button" onClick={() => {
            if (onAskAI) {
              onAskAI(selectedDiscoveryTemple)
            } else {
              setSelectedTemple(selectedDiscoveryTemple.slug)
              handleTabChange('Home')
            }
          }}>Ask AI</button>
        </div>
      </div>
    </section>
  )
}
