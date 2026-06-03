import { describe, test, expect } from 'vitest'
import { convertIngredient, convertTemperatureInText } from './unitConverter.js'

// ── convertIngredient ─────────────────────────────────────────────────────────

describe('convertIngredient', () => {

  describe('no conversion needed', () => {
    test('null amount returns empty result', () => {
      const r = convertIngredient(null, 'cup', 'metric')
      expect(r.label).toBe('')
      expect(r.prefix).toBe('')
      expect(r.tooltip).toBeNull()
      expect(r.clipExtra).toBeNull()
    })

    test('already in target system (imperial → imperial)', () => {
      const r = convertIngredient(1, 'cup', 'imperial')
      expect(r.label).toBe('1 cup')
      expect(r.prefix).toBe('')
      expect(r.tooltip).toBeNull()
    })

    test('already in target system (metric → metric)', () => {
      const r = convertIngredient(250, 'ml', 'metric')
      expect(r.label).toBe('250 ml')
      expect(r.prefix).toBe('')
      expect(r.tooltip).toBeNull()
    })

    test('unknown unit passes through unchanged', () => {
      const r = convertIngredient(2, 'cloves', 'metric')
      expect(r.label).toBe('2 cloves')
      expect(r.prefix).toBe('')
      expect(r.tooltip).toBeNull()
    })

    test('empty unit (count ingredient) passes through', () => {
      const r = convertIngredient(3, '', 'metric')
      expect(r.label).toBe('3')
      expect(r.prefix).toBe('')
      expect(r.tooltip).toBeNull()
    })

    test('unit aliases are normalized (cups → cup)', () => {
      const r = convertIngredient(1, 'cups', 'imperial')
      expect(r.label).toBe('1 cups')  // passes through with original rawUnit
      expect(r.tooltip).toBeNull()
    })
  })

  describe('imperial volume → metric', () => {
    test('1 cup → 237 mL', () => {
      // 1 × 236.588 = 236.588 → round(236.588) = 237
      const r = convertIngredient(1, 'cup', 'metric')
      expect(r.label).toBe('237 mL')
      expect(r.prefix).toBe('')  // 0.17% error, under 2% threshold
      expect(r.tooltip).toContain('original: 1 cup')
      expect(r.clipExtra).toContain('original: 1 cup')
    })

    test('1 tsp → 4.9 mL', () => {
      // 1 × 4.92892 = 4.92892 → round(4.929×10)/10 = 4.9
      const r = convertIngredient(1, 'tsp', 'metric')
      expect(r.label).toBe('4.9 mL')
      expect(r.prefix).toBe('')  // 0.59% error
    })

    test('½ tsp → 2.5 mL', () => {
      // 0.5 × 4.92892 = 2.46446 → round(2.464×10)/10 = 2.5
      const r = convertIngredient(0.5, 'tsp', 'metric')
      expect(r.label).toBe('2.5 mL')
      expect(r.prefix).toBe('')  // 1.46% error
    })

    test('¼ tsp → ~1.2 mL (isApprox)', () => {
      // 0.25 × 4.92892 = 1.23223 → round(1.232×10)/10 = 1.2
      // error: |1.2 - 1.232| / 1.232 = 2.6% > 2%
      const r = convertIngredient(0.25, 'tsp', 'metric')
      expect(r.label).toBe('1.2 mL')
      expect(r.prefix).toBe('~')
      expect(r.tooltip).toContain('exact:')
      expect(r.tooltip).toContain('original: ¼ tsp')
      expect(r.clipExtra).toContain('exact:')
    })

    test('1 tbsp → 15 mL', () => {
      // 1 × 14.7868 = 14.7868 → round(14.787) = 15
      const r = convertIngredient(1, 'tbsp', 'metric')
      expect(r.label).toBe('15 mL')
      expect(r.prefix).toBe('')  // 1.44% error
    })

    test('¼ cup → 59 mL (not rounded to 60)', () => {
      // 0.25 × 236.588 = 59.147 → round(59.147) = 59
      const r = convertIngredient(0.25, 'cup', 'metric')
      expect(r.label).toBe('59 mL')
      expect(r.prefix).toBe('')
    })

    test('2 cups → 473 mL', () => {
      // 2 × 236.588 = 473.176 → round(473.176) = 473
      const r = convertIngredient(2, 'cup', 'metric')
      expect(r.label).toBe('473 mL')
    })

    test('4 cups → 946 mL', () => {
      // 4 × 236.588 = 946.352 → round = 946
      const r = convertIngredient(4, 'cup', 'metric')
      expect(r.label).toBe('946 mL')
    })

    test('1 gallon → L (large volume)', () => {
      // 1 × 3785.41 = 3785.41 → ≥1000 → round(3785.41/10)/100 = 3.79 L
      const r = convertIngredient(1, 'gallon', 'metric')
      expect(r.label).toBe('3.79 L')
      expect(r.prefix).toBe('')  // < 2% error
    })

    test('unit aliases work (teaspoon, tablespoon)', () => {
      const tsp = convertIngredient(1, 'teaspoon', 'metric')
      const tbsp = convertIngredient(1, 'tablespoon', 'metric')
      expect(tsp.label).toBe('4.9 mL')
      expect(tbsp.label).toBe('15 mL')
    })
  })

  describe('imperial weight → metric', () => {
    test('1 oz → 28 g', () => {
      // 1 × 28.3495 = 28.3495 → round(28.35) = 28
      const r = convertIngredient(1, 'oz', 'metric')
      expect(r.label).toBe('28 g')
      expect(r.prefix).toBe('')  // 1.23% error
      expect(r.tooltip).toContain('original: 1 oz')
    })

    test('1 lb → 454 g', () => {
      // 1 × 453.592 = 453.592 → round(453.592) = 454
      const r = convertIngredient(1, 'lb', 'metric')
      expect(r.label).toBe('454 g')
      expect(r.prefix).toBe('')
    })

    test('2 lb → 907 g', () => {
      // 2 × 453.592 = 907.184 → round(907.184) = 907
      const r = convertIngredient(2, 'lb', 'metric')
      expect(r.label).toBe('907 g')
    })

    test('unit aliases work (pound, ounce)', () => {
      const lb = convertIngredient(1, 'pound', 'metric')
      const oz = convertIngredient(1, 'ounce', 'metric')
      expect(lb.label).toBe('454 g')
      expect(oz.label).toBe('28 g')
    })
  })

  describe('metric volume → imperial', () => {
    test('250 ml → cup', () => {
      // 250 mL → mlToImperial: ≥ 141.95 → cup → 250/236.588 = 1.0563
      // formatImperial(1.0563): round to 1/8 → round(8.45)/8 = 8/8 = 1
      // isApprox: |1 - 1.056| / 1.056 = 5.3% > 2% → ~
      const r = convertIngredient(250, 'ml', 'imperial')
      expect(r.label).toBe('1 cup')
      expect(r.prefix).toBe('~')
      expect(r.tooltip).toContain('original: 250 ml')
    })

    test('240 ml → 1 cup (close match, not approx)', () => {
      // 240 / 236.588 = 1.0144 → round(8.115)/8 = 8/8 = 1
      // isApprox: |1 - 1.014| / 1.014 = 1.42% < 2% → no ~
      const r = convertIngredient(240, 'ml', 'imperial')
      expect(r.label).toBe('1 cup')
      expect(r.prefix).toBe('')
    })

    test('15 ml → 1 tbsp', () => {
      // 15 / 14.7868 = 1.0144 → round(8.115)/8 = 8/8 = 1
      const r = convertIngredient(15, 'ml', 'imperial')
      expect(r.label).toBe('1 tbsp')
      expect(r.prefix).toBe('')
    })

    test('5 ml → 1 tsp', () => {
      // 5 / 4.92892 = 1.0144 → 1
      const r = convertIngredient(5, 'ml', 'imperial')
      expect(r.label).toBe('1 tsp')
    })

    test('tooltip contains original metric unit', () => {
      const r = convertIngredient(250, 'ml', 'imperial')
      expect(r.tooltip).toContain('original: 250 ml')
    })
  })

  describe('metric weight → imperial', () => {
    test('100 g → 3 ½ oz', () => {
      // 100 / 28.3495 = 3.5274 → round(3.527×8)/8 = round(28.22)/8 = 28/8 = 3.5 → "3 ½"
      const r = convertIngredient(100, 'g', 'imperial')
      expect(r.label).toBe('3 ½ oz')
      expect(r.prefix).toBe('')  // 0.77% error
    })

    test('500 g → lb', () => {
      // 500 ≥ 362.87 → lb → 500/453.592 = 1.1023
      // round(1.1023*8)/8 = round(8.818)/8 = 9/8 = 1.125 → "1 ⅛"
      const r = convertIngredient(500, 'g', 'imperial')
      expect(r.label).toBe('1 ⅛ lb')
    })

    test('tooltip contains original metric unit', () => {
      const r = convertIngredient(100, 'g', 'imperial')
      expect(r.tooltip).toContain('original: 100 g')
    })
  })

  describe('tooltip and clipExtra format', () => {
    test('non-approx conversion has tooltip with original only', () => {
      const r = convertIngredient(1, 'cup', 'metric')
      expect(r.tooltip).not.toContain('exact:')
      expect(r.tooltip).toContain('original: 1 cup')
      expect(r.clipExtra).toBe('(original: 1 cup)')
    })

    test('approx conversion has tooltip with exact and original', () => {
      const r = convertIngredient(0.25, 'tsp', 'metric')
      expect(r.tooltip).toContain('exact:')
      expect(r.tooltip).toContain('original: ¼ tsp')
      expect(r.clipExtra).toContain('exact:')
      expect(r.clipExtra).toContain('original: ¼ tsp')
    })

    test('clipExtra is wrapped in parentheses', () => {
      const r = convertIngredient(1, 'cup', 'metric')
      expect(r.clipExtra).toMatch(/^\(.*\)$/)
    })
  })

  describe('scaling interaction', () => {
    test('scaled amount converts correctly (2× scale)', () => {
      // scaledAmount = 2 cups at 2× scale
      const r = convertIngredient(2, 'cup', 'metric')
      // 2 × 236.588 = 473.176 → 473 mL
      expect(r.label).toBe('473 mL')
    })

    test('fractional scale converts correctly (½ cup)', () => {
      const r = convertIngredient(0.5, 'cup', 'metric')
      // 0.5 × 236.588 = 118.294 → round(118.294) = 118
      expect(r.label).toBe('118 mL')
    })
  })
})

