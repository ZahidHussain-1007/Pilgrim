export const TEMPLE_BACKGROUND_VIDEO_IDS = {
  yadadri: 'LEVXNv6seKY',
  birla_mandir: '4gRKjNxayf8',
  manyamkonda: 'niyPfnIX-hg',
  jogulamba: 'ySmpvv8s8CM',
  kommuravelli: 'T-f1tAIxeXY',
  keesaragutta: 'LRfsuOMBs2c',
  sanghi: 'myh9r2xND5o',
  kondagattu: 'P_6j5Uts3VI',
  surendrapuri: '7NDT1BGwWrg',
  medaram: 'uHZIugZLeVY',
}

const TEMPLE_VIDEO_ALIASES = {
  yadagirigutta: 'yadadri',
  'yadadri temple': 'yadadri',
  'yadagirigutta temple': 'yadadri',
  'birla mandir': 'birla_mandir',
  manyamonda: 'manyamkonda',
  'manyamonda temple': 'manyamkonda',
  'jogulamba alampur': 'jogulamba',
  'alampur jogulamba': 'jogulamba',
  komuravelli: 'kommuravelli',
  'komuravelli temple': 'kommuravelli',
}

export function normalizeTempleVideoKey(value) {
  const normalized = String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[_-]+/g, ' ')
    .replace(/\s+temple$/, '')
    .replace(/\s+/g, ' ')

  return TEMPLE_VIDEO_ALIASES[normalized] || normalized.replace(/\s+/g, '_')
}

export function templeBackgroundVideoId(value) {
  return TEMPLE_BACKGROUND_VIDEO_IDS[normalizeTempleVideoKey(value)] || null
}

export function buildYouTubeBackgroundUrl(videoId) {
  if (!videoId) return null
  return `https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&mute=1&controls=0&disablekb=1&fs=0&loop=1&playlist=${videoId}&playsinline=1&rel=0&modestbranding=1&autohide=1&showinfo=0&iv_load_policy=3&cc_load_policy=0`
}

export function convertYouTubeEmbed(url) {
  if (!url) return null
  let videoId = null
  try {
    const parsed = new URL(url)
    if (parsed.hostname === 'youtube.com' || parsed.hostname === 'www.youtube.com') {
      if (parsed.pathname === '/watch') {
        videoId = parsed.searchParams.get('v')
      } else if (parsed.pathname.startsWith('/embed/')) {
        videoId = parsed.pathname.split('/embed/')[1]
      }
    } else if (parsed.hostname === 'youtu.be') {
      videoId = parsed.pathname.slice(1)
    }
  } catch (e) {
    return null
  }
  if (!videoId) return null
  videoId = videoId.split('?')[0]
  return `https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&mute=1&controls=0&disablekb=1&fs=0&loop=1&playlist=${videoId}&playsinline=1&rel=0&modestbranding=1&autohide=1&showinfo=0&iv_load_policy=3&cc_load_policy=0`
}

export async function fetchTempleVideo(slug, baseUrl, signal) {
  try {
    const response = await fetch(`${baseUrl}/api/temples/${slug}`, { signal })
    if (response.ok) {
      const data = await response.json()
      if (data.background_video_url) {
        return convertYouTubeEmbed(data.background_video_url)
      }
    }
  } catch (e) {
    if (e.name !== 'AbortError') {
      console.error('Failed to load temple video:', e)
    }
  }
  return null
}

export async function resolveTempleVideo(slug, baseUrl, signal) {
  const mappedId = templeBackgroundVideoId(slug)
  if (mappedId) return buildYouTubeBackgroundUrl(mappedId)
  return fetchTempleVideo(slug, baseUrl, signal)
}
