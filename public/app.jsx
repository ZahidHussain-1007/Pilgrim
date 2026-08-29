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
  Loader2
} from 'lucide-react'

const API_BASE_URL = window.location.origin

class ChatRequestError extends Error {}

function chatErrorMessage(status) {
  if (status === 401) return 'Please sign in to continue.'
  if (status === 422) return 'Your message could not be processed. Please check it and try again.'
  if (status === 502 || status === 503 || status === 504) return 'The PilgrimAI service is unavailable right now. Please try again shortly.'
  if (status >= 400 && status < 500) return 'Your chat request could not be completed. Please try again.'
  return 'The PilgrimAI backend encountered an error. Please try again later.'
}

const TEMPLE_DRONE_VIDEOS = {
  yadadri: 'TL1ikdUlD3M',
  jogulamba: 'jWT9wJk4wcg',
  kaleswara: 'nXmFtN9VM0M',
  birla_mandir: 'dnyJZ9dBwzM',
  sanghi: 'QChoYxGonNM',
  keesaragutta: 'S1hu6aHl4Fk',
  ramappa: '5jjgCUMXDsQ',
  kommuravelli: 'xPReAgNlPYU',
  swarnagiri: 'ZpJf6FsMvcg',
  medaram: 'xerl2SvuUTU',
  surendrapuri: 'KgrN56qZVK0',
  kondagattu: 'vDJYs4iFhjw',
  thousand_pillar: '-Cux_v113Fo',
  manyamkonda: 'KkZfnMVokHw',
  bhadrachalam: 'rLAyTXA8VtQ',
}

function getTempleDroneVideo(temple) {
  const videoId = TEMPLE_DRONE_VIDEOS[temple?.slug]
  return videoId ? `https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&mute=1&controls=0&disablekb=1&fs=0&loop=1&playlist=${videoId}&playsinline=1&rel=0&modestbranding=1&iv_load_policy=3` : null
}

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