// ── convertTemperatureInText ──────────────────────────────────────────────────

describe('convertTemperatureInText', () => {

  describe('Fahrenheit → Celsius (targeting metric)', () => {
    test('350°F → 175°C', () => {
      // (350-32)*5/9 = 176.67 → round(176.67/5)*5 = 175
      const result = convertTemperatureInText('Preheat to 350°F.', 'metric')
      expect(result).toContain('175°C')
      expect(result).toContain('original: 350°F')
    })

    test('no ~ when rounding error < 2%', () => {
      // 350°F: |175-176.67|/176.67 = 0.95% < 2%
      const result = convertTemperatureInText('350°F', 'metric')
      expect(result).not.toContain('~')
    })

    test('400°F → 205°C', () => {
      // (400-32)*5/9 = 204.44 → round(204.44/5)*5 = 205
      const result = convertTemperatureInText('400°F', 'metric')
      expect(result).toContain('205°C')
    })

    test('handles "degrees F" format', () => {
      const result = convertTemperatureInText('Bake at 350 degrees F.', 'metric')
      expect(result).toContain('175°C')
    })

    test('handles °F with space', () => {
      const result = convertTemperatureInText('Heat to 350 °F', 'metric')
      expect(result).toContain('175°C')
    })

    test('converts multiple temperatures in one string', () => {
      const result = convertTemperatureInText(
        'Start at 350°F then increase to 400°F.',
        'metric'
      )
      expect(result).toContain('175°C')
      expect(result).toContain('205°C')
    })

    test('leaves text without temperatures unchanged', () => {
      const result = convertTemperatureInText('Mix well and refrigerate.', 'metric')
      expect(result).toBe('Mix well and refrigerate.')
    })
  })

  describe('Celsius → Fahrenheit (targeting imperial)', () => {
    test('180°C → 355°F', () => {
      // 180*9/5+32 = 356 → round(356/5)*5 = 355
      const result = convertTemperatureInText('Bake at 180°C.', 'imperial')
      expect(result).toContain('355°F')
      expect(result).toContain('original: 180°C')
    })

    test('100°C → 212°F (exact, no ~)', () => {
      // 100*9/5+32 = 212 → round(212/5)*5 = 210. Wait:
      // Math.round(212/5)*5 = Math.round(42.4)*5 = 42*5 = 210
      // isApprox: |210-212|/212 = 0.94% < 2% → no ~
      const result = convertTemperatureInText('100°C', 'imperial')
      expect(result).toContain('210°F')
      expect(result).not.toContain('~')
    })

    test('handles "degrees Celsius" format', () => {
      const result = convertTemperatureInText('180 degrees Celsius', 'imperial')
      expect(result).toContain('355°F')
    })
  })

  describe('same-system text left unchanged', () => {
    test('°F text unchanged when targeting imperial', () => {
      const input = 'Preheat to 350°F.'
      expect(convertTemperatureInText(input, 'imperial')).toBe(input)
    })

    test('°C text unchanged when targeting metric', () => {
      const input = 'Bake at 175°C.'
      expect(convertTemperatureInText(input, 'metric')).toBe(input)
    })
  })
})
