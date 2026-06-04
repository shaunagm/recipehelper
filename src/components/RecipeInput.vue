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
      <p v-if="error && !blocked && !noSchema" class="error">{{ error }}</p>
    </form>

    <!-- Context-specific error messages -->
    <p v-if="blocked" class="error">
      This site blocked the request. Use the bookmarklet below to load the recipe instead.
    </p>
    <p v-if="noSchema" class="error">
      This site doesn't use standard recipe markup, so it can't be parsed automatically.
      Try pasting the JSON-LD below. If you can't find a block, the page doesn't have data
      in a format this tool can read and you won't be able to use this app for that recipe.
    </p>

    <!-- Always-visible alternative input methods -->
    <div class="alt-section">
      <div class="alt-header">Alternative input methods</div>

      <div class="bookmarklet-section">
        <p class="label">Bookmarklet — install once, use on any site</p>
        <p class="hint">
          Drag this link to your bookmarks bar. On mobile: bookmark any page, then edit that
          bookmark and replace its URL with the code shown below.
        </p>
        <a :href="bookmarkletHref" class="bookmarklet-link" @click.prevent>
          📖 Get Recipe
        </a>
        <details class="code-details">
          <summary>Show bookmarklet code</summary>
          <textarea class="code-box" readonly :value="bookmarkletCode" />
        </details>
        <p class="hint" style="margin-top: 0.6rem;">
          Once installed, navigate to a recipe page and tap the
          <strong>📖 Get Recipe</strong> bookmark — it will bring you straight back here with
          the recipe loaded.
        </p>
      </div>

      <div class="bookmarklet-section">
        <p class="label">Paste JSON-LD manually</p>
        <p class="hint">
          Open the recipe page, view its source (Ctrl+U or right-click → View Page Source),
          and search for <code>application/ld+json</code>. If you find a block containing
          <code>"@type": "Recipe"</code>, paste it below.
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
const noSchema = ref(false)

const jsonldPaste = ref('')
const parsing = ref(false)
const parseError = ref('')

const APP_URL = window.location.origin + window.location.pathname

const bookmarkletCode = `javascript:(function(){var s=document.querySelectorAll('script[type="application/ld+json"]');var j=Array.from(s).map(function(x){return x.textContent}).join('\\n');if(!j){alert('No recipe data found on this page.');}else{location.href='${APP_URL}#ld='+encodeURIComponent(j);}})();`

const bookmarkletHref = computed(() => bookmarkletCode)

async function submit() {
  error.value = ''
  blocked.value = false
  noSchema.value = false
  loading.value = true
  try {
    const recipe = await fetchRecipe(url.value)
    emit('recipe-loaded', recipe)
  } catch (e) {
    error.value = e.message
    if (e.status === 502 || e.status === 403) {
      blocked.value = true
    } else if (e.status === 422 && e.message.includes('standard recipe markup')) {
      noSchema.value = true
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
    noSchema.value = false
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

/* Alternative input methods */
.alt-section {
  margin-top: 1.5rem;
  border-top: 1px solid #ddd;
  padding-top: 1.25rem;
}

.alt-header {
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #888;
  margin-bottom: 1rem;
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
