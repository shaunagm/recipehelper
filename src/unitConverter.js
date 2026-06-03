// ── Unit normalization ────────────────────────────────────────────────────────

const UNIT_ALIASES = {
  // Imperial volume
  tsp: 'tsp', teaspoon: 'tsp', teaspoons: 'tsp',
  tbsp: 'tbsp', tablespoon: 'tbsp', tablespoons: 'tbsp', tbs: 'tbsp',
  cup: 'cup', cups: 'cup', c: 'cup',
  'fl oz': 'fl oz', 'fluid ounce': 'fl oz', 'fluid ounces': 'fl oz',
  pint: 'pint', pints: 'pint', pt: 'pint',
  quart: 'quart', quarts: 'quart', qt: 'quart',
  gallon: 'gallon', gallons: 'gallon', gal: 'gallon',
  // Metric volume
  ml: 'ml', milliliter: 'ml', milliliters: 'ml', millilitre: 'ml', millilitres: 'ml',
  l: 'l', liter: 'l', liters: 'l', litre: 'l', litres: 'l',
  // Imperial weight
  oz: 'oz', ounce: 'oz', ounces: 'oz',
  lb: 'lb', lbs: 'lb', pound: 'lb', pounds: 'lb',
  // Metric weight
  g: 'g', gram: 'g', grams: 'g',
  kg: 'kg', kilogram: 'kg', kilograms: 'kg',
}

function normalizeUnit(raw) {
  if (!raw) return ''
  return UNIT_ALIASES[raw.toLowerCase().trim()] ?? ''
}

// ── Unit info (conversion factors) ───────────────────────────────────────────

const UNIT_INFO = {
  // Imperial volume → mL
  tsp:      { system: 'imperial', category: 'volume', toMl: 4.92892 },
  tbsp:     { system: 'imperial', category: 'volume', toMl: 14.7868 },
  'fl oz':  { system: 'imperial', category: 'volume', toMl: 29.5735 },
  cup:      { system: 'imperial', category: 'volume', toMl: 236.588 },
  pint:     { system: 'imperial', category: 'volume', toMl: 473.176 },
  quart:    { system: 'imperial', category: 'volume', toMl: 946.353 },
  gallon:   { system: 'imperial', category: 'volume', toMl: 3785.41 },
  // Metric volume (base: mL)
  ml:       { system: 'metric',   category: 'volume', toMl: 1 },
  l:        { system: 'metric',   category: 'volume', toMl: 1000 },
  // Imperial weight → g
  oz:       { system: 'imperial', category: 'weight', toG: 28.3495 },
  lb:       { system: 'imperial', category: 'weight', toG: 453.592 },
  // Metric weight (base: g)
  g:        { system: 'metric',   category: 'weight', toG: 1 },
  kg:       { system: 'metric',   category: 'weight', toG: 1000 },
}

// ── Formatting helpers ────────────────────────────────────────────────────────

function formatImperial(n) {
  if (n === null || n === undefined || isNaN(n)) return ''
  const rounded = Math.round(n * 8) / 8
  const whole = Math.floor(rounded)
  const frac = Math.round((rounded - whole) * 1000) / 1000
  const FRACS = { 0.125: '⅛', 0.25: '¼', 0.375: '⅜', 0.5: '½', 0.625: '⅝', 0.75: '¾', 0.875: '⅞' }
  const fracStr = FRACS[frac] || ''
  if (whole === 0) return fracStr || '0'
  if (!fracStr) return String(whole)
  return `${whole} ${fracStr}`
}

// Round a mL value for display — preserving precision, only trimming unnecessary decimals.
function roundMl(exactMl) {
  if (exactMl >= 1000) return { val: Math.round(exactMl / 10) / 100, unit: 'L' }   // nearest 10 mL → L (2 dp)
  if (exactMl >= 10)   return { val: Math.round(exactMl),             unit: 'mL' }  // nearest integer
  if (exactMl >= 1)    return { val: Math.round(exactMl * 10) / 10,  unit: 'mL' }  // 1 decimal place
  return                      { val: Math.round(exactMl * 100) / 100, unit: 'mL' }  // 2 decimal places
}

// Round a gram value for display — same philosophy as roundMl.
function roundG(exactG) {
  if (exactG >= 1000) return { val: Math.round(exactG / 10) / 100,  unit: 'kg' }   // nearest 10 g → kg (2 dp)
  if (exactG >= 10)   return { val: Math.round(exactG),              unit: 'g' }    // nearest integer
  if (exactG >= 1)    return { val: Math.round(exactG * 10) / 10,   unit: 'g' }    // 1 decimal place
  return                     { val: Math.round(exactG * 100) / 100,  unit: 'g' }   // 2 decimal places
}

// Choose the best-fitting imperial volume unit for a given mL amount.
function mlToImperial(ml) {
  if (ml >= 946.353 * 0.8) return { val: ml / 946.353, unit: 'quart' }
  if (ml >= 236.588 * 0.6) return { val: ml / 236.588, unit: 'cup' }
  if (ml >= 14.787  * 0.6) return { val: ml / 14.7868, unit: 'tbsp' }
  return                           { val: ml / 4.92892, unit: 'tsp' }
}

