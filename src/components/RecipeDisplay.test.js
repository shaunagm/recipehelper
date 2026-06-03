import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import RecipeDisplay from './RecipeDisplay.vue'

// ── Test fixtures ─────────────────────────────────────────────────────────────

const imperialRecipe = {
  title: 'Chocolate Chip Cookies',
  subrecipes: [
    {
      name: '',
      ingredients: [
        { id: '0', original: '1 cup butter',  amount: 1,   unit: 'cup', item: 'butter' },
        { id: '1', original: '1 tsp salt',    amount: 1,   unit: 'tsp', item: 'salt' },
        { id: '2', original: '2 eggs',        amount: 2,   unit: '',    item: 'eggs' },
      ],
    },
  ],
  direction_sections: [
    {
      heading: '',
      steps: [
        {
          segments: [
            { type: 'text',       content: 'Preheat oven to 350°F. Mix ' },
            { type: 'ingredient', ingredient_id: '0', matched_text: 'butter' },
            { type: 'text',       content: ' with ' },
            { type: 'ingredient', ingredient_id: '1', matched_text: 'salt' },
            { type: 'text',       content: '.' },
          ],
        },
      ],
    },
  ],
}

const metricRecipe = {
  title: 'Metric Bread',
  subrecipes: [
    {
      name: '',
      ingredients: [
        { id: '0', original: '500 g flour', amount: 500, unit: 'g',  item: 'flour' },
        { id: '1', original: '300 ml water', amount: 300, unit: 'ml', item: 'water' },
      ],
    },
  ],
  direction_sections: [
    {
      heading: '',
      steps: [
        { segments: [{ type: 'text', content: 'Bake at 220°C until done.' }] },
      ],
    },
  ],
}

const subrecipeRecipe = {
  title: 'Layered Cake',
  subrecipes: [
    {
      name: 'Cake',
      ingredients: [
        { id: '0', original: '2 cups flour', amount: 2, unit: 'cup', item: 'flour' },
      ],
    },
    {
      name: 'Frosting',
      ingredients: [
        { id: '1', original: '1 cup butter', amount: 1, unit: 'cup', item: 'butter' },
      ],
    },
  ],
  direction_sections: [],
}

