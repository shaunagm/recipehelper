"""Tests for direction section parsing (is_heading, flat_list_to_sections, parse_instructions_to_sections)."""
import pytest
from main import is_heading, flat_list_to_sections, parse_instructions_to_sections


class TestIsHeading:
    def test_colon_suffix(self):
        assert is_heading("For the filling:") is True

    def test_colon_suffix_long_rejected(self):
        assert is_heading("This is a very long heading that goes on and on and on and on:") is False

    def test_gerund_phrase_no_colon(self):
        assert is_heading("Making the Chocolate Fudge Cake") is True

    def test_noun_phrase_two_words(self):
        assert is_heading("Chocolate Ganache") is True

    def test_imperative_verb_rejected(self):
        assert is_heading("Preheat oven to 350°F") is False

    def test_mix_well_rejected(self):
        assert is_heading("Mix well") is False

    def test_stir_until_rejected(self):
        assert is_heading("Stir until combined") is False

    def test_ends_with_period_rejected(self):
        assert is_heading("Bake until golden.") is False

    def test_has_digit_rejected(self):
        assert is_heading("Step 2 batter") is False

    def test_too_many_words_rejected(self):
        # 6 words with no imperative verb — exceeds the 5-word limit for rule 2
        assert is_heading("The mixture should be very thick") is False

    def test_empty_rejected(self):
        assert is_heading("") is False

    def test_for_the_filling_no_colon(self):
        assert is_heading("For the Filling") is True


class TestFlatListToSections:
    def test_no_headings(self):
        steps = ["Mix flour.", "Add eggs."]
        sections = flat_list_to_sections(steps)
        assert len(sections) == 1
        assert sections[0]["heading"] == ""
        assert sections[0]["steps"] == ["Mix flour.", "Add eggs."]

    def test_colon_heading_splits(self):
        steps = ["For the dough:", "Mix flour.", "Add eggs.", "For the filling:", "Add sugar."]
        sections = flat_list_to_sections(steps)
        assert len(sections) == 2
        assert sections[0]["heading"] == "For the dough"
        assert sections[0]["steps"] == ["Mix flour.", "Add eggs."]
        assert sections[1]["heading"] == "For the filling"
        assert sections[1]["steps"] == ["Add sugar."]

    def test_title_phrase_heading(self):
        steps = ["Making the Chocolate Fudge Cake", "Prepare the pan.", "Bake for 30 minutes."]
        sections = flat_list_to_sections(steps)
        assert len(sections) == 1
        assert sections[0]["heading"] == "Making the Chocolate Fudge Cake"
        assert sections[0]["steps"] == ["Prepare the pan.", "Bake for 30 minutes."]


class TestParseInstructionsToSections:
    def test_howto_section_objects(self):
        instructions = [
            {
                "@type": "HowToSection",
                "name": "Making the Cake",
                "itemListElement": [
                    {"@type": "HowToStep", "text": "Mix flour and sugar."},
                    {"@type": "HowToStep", "text": "Bake for 30 minutes."},
                ],
            }
        ]
        sections = parse_instructions_to_sections(instructions)
        assert len(sections) == 1
        assert sections[0]["heading"] == "Making the Cake"
        assert "Mix flour and sugar." in sections[0]["steps"]

    def test_flat_howto_steps(self):
        instructions = [
            {"@type": "HowToStep", "text": "Mix flour."},
            {"@type": "HowToStep", "text": "Add eggs."},
        ]
        sections = parse_instructions_to_sections(instructions)
        assert len(sections) == 1
        assert len(sections[0]["steps"]) == 2
