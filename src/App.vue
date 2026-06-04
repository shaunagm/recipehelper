<template>
  <div id="app">
    <h1>Recipe Helper</h1>
    <RecipeInput :collapsed="!!recipe" @recipe-loaded="onRecipeLoaded" />
    <p v-if="hashError" class="hash-error">{{ hashError }}</p>
    <RecipeDisplay v-if="recipe" :recipe="recipe" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import RecipeInput from './components/RecipeInput.vue'
import RecipeDisplay from './components/RecipeDisplay.vue'
import { parseFromJsonLd } from './recipeFetcher.js'

const recipe = ref(null)
const hashError = ref('')

function onRecipeLoaded(data) {
  recipe.value = data
}

// When the bookmarklet redirects here with #ld=<encoded JSON-LD>,
// extract it, post to the backend, and load the recipe automatically.
onMounted(async () => {
  const hash = window.location.hash
  if (!hash.startsWith('#ld=')) return

  const encoded = hash.slice(4)
  // Clear the hash so it doesn't persist in the URL or get shared accidentally
  history.replaceState(null, '', window.location.pathname)

  try {
    const jsonld = JSON.parse(decodeURIComponent(encoded))
    recipe.value = await parseFromJsonLd(jsonld)
  } catch (e) {
    hashError.value = `Could not load recipe from bookmarklet: ${e.message}`
  }
})
</script>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: Georgia, 'Times New Roman', serif;
  background: #faf9f6;
  color: #2c2c2c;
  line-height: 1.6;
}

#app {
  max-width: 760px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

h1 {
  font-size: 2rem;
  font-weight: normal;
  margin-bottom: 1.5rem;
  color: #1a1a1a;
}

.hash-error {
  color: #c0392b;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}
</style>
