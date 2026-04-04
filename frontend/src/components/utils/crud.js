export function getApiError(error, fallback = 'Request failed') {
  const detail = error?.response?.data?.detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || JSON.stringify(item)).join(', ')
  }
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }
  return fallback
}

export function pick(obj, keys) {
  const output = {}
  keys.forEach((key) => {
    if (obj[key] !== undefined) {
      output[key] = obj[key]
    }
  })
  return output
}

export function toNullableInt(value) {
  if (value === '' || value === null || value === undefined) return null
  const parsed = Number(value)
  return Number.isNaN(parsed) ? null : parsed
}

export function toNullableString(value) {
  if (value === undefined || value === null) return null
  const trimmed = String(value).trim()
  return trimmed === '' ? null : trimmed
}

export function toDateInput(value) {
  if (!value) return ''
  const date = String(value)
  return date.length >= 10 ? date.slice(0, 10) : date
}