const multisectionRecipe = {
  title: 'Cinnamon Rolls',
  subrecipes: [
    {
      name: '',
      ingredients: [
        { id: '0', original: '2 cups flour', amount: 2, unit: 'cup', item: 'flour' },
        { id: '1', original: '1 cup sugar',  amount: 1, unit: 'cup', item: 'sugar' },
      ],
    },
  ],
  direction_sections: [
    {
      heading: 'Make the dough',
      steps: [
        { segments: [{ type: 'text', content: 'Mix the flour together.' }] },
        { segments: [{ type: 'text', content: 'Knead for 10 minutes.' }] },
      ],
    },
    {
      heading: 'Make the filling',
      steps: [
        { segments: [{ type: 'text', content: 'Combine sugar and cinnamon.' }] },
      ],
    },
  ],
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function mountRecipe(recipe) {
  return mount(RecipeDisplay, { props: { recipe } })
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('RecipeDisplay', () => {

  describe('basic rendering', () => {
    test('shows recipe title', () => {
      const w = mountRecipe(imperialRecipe)
      expect(w.find('h2').text()).toBe('Chocolate Chip Cookies')
    })

    test('shows ingredient items', () => {
      const w = mountRecipe(imperialRecipe)
      const items = w.findAll('.item').map((el) => el.text())
      expect(items).toContain('butter')
      expect(items).toContain('salt')
      expect(items).toContain('eggs')
    })

    test('shows subrecipe headings', () => {
      const w = mountRecipe(subrecipeRecipe)
      const headings = w.findAll('h4').map((el) => el.text())
      expect(headings).toContain('Cake')
      expect(headings).toContain('Frosting')
    })

    test('does not show subrecipe heading when name is empty', () => {
      const w = mountRecipe(imperialRecipe)
      expect(w.findAll('h4')).toHaveLength(0)
    })

    test('shows sliders for ingredients with amounts', () => {
      const w = mountRecipe(imperialRecipe)
      // eggs have amount=2, all ingredients have amounts → 3 sliders
      expect(w.findAll('input[type="range"]')).toHaveLength(3)
    })
  })

  describe('imperial mode (default)', () => {
    test('imperial toggle is active by default', () => {
      const w = mountRecipe(imperialRecipe)
      const buttons = w.findAll('.unit-toggle button')
      expect(buttons[0].classes()).toContain('active')  // Imperial button
      expect(buttons[1].classes()).not.toContain('active')
    })

    test('shows amounts in original imperial units', () => {
      const w = mountRecipe(imperialRecipe)
      const amounts = w.findAll('.amount').map((el) => el.text())
      expect(amounts[0]).toBe('1 cup')   // butter
      expect(amounts[1]).toBe('1 tsp')   // salt
      expect(amounts[2]).toBe('2')       // eggs (no unit)
    })

    test('directions show °F unchanged', () => {
      const w = mountRecipe(imperialRecipe)
      expect(w.find('ol').text()).toContain('350°F')
    })

    test('ingredient annotations show original amount', () => {
      const w = mountRecipe(imperialRecipe)
      const brackets = w.findAll('.bracket').map((el) => el.text())
      expect(brackets[0]).toContain('1 cup')   // butter annotation
      expect(brackets[1]).toContain('1 tsp')   // salt annotation
    })
  })

  describe('metric mode', () => {
    test('clicking Metric activates the metric button', async () => {
      const w = mountRecipe(imperialRecipe)
      const buttons = w.findAll('.unit-toggle button')
      await buttons[1].trigger('click')
      expect(buttons[1].classes()).toContain('active')
      expect(buttons[0].classes()).not.toContain('active')
    })

    test('amounts change to metric after toggling', async () => {
      const w = mountRecipe(imperialRecipe)
      await w.findAll('.unit-toggle button')[1].trigger('click')
      const amounts = w.findAll('.amount').map((el) => el.text())
      // 1 cup → 237 mL
      expect(amounts[0]).toBe('237 mL')
      // 1 tsp → 4.9 mL
      expect(amounts[1]).toBe('4.9 mL')
      // 2 eggs → no unit, unchanged
      expect(amounts[2]).toBe('2')
    })

    test('metric amounts show tooltip with original', async () => {
      const w = mountRecipe(imperialRecipe)
      await w.findAll('.unit-toggle button')[1].trigger('click')
      const amountEls = w.findAll('.amount')
      expect(amountEls[0].attributes('title')).toContain('original: 1 cup')
    })

    test('direction annotation brackets show metric amount', async () => {
      const w = mountRecipe(imperialRecipe)
      await w.findAll('.unit-toggle button')[1].trigger('click')
      const brackets = w.findAll('.bracket').map((el) => el.text())
      expect(brackets[0]).toContain('237 mL')
      expect(brackets[1]).toContain('4.9 mL')
    })

    test('°F in directions converts to °C with original shown', async () => {
      const w = mountRecipe(imperialRecipe)
      await w.findAll('.unit-toggle button')[1].trigger('click')
      const dirText = w.find('ol').text()
      expect(dirText).toContain('175°C')
      expect(dirText).toContain('original: 350°F')  // original shown in conversion note
    })

    test('metric recipe in imperial mode converts to imperial', async () => {
      const w = mountRecipe(metricRecipe)
      // Default is already imperial → metric recipe should be converted
      const amounts = w.findAll('.amount').map((el) => el.text())
      // 500g → gToImperial: ≥362.87 → lb → 500/453.592=1.102 → round(8.82)/8=9/8=1.125 → "1 ⅛ lb"
      expect(amounts[0]).toContain('lb')
      // 300ml → cup → 300/236.588=1.268 → round(10.14)/8=10/8=1.25 → "1 ¼ cup"
      expect(amounts[1]).toContain('cup')
    })

    test('°C in directions converts to °F in imperial mode', () => {
      const w = mountRecipe(metricRecipe)
      // Default is imperial
      // 220°C → 220*9/5+32 = 428 → round(428/5)*5 = round(85.6)*5 = 86*5 = 430°F
      expect(w.find('ol').text()).toContain('430°F')
    })
  })

  describe('direction sections', () => {
    test('renders section headings as h4', () => {
      const w = mountRecipe(multisectionRecipe)
      const headings = w.findAll('.direction-heading').map((el) => el.text())
      expect(headings).toContain('Make the dough')
      expect(headings).toContain('Make the filling')
    })

    test('no heading element when heading is empty', () => {
      const w = mountRecipe(imperialRecipe)
      expect(w.findAll('.direction-heading')).toHaveLength(0)
    })

    test('step numbers continue across sections', () => {
      const w = mountRecipe(multisectionRecipe)
      const lists = w.findAll('ol')
      // First section starts at 1 (default, no start attribute needed)
      // Second section should start at 3 (after 2 steps in first section)
      expect(lists[1].attributes('start')).toBe('3')
    })
  })

  describe('scaling', () => {
    test('scale factor adjusts all amounts proportionally', async () => {
      const w = mountRecipe(imperialRecipe)
      // Move slider for butter (id=0) to 2 cups (2× scale)
      const sliders = w.findAll('input[type="range"]')
      await sliders[0].setValue(2)
      await sliders[0].trigger('input')

      const amounts = w.findAll('.amount').map((el) => el.text())
      expect(amounts[0]).toBe('2 cup')  // butter: 1 × 2 = 2
      expect(amounts[1]).toBe('2 tsp')  // salt: 1 × 2 = 2
      expect(amounts[2]).toBe('4')      // eggs: 2 × 2 = 4
    })

    test('scaling and metric conversion work together', async () => {
      const w = mountRecipe(imperialRecipe)
      // Scale to 2× first
      const sliders = w.findAll('input[type="range"]')
      await sliders[0].setValue(2)
      await sliders[0].trigger('input')
      // Then switch to metric
      await w.findAll('.unit-toggle button')[1].trigger('click')

      const amounts = w.findAll('.amount').map((el) => el.text())
      // 2 cups × 236.588 = 473.176 → 473 mL
      expect(amounts[0]).toBe('473 mL')
    })
  })

  describe('clipboard copy', () => {
    beforeEach(() => {
      vi.stubGlobal('navigator', {
        clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
      })
    })

    test('copy button triggers clipboard write', async () => {
      const w = mountRecipe(imperialRecipe)
      await w.find('.copy-btn').trigger('click')
      expect(navigator.clipboard.writeText).toHaveBeenCalled()
    })

    test('clipboard text includes recipe title', async () => {
      const w = mountRecipe(imperialRecipe)
      await w.find('.copy-btn').trigger('click')
      const text = navigator.clipboard.writeText.mock.calls[0][0]
      expect(text).toContain('Chocolate Chip Cookies')
    })

    test('clipboard text includes INGREDIENTS and DIRECTIONS headers', async () => {
      const w = mountRecipe(imperialRecipe)
      await w.find('.copy-btn').trigger('click')
      const text = navigator.clipboard.writeText.mock.calls[0][0]
      expect(text).toContain('INGREDIENTS')
      expect(text).toContain('DIRECTIONS')
    })

    test('clipboard text includes ingredient amounts in current unit system', async () => {
      const w = mountRecipe(imperialRecipe)
      await w.find('.copy-btn').trigger('click')
      const imperialText = navigator.clipboard.writeText.mock.calls[0][0]
      expect(imperialText).toContain('1 cup')

      // Switch to metric and copy again
      await w.findAll('.unit-toggle button')[1].trigger('click')
      await w.find('.copy-btn').trigger('click')
      const metricText = navigator.clipboard.writeText.mock.calls[1][0]
      expect(metricText).toContain('237 mL')
      expect(metricText).toContain('(original: 1 cup)')
    })

    test('clipboard text includes temperature in current unit system', async () => {
      const w = mountRecipe(imperialRecipe)
      await w.findAll('.unit-toggle button')[1].trigger('click')  // switch to metric
      await w.find('.copy-btn').trigger('click')
      const text = navigator.clipboard.writeText.mock.calls[0][0]
      expect(text).toContain('175°C')
      expect(text).toContain('original: 350°F')
    })

    test('clipboard text includes section headings', async () => {
      const w = mountRecipe(multisectionRecipe)
      await w.find('.copy-btn').trigger('click')
      const text = navigator.clipboard.writeText.mock.calls[0][0]
      expect(text).toContain('Make the dough')
      expect(text).toContain('Make the filling')
    })

    test('copy button label changes to Copied! then resets', async () => {
      vi.useFakeTimers()
      const w = mountRecipe(imperialRecipe)
      await w.find('.copy-btn').trigger('click')
      expect(w.find('.copy-btn').text()).toBe('Copied!')
      vi.advanceTimersByTime(2100)
      await w.vm.$nextTick()
      expect(w.find('.copy-btn').text()).toBe('Copy')
      vi.useRealTimers()
    })
  })
})
