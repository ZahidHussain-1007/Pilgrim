import React, { useEffect, useRef, useState } from 'react'
import {
  Home,
  Landmark,
  CalendarCheck,
  BedDouble,
  Compass,
  Flame,
  Milestone,
  Settings,
  Mic,
  Send,
  Volume2,
  Loader2,
  LogIn,
  LogOut
} from 'lucide-react'

const API_BASE_URL = window.location.origin

const TEMPLES_LIST = [
  { slug: 'yadadri', name: 'Yadadri', folder: 'Yadadri_stay', full: 'Sri Lakshmi Narasimha Swamy Temple, Yadadri' },
  { slug: 'surendrapuri', name: 'Surendrapuri', folder: 'Surendrapuri_stay', full: 'Surendrapuri Mythological Theme & Temples' },
  { slug: 'swarnagiri', name: 'Swarnagiri', folder: 'swarnagiri_stay', full: 'Sri Swarnagiri Venkateswara Swamy' },
  { slug: 'basara', name: 'Basara', folder: 'Basara_stay', full: 'Sri Gnana Saraswati Temple, Basara' },
  { slug: 'beechupally', name: 'Beechupally', folder: 'Beechupally_stay', full: 'Sri Beechupally Anjaneya Swamy Temple' },
  { slug: 'bhadrachalam', name: 'Bhadrachalam', folder: 'Bhadrachalam_stay', full: 'Sri Seetha Ramachandraswamy Temple, Bhadrachalam' },
  { slug: 'bhadrakali', name: 'Bhadrakali', folder: 'Bhadrakali_stay', full: 'Sri Bhadrakali Temple, Warangal' },
  { slug: 'birla_mandir', name: 'Birla Mandir', folder: 'Birla_mandir_stay', full: 'Birla Mandir, Hyderabad' },
  { slug: 'chilkur', name: 'Chilkur', folder: 'chilkur_stay', full: 'Chilkur Balaji Temple (Visa Balaji)' },
  { slug: 'dharmapuri', name: 'Dharmapuri', folder: 'Dharmapuri_stay', full: 'Sri Lakshmi Narasimha Swamy, Dharmapuri' },
  { slug: 'edupayala', name: 'Edupayala', folder: 'Edupayala_stay', full: 'Sri Edupayala Vana Durga Bhavani' },
  { slug: 'jamalapuram', name: 'Jamalapuram', folder: 'jamalapuram_stay', full: 'Sri Venkateswara Swamy, Jamalapuram' },
  { slug: 'jogulamba', name: 'Jogulamba', folder: 'jogulamba_stay', full: 'Sri Jogulamba Devi Temple (Alampur)' },
  { slug: 'kaleswara', name: 'Kaleswaram', folder: 'Kaleswara_stay', full: 'Sri Kaleswara Mukteswara Swamy' },
  { slug: 'keesaragutta', name: 'Keesaragutta', folder: 'Keesaragutta_stay', full: 'Sri Ramalingeswara Swamy, Keesaragutta' },
  { slug: 'kommuravelli', name: 'Kommuravelli', folder: 'Kommuravelli_temple', full: 'Sri Komuravelli Mallanna Temple' },
  { slug: 'kondagattu', name: 'Kondagattu', folder: 'kondagattu_stay', full: 'Sri Anjaneya Swamy, Kondagattu' },
  { slug: 'manyamkonda', name: 'Manyamkonda', folder: 'Manyamkonda_stay', full: 'Manyamkonda Sri Venkateswara Swamy' },
  { slug: 'medaram', name: 'Medaram', folder: 'Medaram_stay', full: 'Sammakka Saralamma Temple, Medaram' },
  { slug: 'ramappa', name: 'Ramappa', folder: 'Ramappa_stay', full: 'Ramappa Temple (UNESCO Site)' },
  { slug: 'sanghi', name: 'Sanghi', folder: 'sanghi_stay', full: 'Sanghi Temple, Hyderabad' },
  { slug: 'thousand_pillar', name: 'Thousand Pillar', folder: 'Thousand_pillar_stay', full: 'Thousand Pillar Temple, Warangal' },
  { slug: 'vemulawada', name: 'Vemulawada', folder: 'vemulawada_stay', full: 'Sri Raja Rajeshwara Swamy, Vemulawada' },
]

