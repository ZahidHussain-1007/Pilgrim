export function redirectToGoogleAuth(baseUrl) {
  window.location.assign(`${baseUrl}/auth/google`)
}

export async function executeLogout(baseUrl) {
  await fetch(`${baseUrl}/auth/logout`, { method: 'POST', credentials: 'include' })
}

export async function fetchUserData(baseUrl) {
  const meResponse = await fetch(`${baseUrl}/auth/me`, { credentials: 'include' })
  const meData = meResponse.ok ? await meResponse.json() : null
  
  if (!meData?.user) return null

  const [profileResponse, conversationResponse, favoritesResponse] = await Promise.all([
    fetch(`${baseUrl}/auth/profile`, { credentials: 'include' }),
    fetch(`${baseUrl}/api/conversations`, { credentials: 'include' }),
    fetch(`${baseUrl}/api/favorites`, { credentials: 'include' })
  ])

  const profilePayload = profileResponse.ok ? await profileResponse.json() : null
  const conversations = conversationResponse.ok ? await conversationResponse.json() : null
  const favorites = favoritesResponse.ok ? await favoritesResponse.json() : null

  return {
    user: { ...meData.user, avatarUrl: profilePayload?.profile?.avatar_url || null },
    conversations,
    favorites
  }
}
