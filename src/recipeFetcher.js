/**
 * Calls the FastAPI backend to scrape and parse a recipe URL.
 * Returns { title, subrecipes, directions }.
 *
 * In production, set VITE_API_URL to your deployed backend base URL.
 */
const API_BASE = import.meta.env.VITE_API_URL || ''

async function postToBackend(path, body) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    const error = new Error(err.detail || `Server error (${response.status})`)
    error.status = response.status
    throw error
  }

  return response.json()
}

export function fetchRecipe(url) {
  return postToBackend('/api/scrape', { url })
}

export function parseFromJsonLd(jsonld) {
  return postToBackend('/api/parse-jsonld', { jsonld })
}
