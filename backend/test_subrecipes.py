"""
Tests for the subrecipe (ingredient group) pipeline.
Uses a fake scraper to avoid any network requests.
"""
import pytest
from ingredient_parser import parse_ingredient
from annotator import annotate_directions


def make_groups(group_data):
    """
    Helper: simulate what scraper.ingredient_groups() returns.
    group_data is a list of (purpose, [ingredient strings]).
    """
    class FakeGroup:
        def __init__(self, purpose, ingredients):
            self.purpose = purpose
            self.ingredients = ingredients

    return [FakeGroup(purpose, ings) for purpose, ings in group_data]


def build_subrecipes(groups):
    """Mirror the logic in main.py for building subrecipes from groups."""
    all_ingredients = []
    subrecipes = []
    idx = 0

    for group in groups:
        group_ingredients = [
            parse_ingredient(raw, i + idx) for i, raw in enumerate(group.ingredients)
        ]
        idx += len(group_ingredients)
        all_ingredients.extend(group_ingredients)
        subrecipes.append({
            "name": group.purpose or "",
            "ingredients": group_ingredients,
        })

    return subrecipes, all_ingredients


class TestSubrecipeBuilding:
    def test_single_unnamed_group_has_empty_name(self):
        groups = make_groups([(None, ["2 cups flour", "1 egg"])])
        subrecipes, _ = build_subrecipes(groups)
        assert len(subrecipes) == 1
        assert subrecipes[0]["name"] == ""

    def test_multiple_named_groups(self):
        groups = make_groups([
            ("Dough", ["2 cups flour", "1/2 tsp salt"]),
            ("Filling", ["1/3 cup brown sugar", "1 tbsp cinnamon"]),
            ("Icing", ["4 oz cream cheese", "2/3 cup confectioners sugar"]),
        ])
        subrecipes, all_ingredients = build_subrecipes(groups)

        assert len(subrecipes) == 3
        assert subrecipes[0]["name"] == "Dough"
        assert subrecipes[1]["name"] == "Filling"
        assert subrecipes[2]["name"] == "Icing"

    def test_ingredient_ids_are_globally_unique(self):
        groups = make_groups([
            ("Dough", ["2 cups flour", "1 egg"]),
            ("Filling", ["1/3 cup sugar", "1 tbsp cinnamon"]),
        ])
        _, all_ingredients = build_subrecipes(groups)

        ids = [ing["id"] for ing in all_ingredients]
        assert ids == sorted(ids, key=int)
        assert len(ids) == len(set(ids))  # all unique

    def test_ingredient_counts_per_group(self):
        groups = make_groups([
            ("Dough", ["2 cups flour", "1/2 tsp salt", "1 egg"]),
            ("Filling", ["3 tbsp butter"]),
        ])
        subrecipes, all_ingredients = build_subrecipes(groups)

        assert len(subrecipes[0]["ingredients"]) == 3
        assert len(subrecipes[1]["ingredients"]) == 1
        assert len(all_ingredients) == 4


class TestDirectionsReferenceAcrossGroups:
    def test_directions_annotate_ingredients_from_all_groups(self):
        groups = make_groups([
            ("Dough", ["2 cups flour", "1/2 tsp salt"]),
            ("Filling", ["1/3 cup brown sugar", "1 tbsp cinnamon"]),
        ])
        subrecipes, all_ingredients = build_subrecipes(groups)

        directions = ["Mix the flour and salt, then add the brown sugar and cinnamon."]
        result = annotate_directions(directions, all_ingredients)

        ref_ids = {s["ingredient_id"] for s in result[0]["segments"] if s["type"] == "ref"}
        # Should have found ingredients from both groups
        assert len(ref_ids) >= 3

    def test_direction_refs_resolve_to_correct_group(self):
        groups = make_groups([
            ("Dough", ["2 cups flour"]),
            ("Filling", ["1/3 cup brown sugar"]),
        ])
        subrecipes, all_ingredients = build_subrecipes(groups)

        dough_flour_id = subrecipes[0]["ingredients"][0]["id"]
        filling_sugar_id = subrecipes[1]["ingredients"][0]["id"]

        directions = ["Combine the flour and brown sugar."]
        result = annotate_directions(directions, all_ingredients)

        ref_ids = {s["ingredient_id"] for s in result[0]["segments"] if s["type"] == "ref"}
        assert dough_flour_id in ref_ids
        assert filling_sugar_id in ref_ids
