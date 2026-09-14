import React from 'react'
import {
  Home,
  Landmark,
  CalendarCheck,
  BedDouble,
  Compass,
  Flame,
  Milestone,
  Settings,
} from 'lucide-react'

export default function Sidebar({
  activeTabKey,
  lang,
  t,
  startNewConversation,
  handleTabChange,
  setIsYadadriSelected,
  handleSend,
  setLang
}) {
  const navMenuItems = [
    { key: 'Home', icon: <Home size={18} /> },
    { key: 'Temples', icon: <Landmark size={18} /> },
    { key: 'Darshan Booking', icon: <CalendarCheck size={18} /> },
    { key: 'Accommodation', icon: <BedDouble size={18} /> },
    { key: 'Travel Guide', icon: <Compass size={18} /> },
    { key: 'Rituals', icon: <Flame size={18} /> },
    { key: 'My Journey', icon: <Milestone size={18} /> },
    { key: 'Settings', icon: <Settings size={18} /> },
  ]

  return (
    <aside className="sidebar" style={{ position: 'relative', zIndex: 1 }}>
      <div className="sidebar-menu">
        {navMenuItems.map((item) => (
          <button
            key={item.key}
            className={`menu-item ${activeTabKey === item.key ? 'active' : ''}`}
            onClick={() => {
              if (item.key === 'Home') {
                startNewConversation()
              } else {
                handleTabChange(item.key)
              }
              if (item.key === 'Temples') {
                setIsYadadriSelected(false)
                return
              }
              if (item.key === 'Temples') handleSend(lang === 'తె' ? 'తెలంగాణలోని అన్ని ప్రముఖ ఆలయాల జాబితా ఇవ్వండి' : lang === 'हि' ? 'तेलंगाना के सभी मुख्य मंदिरों की सूची दें' : 'List all 22 verified temples in Telangana')
              if (item.key === 'Accommodation') handleSend(lang === 'తె' ? 'యాదాద్రి వద్ద సరసమైన మరియు ఉత్తమ బస వివరాలు' : lang === 'हि' ? 'यादाद्री के पास प्रमाणित होटल' : 'Verified accommodation and stays near Yadadri')
              if (item.key === 'Darshan Booking') handleSend(lang === 'తె' ? 'యాదాద్రి దర్శనం సమయాలు మరియు టికెట్ వివరాలు' : lang === 'हि' ? 'यादाद्री दर्शन समय और टिकट' : 'Darshan timings and special entry slots for Yadadri')
              if (item.key === 'Travel Guide') handleSend(lang === 'తె' ? 'హైదరాబాద్ నుండి భద్రాచలం ఎలా చేరుకోవాలి' : lang === 'हि' ? 'हैदराबाद से भद्राचलम कैसे पहुंचे' : 'How to reach Bhadrachalam from Hyderabad by bus and train')
              if (item.key === 'Rituals') handleSend(lang === 'తె' ? 'వేములవాడ కోడె మొక్కు పూజా విశేషాలు' : lang === 'हि' ? 'वेमुलवाड़ा मंदिर पूजा एवं अनुष्ठान' : 'Explain the main rituals and poojas at Vemulawada')
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