// Choose the best-fitting imperial weight unit for a given gram amount.
function gToImperial(g) {
  if (g >= 453.592 * 0.8) return { val: g / 453.592, unit: 'lb' }
  return                         { val: g / 28.3495,  unit: 'oz' }
}

// ── Main conversion function ──────────────────────────────────────────────────

/**
 * Convert a (scaled) ingredient amount to the target unit system.
 *
 * Returns:
 *   label     - formatted display string, e.g. "240 mL" or "1 cup"
 *   prefix    - "" normally, "~" when the metric display value was rounded
 *   tooltip   - string for title attribute (desktop hover), or null
 *   clipExtra - additional parenthetical for clipboard output, or null
 */
export function convertIngredient(amount, rawUnit, targetSystem) {
  if (amount === null || amount === undefined) {
    return { label: '', prefix: '', tooltip: null, clipExtra: null }
  }

  const canon = normalizeUnit(rawUnit)
  const info = UNIT_INFO[canon]
  const origLabel = `${formatImperial(amount)}${rawUnit ? ' ' + rawUnit : ''}`.trim()

  // Unknown unit or already in the target system — return as-is
  if (!info || info.system === targetSystem) {
    return { label: origLabel, prefix: '', tooltip: null, clipExtra: null }
  }

  let displayVal, displayUnit, exactVal

  if (info.category === 'volume') {
    const exactMl = amount * info.toMl
    if (targetSystem === 'metric') {
      const { val, unit } = roundMl(exactMl)
      displayVal = val; displayUnit = unit
      // exactVal must be in the same unit as displayVal for isApprox comparison
      exactVal = unit === 'L' ? exactMl / 1000 : exactMl
    } else {
      const { val, unit } = mlToImperial(exactMl)
      displayVal = Math.round(val * 8) / 8  // nearest 1/8 for imperial fractions
      displayUnit = unit; exactVal = val
    }
  } else {
    const exactG = amount * info.toG
    if (targetSystem === 'metric') {
      const { val, unit } = roundG(exactG)
      displayVal = val; displayUnit = unit
      exactVal = unit === 'kg' ? exactG / 1000 : exactG
    } else {
      const { val, unit } = gToImperial(exactG)
      displayVal = Math.round(val * 8) / 8
      displayUnit = unit; exactVal = val
    }
  }

  const isApprox = exactVal !== 0 && Math.abs(displayVal - exactVal) / exactVal > 0.02

  const label = targetSystem === 'metric'
    ? `${displayVal} ${displayUnit}`
    : `${formatImperial(displayVal)} ${displayUnit}`

  const parts = []
  if (isApprox) {
    const exactStr = targetSystem === 'metric'
      ? `${exactVal.toFixed(1)} ${displayUnit}`
      : `${exactVal.toFixed(2)} ${displayUnit}`
    parts.push(`exact: ${exactStr}`)
  }
  parts.push(`original: ${origLabel}`)

  return {
    label,
    prefix: isApprox ? '~' : '',
    tooltip: parts.join(' — '),
    clipExtra: `(${parts.join(', ')})`,
  }
}

// ── Temperature conversion in direction text ──────────────────────────────────

// Matches: 350°F, 350 F, 350 degrees F, 350 degrees Fahrenheit
const TEMP_F_RE = /(\d+(?:\.\d+)?)\s*°?\s*(?:degrees?\s+)?F(?:ahrenheit)?\b/gi
// Matches: 180°C, 180 C, 180 degrees C, 180 degrees Celsius
const TEMP_C_RE = /(\d+(?:\.\d+)?)\s*°?\s*(?:degrees?\s+)?C(?:elsius)?\b/gi

/**
 * Replace temperature references in a direction text string with the
 * converted value. Always shows the original in parentheses; shows ~
 * prefix and "exact:" when the rounded display differs by more than 2%.
 */
export function convertTemperatureInText(text, targetSystem) {
  if (targetSystem === 'metric') {
    return text.replace(TEMP_F_RE, (_, n) => {
      const f = parseFloat(n)
      const exactC = (f - 32) * 5 / 9
      const roundedC = Math.round(exactC / 5) * 5
      const isApprox = Math.abs(exactC) > 0 && Math.abs(roundedC - exactC) / Math.abs(exactC) > 0.02
      const parts = []
      if (isApprox) parts.push(`exact: ${exactC.toFixed(1)}°C`)
      parts.push(`original: ${f}°F`)
      return `${isApprox ? '~' : ''}${roundedC}°C (${parts.join(', ')})`
    })
  } else {
    return text.replace(TEMP_C_RE, (_, n) => {
      const c = parseFloat(n)
      const exactF = c * 9 / 5 + 32
      const roundedF = Math.round(exactF / 5) * 5
      const isApprox = Math.abs(exactF) > 0 && Math.abs(roundedF - exactF) / Math.abs(exactF) > 0.02
      const parts = []
      if (isApprox) parts.push(`exact: ${exactF.toFixed(1)}°F`)
      parts.push(`original: ${c}°C`)
      return `${isApprox ? '~' : ''}${roundedF}°F (${parts.join(', ')})`
    })
  }
}
