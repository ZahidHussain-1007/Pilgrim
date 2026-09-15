import React from 'react'
import {
  Landmark,
  Compass,
  Milestone,
  Plus,
} from 'lucide-react'

export default function Sidebar({
  activeTabKey,
  lang,
  t,
  beginPilgrimagePlanning,
  handleTabChange,
  setIsYadadriSelected,
  handleSend,
  setLang
}) {
  const navMenuItems = [
    { key: 'New Plan', icon: <Plus size={18} /> },
    { key: 'Temples', icon: <Landmark size={18} /> },
    { key: 'My Journey', icon: <Milestone size={18} /> },
    { key: 'Travel Guide', icon: <Compass size={18} /> },
  ]

  return (
    <aside className="sidebar" style={{ position: 'relative', zIndex: 1 }}>
      <div className="sidebar-menu">
        {navMenuItems.map((item) => (
          <button
            key={item.key}
            className={`menu-item ${activeTabKey === item.key ? 'active' : ''}`}
            onClick={() => {
              if (item.key === 'New Plan') {
                beginPilgrimagePlanning()
              } else {
                handleTabChange(item.key)
              }
              if (item.key === 'Temples') {
                setIsYadadriSelected(false)
                return
              }
              if (item.key === 'Temples') handleSend(lang === 'తె' ? 'తెలంగాణలోని అన్ని ప్రముఖ ఆలయాల జాబితా ఇవ్వండి' : lang === 'हि' ? 'तेलंगाना के सभी मुख्य मंदिरों की सूची दें' : 'List all 22 verified temples in Telangana')
              if (item.key === 'Travel Guide') handleSend(lang === 'తె' ? 'హైదరాబాద్ నుండి భద్రాచలం ఎలా చేరుకోవాలి' : lang === 'हि' ? 'हैदराबाद से भद्राचलम कैसे पहुंचे' : 'How to reach Bhadrachalam from Hyderabad by bus and train')
            }}
          >
            <span className="menu-icon">{item.icon}</span>
            <span>{t.menu[item.key]}</span>
          </button>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="lang-title">{t.languageLabel}</div>
        <div className="lang-options">
          {['EN', 'తె', 'हि'].map((l) => (
            <button
              key={l}
              className={`lang-btn ${lang === l ? 'active' : ''}`}
              onClick={() => setLang(l)}
            >
              {l}
            </button>
          ))}
        </div>
      </div>
    </aside>
  )
}