const UI_TRANSLATIONS = {
  EN: {
    navAbout: 'About',
    navFeatures: 'Features',
    navGetStarted: 'Get Started',
    heading: 'Namaste! How can I help your pilgrimage?',
    subtext: 'Ask me anything about temples, darshan, travel, or rituals',
    inputPlaceholder: 'Type or speak your question...',
    followUpPlaceholder: 'Ask a follow-up question...',
    chipNearMe: 'Find temples near me',
    chipDarshan: 'Book darshan at Yadadri',
    chipRituals: 'Tell me about rituals',
    languageLabel: 'Language',
    listen: 'Listen',
    errorMsg: 'Unable to reach the PilgrimAI backend. Please ensure the server is running on port 8000.',
    menu: {
      Home: 'Home',
      Temples: 'Temples',
      'Darshan Booking': 'Darshan Booking',
      Accommodation: 'Accommodation',
      'Travel Guide': 'Travel Guide',
      Rituals: 'Rituals',
      'My Journey': 'My Journey',
      Settings: 'Settings',
    }
  },
  'తె': {
    navAbout: 'గురించి',
    navFeatures: 'ప్రత్యేకతలు',
    navGetStarted: 'ప్రారంభించండి',
    heading: 'నమస్కారం! మీ యాత్రలో ఎలా సహాయపడగలను?',
    subtext: 'ఆలయాలు, దర్శనం, ప్రయాణం లేదా సేవల గురించి ఏదైనా అడగండి',
    inputPlaceholder: 'మీ ప్రశ్నను ఇక్కడ టైప్ చేయండి లేదా మాట్లాడండి...',
    followUpPlaceholder: 'మరిన్ని వివరాల కోసం అడగండి...',
    chipNearMe: 'సమీపంలోని ఆలయాలు',
    chipDarshan: 'యాదాద్రి దర్శనం వివరాలు',
    chipRituals: 'పూజా కార్యక్రమాలు & సేవలు',
    languageLabel: 'భాష',
    listen: 'వినండి',
    errorMsg: 'సర్వర్‌ను సంప్రదించడం సాధ్యపడలేదు. దయచేసి బ్యాకెండ్ రన్ అవుతుందో లేదో తనిఖీ చేయండి.',
    menu: {
      Home: 'హోమ్',
      Temples: 'ఆలయాలు',
      'Darshan Booking': 'దర్శనం బుకింగ్',
      Accommodation: 'బస & హోటళ్ళు',
      'Travel Guide': 'ప్రయాణ మార్గదర్శి',
      Rituals: 'సేవలు & పూజలు',
      'My Journey': 'నా ప్రయాణం',
      Settings: 'సెట్టింగులు',
    }
  },
  'हि': {
    navAbout: 'परिचय',
    navFeatures: 'विशेषताएँ',
    navGetStarted: 'शुरू करें',
    heading: 'नमस्कार! मैं आपकी यात्रा में कैसे सहायता कर सकता हूँ?',
    subtext: 'मंदिरों, दर्शन, यात्रा या पूजा-विधि के बारे में कुछ भी पूछें',
    inputPlaceholder: 'अपना प्रश्न लिखें या बोलकर पूछें...',
    followUpPlaceholder: 'अगला प्रश्न पूछें...',
    chipNearMe: 'निकटतम मंदिर खोजें',
    chipDarshan: 'यादाद्री दर्शन जानकारी',
    chipRituals: 'पूजा विधि एवं अनुष्ठान',
    languageLabel: 'भाषा',
    listen: 'सुनें',
    errorMsg: 'सर्वर से संपर्क नहीं हो सका। कृपया जांचें कि बैकएंड चालू है।',
    menu: {
      Home: 'होम',
      Temples: 'मंदिर',
      'Darshan Booking': 'दर्शन बुकिंग',
      Accommodation: 'ठहरने की व्यवस्था',
      'Travel Guide': 'यात्रा गाइड',
      Rituals: 'अनुष्ठान एवं पूजा',
      'My Journey': 'मेरी यात्रा',
      Settings: 'सेटिंग्स',
    }
  }
}

