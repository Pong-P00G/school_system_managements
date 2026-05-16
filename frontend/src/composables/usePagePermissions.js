import { ref } from 'vue'
import { getMyPages } from '../services/api'

const cachedPages = ref(null)
const cacheTimestamp = ref(0)
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

export function usePagePermissions() {
  const fetchMyPages = async () => {
    const now = Date.now()
    if (cachedPages.value && (now - cacheTimestamp.value) < CACHE_TTL) {
      return cachedPages.value
    }
    try {
      const res = await getMyPages()
      cachedPages.value = res.data
      cacheTimestamp.value = now
      return cachedPages.value
    } catch {
      return cachedPages.value || []
    }
  }

  const invalidateCache = () => {
    cachedPages.value = null
    cacheTimestamp.value = 0
  }

  return { fetchMyPages, invalidateCache }
}
