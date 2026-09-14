export const ROUTE_TO_TAB = {
  '/': 'Home',
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
  'Temples': '/temples',
  'Darshan Booking': '/darshan',
  'Accommodation': '/accommodation',
  'Travel Guide': '/travel',
  'Rituals': '/rituals',
  'My Journey': '/journey',
  'Settings': '/settings',
}

export function parsePathAndApplyState(path, templesList, actions) {
  const { setActiveTabKey, setSelectedDiscoveryTemple, setIsYadadriSelected } = actions;
  
  if (path.startsWith('/temples/')) {
    const slug = path.split('/')[2]
    const temple = templesList.find((t) => t.slug === slug)
    if (temple) {
      setActiveTabKey('Temples')
      setSelectedDiscoveryTemple(temple)
      setIsYadadriSelected(true)
      return { valid: true }
    } else {
      return { fallback: '/temples', tab: 'Temples' }
    }
  }
  
  const tab = ROUTE_TO_TAB[path]
  if (tab) {
    setActiveTabKey(tab)
    setIsYadadriSelected(false)
    return { valid: true }
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
