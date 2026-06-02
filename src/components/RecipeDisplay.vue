<template>
  <div class="recipe">
    <h2>{{ recipe.title }}</h2>

    <!-- Ingredients -->
    <section class="ingredients">
      <h3>Ingredients</h3>
      <div v-for="sub in recipe.subrecipes" :key="sub.name" class="subrecipe">
        <h4 v-if="sub.name">{{ sub.name }}</h4>
        <ul>
          <li v-for="ing in sub.ingredients" :key="ing.id">
            <div class="ingredient-row">
              <span class="amount">{{ displayAmount(ing) }}</span>
              <span class="item">{{ ing.item }}</span>
            </div>
            <input
              v-if="ing.amount !== null"
              type="range"
              :min="ing.amount * 0.25"
              :max="ing.amount * 4"
              :step="sliderStep(ing.amount)"
              :value="scaledAmount(ing)"
              @input="onSlider(ing, $event.target.value)"
              class="slider"
            />
          </li>
        </ul>
      </div>
    </section>

    <!-- Directions -->
    <section class="directions">
      <h3>Directions</h3>
      <ol>
        <li v-for="(step, i) in recipe.directions" :key="i">
          <span v-for="(seg, j) in step.segments" :key="j">
            <span v-if="seg.type === 'text'">{{ seg.content }}</span>
            <span v-else class="inline-amount">
              {{ seg.matched_text }}<span class="bracket"> [{{ scaledDisplayAmount(seg.ingredient_id) }}]</span>
            </span>
          </span>
        </li>
      </ol>
    </section>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  recipe: { type: Object, required: true },
})

const scaleFactor = ref(1)

// Flat list of all ingredients across all subrecipes for lookup by id
const allIngredients = computed(() =>
  props.recipe.subrecipes.flatMap((sub) => sub.ingredients)
)

function scaledAmount(ing) {
  if (ing.amount === null) return null
  return ing.amount * scaleFactor.value
}

function displayAmount(ing) {
  if (ing.amount === null) return ''
  const val = scaledAmount(ing)
  return formatNumber(val) + (ing.unit ? ' ' + ing.unit : '')
}

function scaledDisplayAmount(ingredientId) {
  const ing = allIngredients.value.find((i) => i.id === ingredientId)
  if (!ing) return ''
  return displayAmount(ing)
}

function onSlider(ing, newValue) {
  if (ing.amount === null || ing.amount === 0) return
  scaleFactor.value = parseFloat(newValue) / ing.amount
}

function sliderStep(baseAmount) {
  if (baseAmount <= 0.25) return 0.0625
  if (baseAmount <= 1) return 0.25
  if (baseAmount <= 4) return 0.5
  return 1
}

function formatNumber(n) {
  if (n === null || n === undefined) return ''
  // Round to nearest clean fraction
  const rounded = Math.round(n * 8) / 8
  const whole = Math.floor(rounded)
  const frac = rounded - whole

  const fractions = {
    0.125: '⅛',
    0.25: '¼',
    0.375: '⅜',
    0.5: '½',
    0.625: '⅝',
    0.75: '¾',
    0.875: '⅞',
  }

  const fracStr = fractions[Math.round(frac * 1000) / 1000] || ''

  if (whole === 0) return fracStr || '0'
  if (!fracStr) return String(whole)
  return `${whole} ${fracStr}`
}
</script>

<style scoped>
.recipe h2 {
  font-size: 1.6rem;
  font-weight: normal;
  margin-bottom: 2rem;
  border-bottom: 1px solid #ddd;
  padding-bottom: 0.75rem;
}

section {
  margin-bottom: 2.5rem;
}

h3 {
  font-size: 1.1rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: normal;
  color: #666;
  margin-bottom: 1rem;
}

/* Ingredients */
.subrecipe {
  margin-bottom: 1.5rem;
}

h4 {
  font-size: 0.95rem;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #444;
  margin-bottom: 0.6rem;
}

ul {
  list-style: none;
  padding: 0;
}

ul li {
  margin-bottom: 1rem;
}

.ingredient-row {
  display: flex;
  gap: 0.4rem;
  align-items: baseline;
  margin-bottom: 0.25rem;
}

.amount {
  font-weight: bold;
  min-width: 3.5rem;
  display: inline-block;
}

.item {
  color: #2c2c2c;
}

.slider {
  width: 100%;
  max-width: 300px;
  display: block;
  accent-color: #2c2c2c;
  cursor: pointer;
}

/* Directions */
ol {
  padding-left: 1.4rem;
}

ol li {
  margin-bottom: 1rem;
  line-height: 1.7;
}

.inline-amount .bracket {
  color: #888;
  font-size: 0.88em;
}
</style>
