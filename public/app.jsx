import React, { useEffect, useRef, useState } from 'react'
import { 
  ROUTE_TO_TAB, 
  parsePathAndApplyState as routingParsePath,
  handleTabChange as routingHandleTabChange,
  navigateToTemple,
  navigateToTempleConversation,
  navigateToConversation
} from './features/routing.js'
import { resolveTempleVideo } from './features/templeVideo.js'
import { TEMPLES_LIST } from './features/temples.js'
import { 
  ChatRequestError, detectTempleInText, sendChatMessage, 
  fetchConversationMessages, speakText as chatSpeakText, submitFeedback as chatSubmitFeedback 
} from './features/chat.js'
import { redirectToGoogleAuth, executeLogout, fetchUserData } from './features/authentication.js'
import Sidebar from './components/Sidebar.jsx'
import TopNavbar from './components/TopNavbar.jsx'
import MyJourney from './components/MyJourney.jsx'
import TempleDiscovery from './components/TempleDiscovery.jsx'
import TempleExperienceHero from './components/TempleExperienceHero.jsx'
import HomeHero from './components/HomeHero.jsx'
import ChatUI from './components/ChatUI.jsx'
import About from './components/About.jsx'

const API_BASE_URL = window.location.origin





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
      'New Plan': 'New Plan',
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
      'New Plan': 'కొత్త యాత్ర',
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
      'New Plan': 'नई यात्रा',
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
  const [activeTabKey, setActiveTabKey] = useState(() => {
    const path = window.location.pathname
    if (path.startsWith('/temples/')) return 'Temples'
    if (path.startsWith('/c/')) return 'Home'
    return ROUTE_TO_TAB[path] || 'Home'
  })
  const [lang, setLang] = useState('EN')
  const [query, setQuery] = useState('')
  const [selectedTemple, setSelectedTemple] = useState(() => {
    const path = window.location.pathname
    if (path.startsWith('/c/')) {
      const param = path.slice(3).replace(/\/$/, '')
      const temple = TEMPLES_LIST.find((t) => t.slug === param)
      if (temple) return temple.slug
    }
    return null
  })
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [user, setUser] = useState(null)
  const [conversationId, setConversationId] = useState(() => {
    const path = window.location.pathname
    if (path.startsWith('/c/')) {
      const param = path.slice(3).replace(/\/$/, '')
      const temple = TEMPLES_LIST.find((t) => t.slug === param)
      if (!temple) return param
    }
    return null
  })
  const [conversations, setConversations] = useState([])
  const [favorites, setFavorites] = useState([])
  const [templeSearch, setTempleSearch] = useState('')
  const [selectedDiscoveryTemple, setSelectedDiscoveryTemple] = useState(() => {
    const path = window.location.pathname
    if (path.startsWith('/temples/')) {
      const slug = path.slice(9).replace(/\/$/, '')
      const temple = TEMPLES_LIST.find((t) => t.slug === slug)
      if (temple) return temple
    }
    if (path.startsWith('/c/')) {
      const param = path.slice(3).replace(/\/$/, '')
      const temple = TEMPLES_LIST.find((t) => t.slug === param)
      if (temple) return temple
    }
    return TEMPLES_LIST[0]
  })
  const [isYadadriSelected, setIsYadadriSelected] = useState(() => {
    return window.location.pathname.startsWith('/temples/')
  })
  const fetchedSlugs = useRef(new Set())
  const [videoUrls, setVideoUrls] = useState({})

  useEffect(() => {
    const controller = new AbortController()

    async function loadVideo(slug) {
      if (!slug || fetchedSlugs.current.has(slug)) return

      const embedUrl = await resolveTempleVideo(slug, API_BASE_URL, controller.signal)
      if (embedUrl) {
        fetchedSlugs.current.add(slug)
        setVideoUrls((prev) => ({ ...prev, [slug]: embedUrl }))
      }
    }

    const uniqueSlugs = new Set([selectedDiscoveryTemple?.slug, selectedTemple].filter(Boolean))
    uniqueSlugs.forEach(loadVideo)

    return () => controller.abort()
  }, [selectedDiscoveryTemple?.slug, selectedTemple])
  const threadEndRef = useRef(null)
  const plannerSessionRef = useRef(0)

  async function loadConversation(id) {
    const history = await fetchConversationMessages(id, API_BASE_URL)
    setConversationId(id)
    if (history && history.length > 0) {
      setMessages(history.map((message) => ({ id: message.id, who: message.role === 'assistant' ? 'bot' : 'user', text: message.content })))
    }
    if (window.location.pathname !== `/c/${id}`) {
      window.history.pushState({ key: 'Conversation', conversationId: id }, '', `/c/${id}`)
    }
    setActiveTabKey('Home')
    setIsYadadriSelected(false)
  }

  const routeActions = { 
    setActiveTabKey, 
    setSelectedDiscoveryTemple, 
    setIsYadadriSelected, 
    setSelectedTemple, 
    setConversationId, 
    loadConversation 
  }

  function parsePathAndApplyState(path) {
    return routingParsePath(path, TEMPLES_LIST, routeActions)
  }

  function handleTabChange(key) {
    routingHandleTabChange(key, TEMPLES_LIST, routeActions)
  }

  useEffect(() => {
    const init = parsePathAndApplyState(window.location.pathname)
    if (!init.valid) {
      window.history.replaceState({ key: init.tab }, '', init.fallback)
      parsePathAndApplyState(init.fallback)
    }

    function handlePopState() {
      const pop = parsePathAndApplyState(window.location.pathname)
      if (!pop.valid) {
        window.history.replaceState({ key: pop.tab }, '', pop.fallback)
        parsePathAndApplyState(pop.fallback)
      }
    }
    
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const t = UI_TRANSLATIONS[lang]
  const isConversationRoute = window.location.pathname.startsWith('/c/')
  const isChatMode = messages.length > 0 || isConversationRoute

  function openTempleExperience(temple) {
    const route = `/temples/${temple.slug}`
    if (window.location.pathname !== route) {
      window.history.pushState({ key: 'Temples', slug: temple.slug }, '', route)
    }
    parsePathAndApplyState(route)
  }

  function selectDiscoveryTemple(temple) {
    setSelectedDiscoveryTemple(temple)
    setSelectedTemple(temple.slug)
    openTempleExperience(temple)
  }

  function handleAskAI(temple) {
    const target = typeof temple === 'string' ? temple : temple?.slug
    if (!target) return
    const matched = TEMPLES_LIST.find((t) => t.slug === target)
    if (matched) {
      setSelectedTemple(matched.slug)
      setSelectedDiscoveryTemple(matched)
    } else {
      setSelectedTemple(target)
    }
    setIsYadadriSelected(false)
    setActiveTabKey('Home')
    const route = `/c/${target}`
    if (window.location.pathname !== route) {
      window.history.pushState({ key: 'Conversation', templeSlug: target }, '', route)
    }
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
    if (targetTab) handleTabChange(targetTab)
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

    fetchUserData(API_BASE_URL)
      .then((data) => {
        if (!data) return
        setUser(data.user)
        setConversations(data.conversations)
        setFavorites(data.favorites)
      })
      .catch(() => {})
  }, [])

  async function submitFeedback(messageId, rating) {
    await chatSubmitFeedback(messageId, rating, API_BASE_URL)
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
    setSelectedTemple(null)
    setIsYadadriSelected(false)
    setMessages([])
    if (window.location.pathname !== '/') {
      window.history.pushState({ key: 'Home' }, '', '/')
    }
    setActiveTabKey('Home')
  }

  function beginPilgrimagePlanning() {
    plannerSessionRef.current += 1
    setConversationId(null)
    setSelectedTemple(null)
    setIsYadadriSelected(false)
    setQuery('')
    setIsLoading(false)
    setIsListening(false)
    setTempleSearch('')
    setSelectedDiscoveryTemple(TEMPLES_LIST[0])
    setMessages([{
      who: 'bot',
      text: 'Sure! Which temple would you like to visit? Please tell me your starting city, number of days, travel mode, and travel dates if you have them.'
    }])
    if (window.location.pathname !== '/') {
      window.history.pushState({ key: 'Home' }, '', '/')
    }
    setActiveTabKey('Home')
  }

  async function handleSend(textOverride) {
    const text = (textOverride ?? query).trim()
    if (!text || isLoading) return

    const matchedSlug = detectTempleInText(text, TEMPLES_LIST)
    const targetTemple = matchedSlug ? matchedSlug : selectedTemple

    if (matchedSlug) setSelectedTemple(matchedSlug)

    setMessages((prev) => [...prev, { who: 'user', text }])
    setQuery('')
    setIsLoading(true)
    const requestSession = plannerSessionRef.current

    try {
      const data = await sendChatMessage({ text, targetTemple, lang, conversationId, baseUrl: API_BASE_URL })
      if (requestSession !== plannerSessionRef.current) return

      const activeConvId = data.conversationId || (window.crypto?.randomUUID ? window.crypto.randomUUID().slice(0, 8) : Math.random().toString(36).substring(2, 10))

      if (!conversationId) {
        setConversationId(activeConvId)
        if (!conversations.some((item) => item.id === activeConvId)) {
          setConversations((prev) => [{ id: activeConvId, title: text }, ...prev])
        }
        const currentPath = window.location.pathname
        const isTempleRoute = currentPath.startsWith('/c/') && TEMPLES_LIST.some((t) => t.slug === currentPath.slice(3).replace(/\/$/, ''))
        if (!isTempleRoute && currentPath !== `/c/${activeConvId}`) {
          window.history.pushState({ key: 'Conversation', conversationId: activeConvId }, '', `/c/${activeConvId}`)
        }
      }

      setMessages((prev) => [...prev, { id: data.assistantMessageId, who: 'bot', text: data.answer }])
    } catch (err) {
      if (requestSession !== plannerSessionRef.current) return
      if (!conversationId) {
        const fallbackConvId = window.crypto?.randomUUID ? window.crypto.randomUUID().slice(0, 8) : Math.random().toString(36).substring(2, 10)
        setConversationId(fallbackConvId)
        const currentPath = window.location.pathname
        const isTempleRoute = currentPath.startsWith('/c/') && TEMPLES_LIST.some((t) => t.slug === currentPath.slice(3).replace(/\/$/, ''))
        if (!isTempleRoute && currentPath !== `/c/${fallbackConvId}`) {
          window.history.pushState({ key: 'Conversation', conversationId: fallbackConvId }, '', `/c/${fallbackConvId}`)
        }
      }
      const message = err instanceof ChatRequestError ? err.message : t.errorMsg
      setMessages((prev) => [...prev, { who: 'bot', text: message }])
    } finally {
      if (requestSession === plannerSessionRef.current) setIsLoading(false)
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
    chatSpeakText(text, lang)
  }

  function signInWithGoogle() {
    redirectToGoogleAuth(API_BASE_URL)
  }

  async function signOut() {
    try {
      await executeLogout(API_BASE_URL)
    } finally {
      setUser(null)
    }
  }

  const immersiveTempleChat = Boolean(
    selectedTemple && videoUrls[selectedTemple] && activeTabKey !== 'Temples' && isChatMode
  )
  const templeVideoActive = Boolean(
    selectedTemple && videoUrls[selectedTemple] && activeTabKey !== 'Temples'
  )


  return (
    <div className={`app-container ${immersiveTempleChat ? 'immersive-app' : ''}`}>
      {/* 1. TOP NAVBAR */}
      <TopNavbar user={user} t={t} signInWithGoogle={signInWithGoogle} signOut={signOut} handleTabChange={handleTabChange} startNewConversation={startNewConversation} />

      {/* 2. WORKSPACE */}
      <div className={`workspace ${templeVideoActive ? 'video-workspace' : ''} ${immersiveTempleChat ? 'immersive-temple-chat' : ''}`} style={{ position: 'relative' }}>
        {immersiveTempleChat && (
          <section className="temple-video-panel" aria-label="Temple video">
            <iframe
              className="temple-panel-video"
              src={videoUrls[selectedTemple]}
              title={`${selectedTemple} temple video`}
              tabIndex={-1}
              aria-hidden="true"
              allow="autoplay; encrypted-media"
              allowFullScreen={false}
            />
            <div className="temple-video-shield" aria-hidden="true" />
          </section>
        )}
        {templeVideoActive && !immersiveTempleChat && (
          <div className="temple-video-layer">
            <iframe
              className="yadadri-video"
              src={videoUrls[selectedTemple]}
              tabIndex={-1}
              aria-hidden="true"
              allow="autoplay; encrypted-media"
              allowFullScreen={false}
            />
            <div className="temple-video-wash" />
          </div>
        )}
        {/* 2. SIDEBAR */}
        {!immersiveTempleChat && (
          <Sidebar
            activeTabKey={activeTabKey}
            lang={lang}
            t={t}
            beginPilgrimagePlanning={beginPilgrimagePlanning}
            handleTabChange={handleTabChange}
            setIsYadadriSelected={setIsYadadriSelected}
            handleSend={handleSend}
            setLang={setLang}
          />
        )}

        {/* MAIN CONTENT AREA */}
        <main 
          className={`main-content ${activeTabKey === 'Temples' ? 'temples-page-main' : ''} ${templeVideoActive ? 'video-main' : ''} ${immersiveTempleChat ? 'immersive-chat-main' : ''}`}
          style={{ position: 'relative', zIndex: 2, backgroundColor: templeVideoActive && !immersiveTempleChat ? 'transparent' : undefined }}
        >
          {activeTabKey === 'Temples' ? (
            <TempleDiscovery
              templeSearch={templeSearch}
              setTempleSearch={setTempleSearch}
              selectedDiscoveryTemple={selectedDiscoveryTemple}
              selectDiscoveryTemple={selectDiscoveryTemple}
              openTempleExperience={openTempleExperience}
              openPurpose={openPurpose}
              onAskAI={handleAskAI}
            />
          ) : activeTabKey === 'My Journey' ? (
            <MyJourney
              user={user}
              conversations={conversations}
              favorites={favorites}
              loadConversation={loadConversation}
            />
          ) : activeTabKey === 'About' ? (
            <About />
          ) : !isChatMode ? (
            <HomeHero
              t={t}
              isListening={isListening}
              toggleVoice={toggleVoice}
              handleTabChange={handleTabChange}
              handleSend={handleSend}
              query={query}
              setQuery={setQuery}
              beginPilgrimagePlanning={beginPilgrimagePlanning}
            />
          ) : (
            <ChatUI
              messages={messages}
              query={query}
              isLoading={isLoading}
              user={user}
              selectedTemple={selectedTemple}
              favorites={favorites}
              t={t}
              setQuery={setQuery}
              handleSend={handleSend}
              speakText={speakText}
              submitFeedback={submitFeedback}
              toggleFavorite={toggleFavorite}
              threadEndRef={threadEndRef}
            />
          )}
        </main>
      </div>
      {isYadadriSelected && (
        <TempleExperienceHero
          selectedDiscoveryTemple={selectedDiscoveryTemple}
          videoUrl={videoUrls[selectedDiscoveryTemple?.slug]}
          setSelectedTemple={setSelectedTemple}
          handleTabChange={handleTabChange}
          onAskAI={handleAskAI}
          onBackToTemples={() => {
            if (window.history.state && window.history.state.slug) {
              window.history.back()
            } else {
              window.history.replaceState({ key: 'Temples' }, '', '/temples')
              parsePathAndApplyState('/temples')
            }
          }}
        />
      )}
    </div>
  )
}


