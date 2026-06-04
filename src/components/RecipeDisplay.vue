<template>
  <div class="recipe">
    <div class="title-row">
      <h2>{{ recipe.title }}</h2>
      <button class="copy-btn" @click="copyToClipboard">{{ copyLabel }}</button>
    </div>

    <!-- Unit toggle -->
    <div class="controls-row">
      <span class="controls-label">Units:</span>
      <div class="unit-toggle">
        <button
          :class="{ active: unitSystem === 'imperial' }"
          @click="unitSystem = 'imperial'"
        >Imperial</button>
        <button
          :class="{ active: unitSystem === 'metric' }"
          @click="unitSystem = 'metric'"
        >Metric</button>
      </div>
      <span
        class="unit-note"
        title="Volume is converted as volume (e.g. 1 cup → 240 mL), not by weight (grams). This is how the recipe measures it, not necessarily how metric bakers would measure it."
      >ⓘ</span>
    </div>

    <!-- Ingredients -->
    <section class="ingredients">
      <h3>Ingredients</h3>
      <div v-for="sub in recipe.subrecipes" :key="sub.name" class="subrecipe">
        <h4 v-if="sub.name">{{ sub.name }}</h4>
        <ul>
          <li v-for="ing in sub.ingredients" :key="ing.id">
            <div class="ingredient-row">
              <template v-if="scaleFactor === 1">
                <span class="item">{{ ing.original }}</span>
              </template>
              <template v-else>
                <span
                  class="amount"
                  :class="{ approx: amountInfo(ing).prefix }"
                  :title="amountInfo(ing).tooltip || undefined"
                >{{ amountInfo(ing).prefix }}{{ amountInfo(ing).label }}</span>
                <span class="item">{{ ing.tail || ing.item }}</span>
              </template>
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
      <div
        v-for="(section, si) in recipe.direction_sections"
        :key="si"
        class="direction-section"
      >
        <h4 v-if="section.heading" class="direction-heading">{{ section.heading }}</h4>
        <ol :start="sectionStart(si)">
          <li v-for="(step, i) in section.steps" :key="i">
            <span v-for="(seg, j) in step.segments" :key="j">
              <span v-if="seg.type === 'text'">{{ convertedText(seg.content) }}</span>
              <span v-else class="inline-amount">
                {{ seg.matched_text }}<span
                  class="bracket"
                  :class="{ approx: scaledAmountInfo(seg.ingredient_id).prefix }"
                  :title="scaledAmountInfo(seg.ingredient_id).tooltip || undefined"
                > [{{ scaledAmountInfo(seg.ingredient_id).prefix }}{{ scaledAmountInfo(seg.ingredient_id).label }}]</span>
              </span>
            </span>
          </li>
        </ol>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { convertIngredient, convertTemperatureInText } from '../unitConverter.js'

const props = defineProps({
  recipe: { type: Object, required: true },
})

const scaleFactor = ref(1)
const copyLabel = ref('Copy')
const unitSystem = ref('imperial')

// Flat list of all ingredients across all subrecipes for lookup by id
const allIngredients = computed(() =>
  props.recipe.subrecipes.flatMap((sub) => sub.ingredients)
)

function scaledAmount(ing) {
  if (ing.amount === null) return null
  return ing.amount * scaleFactor.value
}

// Returns { label, prefix, tooltip, clipExtra } for an ingredient at current scale + unit system.
function amountInfo(ing) {
  const scaled = scaledAmount(ing)
  return convertIngredient(scaled, ing.unit, unitSystem.value)
}

function scaledAmountInfo(ingredientId) {
  const ing = allIngredients.value.find((i) => i.id === ingredientId)
  if (!ing) return { label: '', prefix: '', tooltip: null, clipExtra: null }
  return amountInfo(ing)
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

// Apply temperature conversion to a direction text segment.
function convertedText(content) {
  return convertTemperatureInText(content, unitSystem.value)
}

// Returns the 1-based starting step number for an ol in the given section index.
function sectionStart(sectionIndex) {
  let count = 1
  for (let i = 0; i < sectionIndex; i++) {
    count += props.recipe.direction_sections[i].steps.length
  }
  return count
}

// Build a plain-text representation of a direction step for the clipboard.
// Includes exact values and originals in parentheses where relevant.
function renderStep(step) {
  return step.segments
    .map((seg) => {
      if (seg.type === 'text') return convertedText(seg.content)
      const info = scaledAmountInfo(seg.ingredient_id)
      const amountStr = `${info.prefix}${info.label}${info.clipExtra ? ' ' + info.clipExtra : ''}`
      return `${seg.matched_text} [${amountStr}]`
    })
    .join('')
}

function buildPlainText() {
  const lines = [props.recipe.title, '']

  lines.push('INGREDIENTS')
  for (const sub of props.recipe.subrecipes) {
    if (sub.name) lines.push(sub.name)
    for (const ing of sub.ingredients) {
      if (scaleFactor.value === 1) {
        lines.push(ing.original)
      } else {
        const info = amountInfo(ing)
        const amountStr = info.label
          ? `${info.prefix}${info.label}${info.clipExtra ? ' ' + info.clipExtra : ''}`
          : ''
        const tail = ing.tail || ing.item
        lines.push(amountStr ? `${amountStr} ${tail}` : tail)
      }
    }
    lines.push('')
  }

  lines.push('DIRECTIONS')
  let stepNum = 1
  for (const section of props.recipe.direction_sections) {
    if (section.heading) lines.push(`\n${section.heading}`)
    for (const step of section.steps) {
      lines.push(`${stepNum}. ${renderStep(step)}`)
      stepNum++
    }
  }

  return lines.join('\n').trim()
}

async function copyToClipboard() {
  try {
    await navigator.clipboard.writeText(buildPlainText())
    copyLabel.value = 'Copied!'
    setTimeout(() => { copyLabel.value = 'Copy' }, 2000)
  } catch {
    copyLabel.value = 'Failed'
    setTimeout(() => { copyLabel.value = 'Copy' }, 2000)
  }
}
</script>

<style scoped>
.title-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid #ddd;
  padding-bottom: 0.75rem;
}

.recipe h2 {
  font-size: 1.6rem;
  font-weight: normal;
}

.copy-btn {
  flex-shrink: 0;
  padding: 0.3rem 0.8rem;
  font-size: 0.85rem;
  font-family: inherit;
  background: transparent;
  border: 1px solid #aaa;
  border-radius: 4px;
  cursor: pointer;
  color: #555;
}

.copy-btn:hover {
  background: #f0f0f0;
  border-color: #888;
  color: #2c2c2c;
}

/* Unit toggle */
.controls-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 2rem;
}

.controls-label {
  font-size: 0.85rem;
  color: #666;
}

.unit-toggle {
  display: flex;
  border: 1px solid #ccc;
  border-radius: 4px;
  overflow: hidden;
}

.unit-toggle button {
  padding: 0.25rem 0.75rem;
  font-size: 0.85rem;
  font-family: inherit;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #555;
}

.unit-toggle button + button {
  border-left: 1px solid #ccc;
}

.unit-toggle button.active {
  background: #2c2c2c;
  color: #fff;
}

.unit-toggle button:not(.active):hover {
  background: #f0f0f0;
}

.unit-note {
  font-size: 0.8rem;
  color: #aaa;
  cursor: help;
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

.amount.approx {
  cursor: help;
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
.direction-section {
  margin-bottom: 1.5rem;
}

.direction-heading {
  font-size: 0.95rem;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #444;
  margin-bottom: 0.5rem;
  margin-top: 1.5rem;
}

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

.inline-amount .bracket.approx {
  cursor: help;
}
</style>
