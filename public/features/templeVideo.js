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
  return `https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&mute=1&controls=0&disablekb=1&fs=0&loop=1&playlist=${videoId}&playsinline=1&rel=0&modestbranding=1&iv_load_policy=3`
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
