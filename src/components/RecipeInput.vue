<template>
  <div class="input-section">
    <form @submit.prevent="submit">
      <div class="input-row">
        <input
          v-model="url"
          type="url"
          placeholder="Paste a recipe URL…"
          :disabled="loading"
          required
        />
        <button type="submit" :disabled="loading || !url">
          {{ loading ? 'Fetching…' : 'Get Recipe' }}
        </button>
      </div>
      <p v-if="error && !blocked" class="error">{{ error }}</p>
    </form>

    <!-- Fallback shown when the site blocks our server -->
    <div v-if="blocked" class="fallback">
      <p class="error">
        This site blocked the request. Use the bookmarklet to load the recipe instead.
      </p>

      <div class="bookmarklet-section">
        <p class="label">Step 1 — Install the bookmarklet (one time only)</p>
        <p class="hint">
          Drag this link to your bookmarks bar, or on mobile: bookmark any page,
          then edit that bookmark's URL and replace it with the code below.
        </p>
        <a :href="bookmarkletHref" class="bookmarklet-link" @click.prevent>
          📖 Get Recipe
        </a>
        <details class="code-details">
          <summary>Show bookmarklet code</summary>
          <textarea class="code-box" readonly :value="bookmarkletCode" />
        </details>
      </div>

      <div class="bookmarklet-section">
        <p class="label">Step 2 — Use it</p>
        <p class="hint">
          Go to the recipe page in your browser, then tap the
          <strong>📖 Get Recipe</strong> bookmark. It will extract the recipe
          data and bring you straight back here.
        </p>
      </div>

      <div class="bookmarklet-section">
        <p class="label">Or paste the JSON-LD manually</p>
        <p class="hint">
          View the page source, search for <code>application/ld+json</code>,
          and paste the JSON between the script tags below.
        </p>
        <textarea
          v-model="jsonldPaste"
          class="jsonld-textarea"
          placeholder='{"@context": "https://schema.org", "@type": "Recipe", ...}'
        />
        <button
          class="parse-btn"
          :disabled="!jsonldPaste.trim() || parsing"
          @click="parseJsonLd"
        >
          {{ parsing ? 'Parsing…' : 'Parse JSON-LD' }}
        </button>
        <p v-if="parseError" class="error">{{ parseError }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { fetchRecipe, parseFromJsonLd } from '../recipeFetcher.js'

const emit = defineEmits(['recipe-loaded'])

const url = ref('')
const loading = ref(false)
const error = ref('')
const blocked = ref(false)

const jsonldPaste = ref('')
const parsing = ref(false)
const parseError = ref('')

const APP_URL = window.location.origin + window.location.pathname

const bookmarkletCode = `javascript:(function(){var s=document.querySelectorAll('script[type="application/ld+json"]');var j=Array.from(s).map(function(x){return x.textContent}).join('\\n');if(!j){alert('No recipe data found on this page.');}else{location.href='${APP_URL}#ld='+encodeURIComponent(j);}})();`

const bookmarkletHref = computed(() => bookmarkletCode)

async function submit() {
  error.value = ''
  blocked.value = false
  loading.value = true
  try {
    const recipe = await fetchRecipe(url.value)
    emit('recipe-loaded', recipe)
  } catch (e) {
    error.value = e.message
    if (e.status === 502 || e.status === 403) {
      blocked.value = true
    }
  } finally {
    loading.value = false
  }
}

async function parseJsonLd() {
  parseError.value = ''
  parsing.value = true
  try {
    let data
    try {
      data = JSON.parse(jsonldPaste.value)
    } catch {
      data = jsonldPaste.value
    }
    const recipe = await parseFromJsonLd(data)
    emit('recipe-loaded', recipe)
    blocked.value = false
  } catch (e) {
    parseError.value = e.message
  } finally {
    parsing.value = false
  }
}
</script>

<style scoped>
.input-section {
  margin-bottom: 2.5rem;
}

.input-row {
  display: flex;
  gap: 0.5rem;
}

input[type="url"] {
  flex: 1;
  padding: 0.6rem 0.8rem;
  font-size: 1rem;
  font-family: inherit;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: #fff;
  color: #2c2c2c;
}

input[type="url"]:focus {
  outline: none;
  border-color: #888;
}

button {
  padding: 0.6rem 1.2rem;
  font-size: 1rem;
  font-family: inherit;
  background: #2c2c2c;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  white-space: nowrap;
}

button:hover:not(:disabled) {
  background: #444;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error {
  margin-top: 0.5rem;
  color: #c0392b;
  font-size: 0.9rem;
}

/* Fallback UI */
.fallback {
  margin-top: 1.25rem;
  border-top: 1px solid #ddd;
  padding-top: 1.25rem;
}

.bookmarklet-section {
  margin-bottom: 1.5rem;
}

.label {
  font-weight: bold;
  font-size: 0.95rem;
  margin-bottom: 0.3rem;
}

.hint {
  font-size: 0.88rem;
  color: #555;
  margin-bottom: 0.6rem;
  line-height: 1.5;
}

.bookmarklet-link {
  display: inline-block;
  padding: 0.5rem 1rem;
  background: #f0f0f0;
  border: 2px dashed #aaa;
  border-radius: 4px;
  text-decoration: none;
  color: #2c2c2c;
  font-size: 0.95rem;
  cursor: grab;
}

.bookmarklet-link:hover {
  background: #e8e8e8;
}

.code-details {
  margin-top: 0.6rem;
  font-size: 0.85rem;
}

.code-details summary {
  cursor: pointer;
  color: #666;
}

.code-box {
  display: block;
  width: 100%;
  margin-top: 0.4rem;
  padding: 0.5rem;
  font-size: 0.75rem;
  font-family: monospace;
  background: #f8f8f8;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: none;
  height: 4.5rem;
  color: #444;
}

.jsonld-textarea {
  display: block;
  width: 100%;
  height: 8rem;
  padding: 0.6rem;
  font-size: 0.85rem;
  font-family: monospace;
  border: 1px solid #ccc;
  border-radius: 4px;
  resize: vertical;
  background: #fff;
  color: #2c2c2c;
  margin-bottom: 0.5rem;
}

.parse-btn {
  margin-top: 0;
}

code {
  background: #f0f0f0;
  padding: 0.1em 0.3em;
  border-radius: 3px;
  font-size: 0.85em;
}
</style>