export default function App() {
  const [activeTabKey, setActiveTabKey] = useState('Home')
  const [lang, setLang] = useState('EN')
  const [query, setQuery] = useState('')
  const [selectedTemple, setSelectedTemple] = useState(null)
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [user, setUser] = useState(null)
  const threadEndRef = useRef(null)

  const t = UI_TRANSLATIONS[lang]
  const isChatMode = messages.length > 0

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('login') === 'success') {
      window.history.replaceState({}, '', window.location.pathname)
    }

    fetch(`${API_BASE_URL}/auth/me`, { credentials: 'include' })
      .then((response) => response.ok ? response.json() : null)
      .then((data) => data?.user && setUser(data.user))
      .catch(() => {})
  }, [])

  async function handleSend(textOverride) {
    const text = (textOverride ?? query).trim()
    if (!text || isLoading) return

    const lower = text.toLowerCase()
    const matched = TEMPLES_LIST.find((tp) => lower.includes(tp.slug) || lower.includes(tp.name.toLowerCase()))
    const targetTemple = matched ? matched.slug : selectedTemple

    if (matched) setSelectedTemple(matched.slug)

    setMessages((prev) => [...prev, { who: 'user', text }])
    setQuery('')
    setIsLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: text,
          temple: targetTemple,
          language: lang === 'తె' ? 'te' : lang === 'हि' ? 'hi' : 'en'
        })
      })

      if (!response.ok) {
        throw new Error(`Server status: ${response.status}`)
      }

      const data = await response.json()
      setMessages((prev) => [...prev, { who: 'bot', text: data.reply }])
    } catch (err) {
      setMessages((prev) => [...prev, { who: 'bot', text: t.errorMsg }])
    } finally {
      setIsLoading(false)
    }
  }

  function toggleVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert('Voice search is supported in Chrome and Edge.')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = lang === 'తె' ? 'te-IN' : lang === 'हि' ? 'hi-IN' : 'en-IN'
    recognition.continuous = false

    if (!isListening) {
      recognition.start()
      setIsListening(true)
      recognition.onresult = (e) => {
        const transcript = e.results[0][0].transcript
        setQuery(transcript)
        setIsListening(false)
        handleSend(transcript)
      }
      recognition.onerror = () => setIsListening(false)
      recognition.onend = () => setIsListening(false)
    } else {
      recognition.stop()
      setIsListening(false)
    }
  }

  function speakText(text) {
    if (!('speechSynthesis' in window)) return
    const clean = text.replace(/[*#•`_]/g, '')
    const utterance = new SpeechSynthesisUtterance(clean)
    utterance.lang = lang === 'తె' ? 'te-IN' : lang === 'हि' ? 'hi-IN' : 'en-IN'
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(utterance)
  }

  function signInWithGoogle() {
    window.location.assign(`${API_BASE_URL}/auth/google`)
  }

  async function signOut() {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, { method: 'POST', credentials: 'include' })
    } finally {
      setUser(null)
    }
  }

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
    <div className="app-container">
      {/* 1. TOP NAVBAR */}
      <header className="top-navbar">
        <div className="nav-brand">
          <span className="brand-om">ॐ</span>
          <span className="brand-title">PilgrimAI</span>
        </div>
        <div className="nav-links">
          <a href="#about" className="nav-link">{t.navAbout}</a>
          <a href="#features" className="nav-link">{t.navFeatures}</a>
          {user ? (
            <button className="google-login-button signed-in" onClick={signOut} title="Sign out">
              <LogOut size={16} />
              <span>{user.name}</span>
            </button>
          ) : (
            <button className="google-login-button" onClick={signInWithGoogle}>
              <GoogleMark />
              <span>Continue with Google</span>
            </button>
          )}
          <button className="btn-get-started" onClick={() => { setMessages([]); setActiveTabKey('Home'); }}>
            {t.navGetStarted}
          </button>
        </div>
      </header>

      {/* 2. WORKSPACE */}
      <div className="workspace">
        {/* SIDEBAR */}
        <aside className="sidebar">
          <div className="sidebar-menu">
            {navMenuItems.map((item) => (
              <button
                key={item.key}
                className={`menu-item ${activeTabKey === item.key ? 'active' : ''}`}
                onClick={() => {
                  setActiveTabKey(item.key)
                  if (item.key === 'Home') setMessages([])
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

        {/* MAIN CONTENT AREA */}
        <main className="main-content">
          {!isChatMode ? (
            <div className="center-hero">
              <div className="center-om">ॐ</div>
              <h1 className="hero-heading">{t.heading}</h1>
              <p className="hero-subtext">{t.subtext}</p>

              <button
                className={`mic-circle-btn ${isListening ? 'listening' : ''}`}
                onClick={toggleVoice}
                title="Voice Search"
              >
                <Mic size={28} />
              </button>

              <div className="quick-chips-row">
                <button
                  className="quick-chip"
                  onClick={() => handleSend(t.chipNearMe)}
                >
                  {t.chipNearMe}
                </button>
                <button
                  className="quick-chip"
                  onClick={() => handleSend(t.chipDarshan)}
                >
                  {t.chipDarshan}
                </button>
                <button
                  className="quick-chip"
                  onClick={() => handleSend(t.chipRituals)}
                >
                  {t.chipRituals}
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
            </div>
          ) : (
            <div className="chat-conversation">
              <div className="message-stream">
                {messages.map((m, idx) => (
                  <div key={idx} className={`chat-bubble ${m.who}`}>
                    {m.text}
                    {m.who === 'bot' && (
                      <button
                        onClick={() => speakText(m.text)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          fontSize: '12px',
                          color: '#C87D17',
                          fontWeight: '700',
                          marginTop: '8px',
                          paddingTop: '6px',
                          borderTop: '1px solid #EADBCB'
                        }}
                      >
                        <Volume2 size={14} /> {t.listen}
                      </button>
                    )}
                  </div>
                ))}

                {isLoading && (
                  <div className="chat-bubble bot" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#7A6F66' }}>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Searching verified records...</span>
                  </div>
                )}
                <div ref={threadEndRef} />
              </div>

              <div className="input-shell" style={{ width: '100%', maxWidth: '100%' }}>
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
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

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
