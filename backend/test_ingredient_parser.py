import pytest
from ingredient_parser import parse_ingredient, compute_original_tail


def p(raw):
    return parse_ingredient(raw, 0)


class TestAmountParsing:
    def test_integer(self):
        result = p("2 cups flour")
        assert result["amount"] == 2.0

    def test_decimal(self):
        result = p("1.5 cups milk")
        assert result["amount"] == 1.5

    def test_simple_fraction(self):
        result = p("1/2 teaspoon salt")
        assert result["amount"] == pytest.approx(0.5)

    def test_mixed_number(self):
        result = p("1 1/2 cups milk")
        assert result["amount"] == pytest.approx(1.5)

    def test_mixed_number_with_and(self):
        # "2 and 3/4 cups flour" is common in American recipes
        result = p("2 and 3/4 cups all-purpose flour")
        assert result["amount"] == pytest.approx(2.75)

    def test_unicode_half(self):
        result = p("½ teaspoon vanilla")
        assert result["amount"] == pytest.approx(0.5)

    def test_unicode_quarter(self):
        result = p("¼ cup sugar")
        assert result["amount"] == pytest.approx(0.25)

    def test_unicode_three_quarters(self):
        result = p("¾ cup whole milk")
        assert result["amount"] == pytest.approx(0.75)

    def test_no_amount(self):
        result = p("salt to taste")
        assert result["amount"] is None

    def test_word_half(self):
        result = p("half cup milk")
        assert result["amount"] == pytest.approx(0.5)
        assert result["unit"] == "cup"
        assert result["item"] == "milk"

    def test_word_a_pinch(self):
        result = p("a pinch of salt")
        assert result["amount"] == pytest.approx(1.0)

    def test_word_one(self):
        result = p("one cup sugar")
        assert result["amount"] == pytest.approx(1.0)

    def test_word_couple(self):
        result = p("couple tablespoons olive oil")
        assert result["amount"] == pytest.approx(2.0)

    def test_word_eighth(self):
        result = p("eighth teaspoon cayenne")
        assert result["amount"] == pytest.approx(0.125)


class TestUnitParsing:
    def test_cups(self):
        assert p("2 cups flour")["unit"] == "cups"

    def test_tablespoons(self):
        assert p("3 Tablespoons butter")["unit"] == "Tablespoons"

    def test_teaspoon(self):
        assert p("1/2 teaspoon salt")["unit"] == "teaspoon"

    def test_tablespoon_abbrev(self):
        assert p("1 tbsp olive oil")["unit"] == "tbsp"

    def test_ounces(self):
        assert p("4 ounces cream cheese")["unit"] == "ounces"

    def test_pounds(self):
        assert p("1 lb ground beef")["unit"] == "lb"

    def test_grams(self):
        assert p("100 g chocolate")["unit"] == "g"

    def test_no_unit(self):
        assert p("2 eggs")["unit"] == ""

    def test_no_unit_with_descriptor(self):
        assert p("1 large egg")["unit"] == ""


class TestItemParsing:
    def test_simple_item(self):
        assert p("2 cups flour")["item"] == "flour"

    def test_multiword_item(self):
        assert p("2 cups all-purpose flour")["item"] == "all-purpose flour"

    def test_strips_large_descriptor(self):
        assert p("1 large egg")["item"] == "egg"

    def test_strips_fresh_descriptor(self):
        assert p("2 tbsp fresh parsley")["item"] == "parsley"

    def test_strips_parenthetical(self):
        result = p("2 and 3/4 cups (344g) all-purpose flour")
        assert "344g" not in result["item"]
        assert "flour" in result["item"]

    def test_strips_trailing_comma_clause(self):
        result = p("2 and 3/4 cups (344g) all-purpose flour (spooned & leveled), plus more as needed")
        assert result["item"] == "all-purpose flour"

    def test_strips_to_taste(self):
        result = p("salt, to taste")
        assert result["item"] == "salt"

    def test_strips_divided(self):
        result = p("3 Tablespoons unsalted butter, divided")
        assert result["item"] == "unsalted butter"

    def test_no_amount_item(self):
        assert p("salt to taste")["item"] == "salt to taste"

    def test_original_preserved(self):
        raw = "2 and 3/4 cups (344g) all-purpose flour"
        assert p(raw)["original"] == raw

    def test_inline_size_descriptor_before_unit(self):
        # "1 (29 ounce) can" — the inline size should be skipped so "can" is the unit
        result = p("1 (29 ounce) can sliced peaches in heavy syrup, undrained")
        assert result["amount"] == pytest.approx(1.0)
        assert result["unit"] == "can"
        assert result["item"] == "peaches in heavy syrup"  # "sliced" stripped as leading descriptor

    def test_orphaned_closing_paren_stripped(self):
        # recipe-scrapers sometimes strips the "(" but leaves the ")" in the text
        result = p("1 cup self-rising flour, see Note for substitution)")
        assert result["item"] == "self-rising flour"
        assert ")" not in result["item"]

    def test_comma_before_paren_note(self):
        # e.g. "3/4 cup granulated sugar, (plus 2 additional Tablespoons for topping)"
        result = p("3/4 cup granulated sugar, (plus 2 additional Tablespoons for topping)")
        assert result["item"] == "granulated sugar"

    def test_divided_with_trailing_paren_note(self):
        # e.g. "1/2 cup butter, divided (and melted separately)"
        result = p("1/2 cup butter, divided (and melted separately)")
        assert result["item"] == "butter"


class TestComputeOriginalTail:
    def test_cup_with_note(self):
        assert compute_original_tail(
            "1 cup self-rising flour, (see Note for substitution)", "cup"
        ) == "self-rising flour, (see Note for substitution)"

    def test_unicode_fraction(self):
        assert compute_original_tail(
            "¾ cup granulated sugar, (plus 2 additional Tablespoons for topping)", "cup"
        ) == "granulated sugar, (plus 2 additional Tablespoons for topping)"

    def test_inline_paren_unit(self):
        assert compute_original_tail(
            "1 (29 ounce) can sliced peaches in heavy syrup, undrained", "can"
        ) == "sliced peaches in heavy syrup, undrained"

    def test_no_unit(self):
        assert compute_original_tail("2 eggs", "") == "eggs"

    def test_no_number(self):
        assert compute_original_tail("salt, to taste", "") == "salt, to taste"

    def test_divided_note_preserved(self):
        assert compute_original_tail(
            "1/2 cup butter, divided (and melted separately)", "cup"
        ) == "butter, divided (and melted separately)"

    def test_tail_stored_on_ingredient(self):
        result = parse_ingredient("1 cup self-rising flour, (see Note)", 0)
        assert result["tail"] == "self-rising flour, (see Note)"
