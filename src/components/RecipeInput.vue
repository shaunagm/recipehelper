<template>
  <div class="input-section">
    <!-- Collapsed bar shown after a recipe loads -->
    <div v-if="collapsed && !expanded" class="collapsed-bar">
      <span class="collapsed-label">Recipe Helper</span>
      <button class="ghost-btn" @click="expanded = true">Change recipe</button>
    </div>

    <!-- Full input panel -->
    <div v-else>
      <div class="tab-bar">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab-btn"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
        <button v-if="collapsed" class="ghost-btn collapse-btn" @click="expanded = false">
          ✕ Close
        </button>
      </div>

      <!-- Tab: URL -->
      <div v-if="activeTab === 'url'" class="tab-panel">
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
        </form>
        <p v-if="blocked" class="error">
          This site blocked the request. Try the <a href="#" @click.prevent="activeTab = 'bookmarklet'">Bookmarklet</a> or <a href="#" @click.prevent="activeTab = 'jsonld'">Paste JSON-LD</a> tab instead.
        </p>
        <p v-else-if="noSchema" class="error">
          This site doesn't use standard recipe markup. Try the <a href="#" @click.prevent="activeTab = 'jsonld'">Paste JSON-LD</a> tab. If you can't find a JSON-LD block in the page source, this app can't read that recipe.
        </p>
        <p v-else-if="error" class="error">{{ error }}</p>
      </div>

      <!-- Tab: Bookmarklet -->
      <div v-if="activeTab === 'bookmarklet'" class="tab-panel">
        <p class="hint">
          Drag this link to your bookmarks bar. On mobile: bookmark any page, then edit that
          bookmark and replace its URL with the code below.
        </p>
        <a :href="bookmarkletHref" class="bookmarklet-link" @click.prevent>
          📖 Get Recipe
        </a>
        <details class="code-details">
          <summary>Show bookmarklet code</summary>
          <textarea class="code-box" readonly :value="bookmarkletCode" />
        </details>
        <p class="hint" style="margin-top: 0.75rem;">
          Once installed, navigate to a recipe page and tap <strong>📖 Get Recipe</strong> — it
          will bring you straight back here with the recipe loaded.
        </p>
      </div>

      <!-- Tab: Paste JSON-LD -->
      <div v-if="activeTab === 'jsonld'" class="tab-panel">
        <p class="hint">
          Open the recipe page, view its source (Ctrl+U or right-click → View Page Source),
          and search for <code>application/ld+json</code>. If you find a block containing
          <code>"@type": "Recipe"</code>, paste it below. If no such block exists, the page
          can't be used with this app.
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
import { ref, watch } from 'vue'
import { fetchRecipe, parseFromJsonLd } from '../recipeFetcher.js'

const props = defineProps({
  collapsed: { type: Boolean, default: false },
})
const emit = defineEmits(['recipe-loaded'])

const tabs = [
  { id: 'url', label: 'URL' },
  { id: 'bookmarklet', label: 'Bookmarklet' },
  { id: 'jsonld', label: 'Paste JSON-LD' },
]
const activeTab = ref('url')
const expanded = ref(false)

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
const bookmarkletHref = bookmarkletCode

// When a blocking error occurs, nudge the user to the relevant tab
watch(blocked, (val) => { if (val) activeTab.value = 'bookmarklet' })
watch(noSchema, (val) => { if (val) activeTab.value = 'jsonld' })

async function submit() {
  error.value = ''
  blocked.value = false
  noSchema.value = false
  loading.value = true
  try {
    const recipe = await fetchRecipe(url.value)
    emit('recipe-loaded', recipe)
    expanded.value = false
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
    expanded.value = false
  } catch (e) {
    parseError.value = e.message
  } finally {
    parsing.value = false
  }
}
</script>

<style scoped>
.input-section {
  margin-bottom: 2rem;
}

/* Collapsed bar */
.collapsed-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #ddd;
  margin-bottom: 1.5rem;
}

.collapsed-label {
  font-size: 0.9rem;
  color: #888;
}

/* Tabs */
.tab-bar {
  display: flex;
  align-items: center;
  gap: 0;
  border-bottom: 2px solid #ddd;
  margin-bottom: 1rem;
}

.tab-btn {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-family: inherit;
  background: none;
  color: #666;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  border-radius: 0;
  cursor: pointer;
  white-space: nowrap;
}

.tab-btn:hover:not(:disabled) {
  background: #f5f5f5;
  color: #2c2c2c;
}

.tab-btn.active {
  color: #2c2c2c;
  border-bottom-color: #2c2c2c;
  font-weight: 600;
}

.collapse-btn {
  margin-left: auto;
  font-size: 0.8rem;
  color: #999;
}

.tab-panel {
  padding: 0.5rem 0 0.75rem;
}

/* URL tab */
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

.ghost-btn {
  background: none;
  color: #777;
  border: 1px solid #ccc;
  padding: 0.3rem 0.75rem;
  font-size: 0.85rem;
  border-radius: 4px;
}

.ghost-btn:hover:not(:disabled) {
  background: #f5f5f5;
  color: #2c2c2c;
}

.error {
  margin-top: 0.6rem;
  color: #c0392b;
  font-size: 0.9rem;
}

.error a {
  color: #c0392b;
  font-weight: 600;
}

/* Bookmarklet tab */
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
  margin-bottom: 0.4rem;
}

.bookmarklet-link:hover {
  background: #e8e8e8;
}

.code-details {
  margin-top: 0.4rem;
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

/* JSON-LD tab */
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

.hint {
  font-size: 0.88rem;
  color: #555;
  margin-bottom: 0.6rem;
  line-height: 1.5;
}

code {
  background: #f0f0f0;
  padding: 0.1em 0.3em;
  border-radius: 3px;
  font-size: 0.85em;
}
</style>