const CONSTELLATION_POSITIONS = {
  yadadri: { '--marker-column': 1, '--marker-row': 1 },
  surendrapuri: { '--marker-column': 2, '--marker-row': 1 },
  swarnagiri: { '--marker-column': 3, '--marker-row': 1 },
  basara: { '--marker-column': 4, '--marker-row': 1 },
  beechupally: { '--marker-column': 5, '--marker-row': 1 },
  bhadrachalam: { '--marker-column': 1, '--marker-row': 2 },
  bhadrakali: { '--marker-column': 2, '--marker-row': 2 },
  birla_mandir: { '--marker-column': 3, '--marker-row': 2 },
  chilkur: { '--marker-column': 4, '--marker-row': 2 },
  dharmapuri: { '--marker-column': 5, '--marker-row': 2 },
  edupayala: { '--marker-column': 1, '--marker-row': 3 },
  jamalapuram: { '--marker-column': 2, '--marker-row': 3 },
  jogulamba: { '--marker-column': 3, '--marker-row': 3 },
  kaleswara: { '--marker-column': 4, '--marker-row': 3 },
  keesaragutta: { '--marker-column': 5, '--marker-row': 3 },
  kommuravelli: { '--marker-column': 1, '--marker-row': 4 },
  kondagattu: { '--marker-column': 2, '--marker-row': 4 },
  manyamkonda: { '--marker-column': 3, '--marker-row': 4 },
  medaram: { '--marker-column': 4, '--marker-row': 4 },
  ramappa: { '--marker-column': 5, '--marker-row': 4 },
  sanghi: { '--marker-column': 2, '--marker-row': 5 },
  thousand_pillar: { '--marker-column': 3, '--marker-row': 5 },
  vemulawada: { '--marker-column': 4, '--marker-row': 5 },
}

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
  const [conversationId, setConversationId] = useState(null)
  const [conversations, setConversations] = useState([])
  const [favorites, setFavorites] = useState([])
  const [templeSearch, setTempleSearch] = useState('')
  const [selectedDiscoveryTemple, setSelectedDiscoveryTemple] = useState(TEMPLES_LIST[0])
  const [isYadadriSelected, setIsYadadriSelected] = useState(false)
  const threadEndRef = useRef(null)

  const t = UI_TRANSLATIONS[lang]
  const isChatMode = messages.length > 0
  function openTempleExperience(temple) {
    setSelectedDiscoveryTemple(temple)
    setIsYadadriSelected(true)
  }

  function selectDiscoveryTemple(temple) {
    setSelectedDiscoveryTemple(temple)
    setSelectedTemple(temple.slug)
  }

  function openPurpose(key) {
    const purposeQueries = {
      Darshan: 'Darshan timings and special entry slots for Yadadri',
      Rituals: 'Explain the main rituals and poojas at Vemulawada',
      Travel: 'How to reach Bhadrachalam from Hyderabad by bus and train',
      Accommodation: 'Verified accommodation and stays near Yadadri',
      Restaurants: 'Find restaurants near Telangana temples',
      Emergency: 'Emergency contacts and help for pilgrims in Telangana',
    }
    const targetTab = { Darshan: 'Darshan Booking', Rituals: 'Rituals', Travel: 'Travel Guide', Accommodation: 'Accommodation' }[key]
    if (targetTab) setActiveTabKey(targetTab)
    handleSend(purposeQueries[key])
  }

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
      .then(async (data) => {
        if (!data?.user) return
        const [profileResponse, conversationResponse, favoritesResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/auth/profile`, { credentials: 'include' }),
          fetch(`${API_BASE_URL}/api/conversations`, { credentials: 'include' }),
          fetch(`${API_BASE_URL}/api/favorites`, { credentials: 'include' })
        ])
        const profilePayload = profileResponse.ok ? await profileResponse.json() : null
        setUser({ ...data.user, avatarUrl: profilePayload?.profile?.avatar_url || null })
        if (conversationResponse.ok) setConversations(await conversationResponse.json())
        if (favoritesResponse.ok) setFavorites(await favoritesResponse.json())
      })
      .catch(() => {})
  }, [])

  async function loadConversation(id) {
    const response = await fetch(`${API_BASE_URL}/api/conversations/${id}/messages`, { credentials: 'include' })
    if (!response.ok) return
    const history = await response.json()
    setConversationId(id)
    setMessages(history.map((message) => ({ id: message.id, who: message.role === 'assistant' ? 'bot' : 'user', text: message.content })))
    setActiveTabKey('Home')
  }

  async function submitFeedback(messageId, rating) {
    await fetch(`${API_BASE_URL}/api/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ messageId, rating })
    })
  }

  async function toggleFavorite() {
    if (!user || !selectedTemple) return
    const existing = favorites.find((favorite) => favorite.item_type === 'temple' && favorite.item_key === selectedTemple)
    if (existing) {
      await fetch(`${API_BASE_URL}/api/favorites/temple/${encodeURIComponent(selectedTemple)}`, { method: 'DELETE', credentials: 'include' })
      setFavorites((prev) => prev.filter((favorite) => favorite.id !== existing.id))
      return
    }
    const temple = TEMPLES_LIST.find((item) => item.slug === selectedTemple)
    const response = await fetch(`${API_BASE_URL}/api/favorites`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ itemType: 'temple', itemKey: selectedTemple, itemData: temple })
    })
    if (response.ok) {
      const favorite = await response.json()
      setFavorites((prev) => [favorite, ...prev])
    }
  }

  function startNewConversation() {
    setConversationId(null)
    setMessages([])
    setActiveTabKey('Home')
  }

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
        credentials: 'include',
        body: JSON.stringify({
          query: text,
          temple: targetTemple,
          language: lang === 'తె' ? 'te' : lang === 'हि' ? 'hi' : 'en'
          , conversationId
        })
      })

      if (!response.ok) {
        throw new ChatRequestError(chatErrorMessage(response.status))
      }

      const data = await response.json()
      if (data.conversationId) setConversationId(data.conversationId)
      if (data.conversationId && !conversations.some((item) => item.id === data.conversationId)) {
        setConversations((prev) => [{ id: data.conversationId, title: text }, ...prev])
      }
      setMessages((prev) => [...prev, { id: data.assistantMessageId, who: 'bot', text: data.answer }])
    } catch (err) {
      const message = err instanceof ChatRequestError ? err.message : t.errorMsg
      setMessages((prev) => [...prev, { who: 'bot', text: message }])
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
                  if (item.key === 'Home') startNewConversation()
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

        {/* MAIN CONTENT AREA */}
        <main className={`main-content ${activeTabKey === 'Temples' ? 'temples-page-main' : ''}`}>
          {activeTabKey === 'Temples' ? (
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
                  <div className="temple-discovery-selected-actions"><button type="button" className="temple-discovery-primary" onClick={() => openTempleExperience(selectedDiscoveryTemple)}>Explore Temple <span aria-hidden="true">→</span></button><button type="button" onClick={() => openPurpose('Darshan')}>Ask AI</button></div>
                </aside>
              </div>

              <div className="temple-discovery-section-heading temple-discovery-purpose-heading"><div><span className="temple-discovery-eyebrow">PLAN YOUR DAY</span><h2>Explore by Purpose</h2></div></div>
              <div className="temple-discovery-purpose-grid">{[['🙏', 'Darshan'], ['🪔', 'Rituals'], ['🗺️', 'Travel'], ['🏨', 'Accommodation'], ['🍽️', 'Restaurants'], ['🚑', 'Emergency']].map(([icon, label]) => <button type="button" className="temple-discovery-purpose" key={label} onClick={() => openPurpose(label)}><span>{icon}</span><strong>{label}</strong><small>Discover more <span aria-hidden="true">↗</span></small></button>)}</div>
            </section>
          ) : activeTabKey === 'My Journey' ? (
            <div className="chat-conversation">
              <h2>My Journey</h2>
              {user ? conversations.map((conversation) => (
                <button key={conversation.id} className="quick-chip" onClick={() => loadConversation(conversation.id)}>
                  {conversation.title || 'Untitled conversation'}
                </button>
              )) : <p>Sign in to view saved conversations and favorites.</p>}
              {user && favorites.length > 0 && <><h3>Favorites</h3>{favorites.map((favorite) => <p key={favorite.id}>{favorite.item_type}: {favorite.item_key}</p>)}</>}
            </div>
          ) : !isChatMode ? (
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
                  onClick={() => setActiveTabKey('Temples')}
                >
                  Explore Sacred Telangana
                </button>
                <button
                  className="quick-chip"
                  onClick={() => handleSend('Plan my pilgrimage')}
                >
                  Plan My Pilgrimage
                </button>
                <button
                  className="quick-chip"
                  onClick={() => {
                    setActiveTabKey('Darshan Booking')
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
                <button className="home-plan-button" type="button" onClick={() => handleSend('Plan my pilgrimage')}>
                  <span>✦ Plan My Trip</span><span aria-hidden="true">→</span>
                </button>
              </div>
              <p className="home-capability-strip">🛕 Temples · 🙏 Darshan · 🗺️ Travel · 🏨 Stay · 🪔 Rituals · 🧭 Trip Planning</p>
            </div>
          ) : (
            <div className="chat-conversation">
              <div className="message-stream">
                {messages.map((m, idx) => (
                  <div key={idx} className={`chat-bubble ${m.who}`}>
                    {m.text}
                    {m.who === 'bot' && (
                      <>
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
                      {m.id && <div className="feedback-actions">
                        {[1, 2, 3, 4, 5].map((rating) => (
                          <button key={rating} onClick={() => submitFeedback(m.id, rating)} title={`Rate ${rating} out of 5`}>{rating}</button>
                        ))}
                      </div>}
                      </>
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
              {user && selectedTemple && <button className="quick-chip" onClick={toggleFavorite}>
                {favorites.some((favorite) => favorite.item_type === 'temple' && favorite.item_key === selectedTemple) ? 'Remove temple from favorites' : 'Save temple to favorites'}
              </button>}
            </div>
          )}
        </main>
      </div>
      {isYadadriSelected && (
        <section className="yadadri-hero" aria-label="Yadadri temple hero">
          {getTempleDroneVideo(selectedDiscoveryTemple) ? (
            <iframe
              className="yadadri-video"
              src={getTempleDroneVideo(selectedDiscoveryTemple)}
              title={`${selectedDiscoveryTemple.name} temple drone video`}
              tabIndex={-1}
              aria-hidden="true"
              allow="autoplay"
            />
          ) : <div className="yadadri-fallback" aria-hidden="true" />}
          <div className="yadadri-video-shield" aria-hidden="true" />
          <div className="yadadri-overlay" />
          <button className="yadadri-back" type="button" onClick={() => setIsYadadriSelected(false)}>← Back to Temples</button>
          <div className="yadadri-content">
            <span className="yadadri-label">{selectedDiscoveryTemple.name.toUpperCase()}</span>
            <h1>{selectedDiscoveryTemple.full}</h1>
            <p>Telangana</p>
            <div className="yadadri-actions">
              <button type="button">Explore Temple</button>
              <button type="button">Ask AI</button>
            </div>
          </div>
        </section>
      )}
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
