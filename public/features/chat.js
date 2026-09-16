export class ChatRequestError extends Error {}

export function chatErrorMessage(status) {
  if (status === 401) return 'Please sign in to continue.'
  if (status === 422) return 'Your message could not be processed. Please check it and try again.'
  if (status === 502 || status === 503 || status === 504) return 'The PilgrimAI service is unavailable right now. Please try again shortly.'
  if (status >= 400 && status < 500) return 'Your chat request could not be completed. Please try again.'
  return 'The PilgrimAI backend encountered an error. Please try again later.'
}

export function speakText(text, lang) {
  if (!('speechSynthesis' in window)) return
  const clean = text.replace(/[*#•`_]/g, '')
  const utterance = new SpeechSynthesisUtterance(clean)
  utterance.lang = lang === 'తె' ? 'te-IN' : lang === 'हि' ? 'hi-IN' : 'en-IN'
  window.speechSynthesis.cancel()
  window.speechSynthesis.speak(utterance)
}

export async function submitFeedback(messageId, rating, baseUrl) {
  await fetch(`${baseUrl}/api/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ messageId, rating })
  })
}

export function detectTempleInText(text, templesList) {
  const lower = text.toLowerCase()
  const matched = templesList.find((tp) => {
    const names = [tp.slug, tp.name, ...(tp.aliases || [])]
    return names.some((name) => lower.includes(name.toLowerCase()))
  })
  return matched ? matched.slug : null
}

export async function sendChatMessage({ text, targetTemple, lang, conversationId, baseUrl }) {
  const response = await fetch(`${baseUrl}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      query: text,
      temple: targetTemple,
      language: lang === 'తె' ? 'te' : lang === 'हि' ? 'hi' : 'en',
      conversationId
    })
  })

  if (!response.ok) {
    throw new ChatRequestError(chatErrorMessage(response.status))
  }

  return response.json()
}

export async function fetchConversationMessages(id, baseUrl) {
  const response = await fetch(`${baseUrl}/api/conversations/${id}/messages`, { credentials: 'include' })
  if (!response.ok) return null
  return response.json()
}
