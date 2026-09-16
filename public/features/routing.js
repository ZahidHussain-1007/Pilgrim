export const ROUTE_TO_TAB = {
  '/': 'Home',
  '/home': 'Home',
  '/about': 'About',
  '/temples': 'Temples',
  '/darshan': 'Darshan Booking',
  '/accommodation': 'Accommodation',
  '/travel': 'Travel Guide',
  '/rituals': 'Rituals',
  '/journey': 'My Journey',
  '/settings': 'Settings',
}

export const TAB_TO_ROUTE = {
  'Home': '/',
  'About': '/about',
  'Temples': '/temples',
  'Darshan Booking': '/darshan',
  'Accommodation': '/accommodation',
  'Travel Guide': '/travel',
  'Rituals': '/rituals',
  'My Journey': '/journey',
  'Settings': '/settings',
}

export function parsePathAndApplyState(path, templesList, actions) {
  const { 
    setActiveTabKey, 
    setSelectedDiscoveryTemple, 
    setIsYadadriSelected, 
    setSelectedTemple, 
    setConversationId, 
    loadConversation 
  } = actions

  const cleanPath = path.length > 1 && path.endsWith('/') ? path.slice(0, -1) : path

  if (cleanPath.startsWith('/c/')) {
    const param = cleanPath.slice(3)
    if (!param) {
      return { fallback: '/', tab: 'Home' }
    }

    const temple = templesList.find((t) => t.slug === param)
    if (temple) {
      setActiveTabKey('Home')
      setIsYadadriSelected(false)
      if (setSelectedTemple) setSelectedTemple(temple.slug)
      if (setSelectedDiscoveryTemple) setSelectedDiscoveryTemple(temple)
      return { valid: true, type: 'temple-conversation', slug: temple.slug }
    } else {
      setActiveTabKey('Home')
      setIsYadadriSelected(false)
      if (setConversationId) setConversationId(param)
      if (loadConversation) loadConversation(param)
      return { valid: true, type: 'conversation', conversationId: param }
    }
  }

  if (cleanPath.startsWith('/temples/')) {
    const slug = cleanPath.slice(9)
    const temple = templesList.find((t) => t.slug === slug)
    if (temple) {
      setActiveTabKey('Temples')
      setSelectedDiscoveryTemple(temple)
      setIsYadadriSelected(true)
      return { valid: true, type: 'temple-details', temple }
    } else {
      return { fallback: '/temples', tab: 'Temples' }
    }
  }

  const tab = ROUTE_TO_TAB[cleanPath]
  if (tab) {
    setActiveTabKey(tab)
    setIsYadadriSelected(false)
    return { valid: true, type: 'tab', tab }
  }

  return { fallback: '/', tab: 'Home' }
}

export function handleTabChange(key, templesList, actions) {
  const route = TAB_TO_ROUTE[key] || '/'
  if (window.location.pathname !== route) {
    window.history.pushState({ key }, '', route)
  }
  const result = parsePathAndApplyState(route, templesList, actions)
  if (!result.valid) {
    window.history.replaceState({ key: result.tab }, '', result.fallback)
    parsePathAndApplyState(result.fallback, templesList, actions)
  }
}

export function navigateToTemple(temple, templesList, actions) {
  const route = `/temples/${temple.slug}`
  if (window.location.pathname !== route) {
    window.history.pushState({ key: 'Temples', slug: temple.slug }, '', route)
  }
  return parsePathAndApplyState(route, templesList, actions)
}

export function navigateToTempleConversation(templeSlug, templesList, actions) {
  const route = `/c/${templeSlug}`
  if (window.location.pathname !== route) {
    window.history.pushState({ key: 'Conversation', templeSlug }, '', route)
  }
  return parsePathAndApplyState(route, templesList, actions)
}

export function navigateToConversation(conversationId, templesList, actions) {
  const route = `/c/${conversationId}`
  if (window.location.pathname !== route) {
    window.history.pushState({ key: 'Conversation', conversationId }, '', route)
  }
  return parsePathAndApplyState(route, templesList, actions)
}
