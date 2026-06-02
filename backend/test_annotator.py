import pytest
from annotator import annotate_directions, build_pattern


def make_ingredient(id, item, amount=1.0, unit=""):
    return {"id": str(id), "original": item, "amount": amount, "unit": unit, "item": item}


def text_segments(step):
    return [s["content"] for s in step["segments"] if s["type"] == "text"]


def ref_segments(step):
    return [s for s in step["segments"] if s["type"] == "ref"]


class TestBuildPattern:
    def test_matches_exact(self):
        pat = build_pattern("flour")
        assert pat.search("add the flour now")

    def test_case_insensitive(self):
        pat = build_pattern("flour")
        assert pat.search("Add the Flour")

    def test_plural_matches_singular(self):
        pat = build_pattern("eggs")
        assert pat.search("add one egg")

    def test_singular_matches_plural(self):
        pat = build_pattern("egg")
        assert pat.search("add the eggs")

    def test_no_partial_word_match(self):
        # "butter" should not match "buttermilk"
        pat = build_pattern("butter")
        assert not pat.search("add buttermilk")

    def test_ies_plural(self):
        pat = build_pattern("berries")
        assert pat.search("fold in the berry")

    def test_short_item_returns_none(self):
        assert build_pattern("") is None
        assert build_pattern("x") is None


class TestAnnotateDirections:
    def test_single_ingredient_match(self):
        ingredients = [make_ingredient(0, "eggs")]
        directions = ["Beat the eggs until fluffy."]
        result = annotate_directions(directions, ingredients)

        refs = ref_segments(result[0])
        assert len(refs) == 1
        assert refs[0]["ingredient_id"] == "0"
        assert refs[0]["matched_text"].lower() == "eggs"

    def test_plain_text_preserved(self):
        ingredients = [make_ingredient(0, "eggs")]
        directions = ["Preheat the oven to 350F."]
        result = annotate_directions(directions, ingredients)

        assert result[0]["segments"] == [{"type": "text", "content": "Preheat the oven to 350F."}]

    def test_multiple_ingredients_in_one_step(self):
        ingredients = [
            make_ingredient(0, "flour"),
            make_ingredient(1, "sugar"),
        ]
        directions = ["Mix flour and sugar together."]
        result = annotate_directions(directions, ingredients)

        ids = {s["ingredient_id"] for s in ref_segments(result[0])}
        assert "0" in ids
        assert "1" in ids

    def test_multiple_steps(self):
        ingredients = [make_ingredient(0, "butter")]
        directions = ["Melt the butter.", "Pour into pan."]
        result = annotate_directions(directions, ingredients)

        assert len(result) == 2
        assert len(ref_segments(result[0])) == 1
        assert len(ref_segments(result[1])) == 0

    def test_singular_ingredient_matches_plural_in_text(self):
        ingredients = [make_ingredient(0, "egg")]
        directions = ["Whisk the eggs."]
        result = annotate_directions(directions, ingredients)

        refs = ref_segments(result[0])
        assert len(refs) == 1
        assert refs[0]["ingredient_id"] == "0"

    def test_no_spurious_matches(self):
        # "butter" ingredient should not match "buttermilk" in text
        ingredients = [make_ingredient(0, "butter")]
        directions = ["Add the buttermilk and stir."]
        result = annotate_directions(directions, ingredients)

        assert len(ref_segments(result[0])) == 0

    def test_multiword_item_matches_last_word(self):
        # "all-purpose flour" should match "flour" in directions
        ingredients = [make_ingredient(0, "all-purpose flour")]
        directions = ["Whisk the flour until smooth."]
        result = annotate_directions(directions, ingredients)

        refs = ref_segments(result[0])
        assert len(refs) == 1
        assert refs[0]["ingredient_id"] == "0"

    def test_multiword_item_matches_full_phrase_preferentially(self):
        # When the full phrase appears, it should match (not just the last word)
        ingredients = [make_ingredient(0, "all-purpose flour")]
        directions = ["Use all-purpose flour for best results."]
        result = annotate_directions(directions, ingredients)

        refs = ref_segments(result[0])
        assert len(refs) == 1
        assert "all-purpose flour" in refs[0]["matched_text"].lower()

    def test_ingredient_annotated_only_once_per_step(self):
        ingredients = [make_ingredient(0, "flour")]
        directions = ["Add flour, then stir in more flour."]
        result = annotate_directions(directions, ingredients)

        refs = ref_segments(result[0])
        assert len(refs) == 1
        assert refs[0]["matched_text"].lower() == "flour"

    def test_duplicate_named_ingredients_annotated_only_once(self):
        # Recipes with multiple "butter" entries (dough, filling, icing) should
        # only annotate the word "butter" once per step.
        ingredients = [
            make_ingredient(0, "butter"),
            make_ingredient(1, "butter"),
            make_ingredient(2, "butter"),
        ]
        directions = ["Melt the butter until the butter is smooth."]
        result = annotate_directions(directions, ingredients)

        refs = ref_segments(result[0])
        assert len(refs) == 1

    def test_segments_reconstruct_original_text(self):
        ingredients = [make_ingredient(0, "flour")]
        directions = ["Sift the flour carefully."]
        result = annotate_directions(directions, ingredients)

        reconstructed = "".join(
            s.get("content") or s.get("matched_text", "")
            for s in result[0]["segments"]
        )
        assert reconstructed == "Sift the flour carefully."
