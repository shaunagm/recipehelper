import re


def build_pattern(item: str) -> re.Pattern | None:
    """
    Builds a case-insensitive regex that matches the ingredient item name
    and common singular/plural variants as a whole word.
    For multi-word items (e.g. "all-purpose flour"), also matches the last
    word ("flour") so that shorthand references in directions are caught.
    """
    if not item or len(item) < 2:
        return None

    item = item.strip().lower()

    # Words too generic to use as a first-word seed — they appear constantly
    # in cooking directions independent of any specific ingredient.
    _GENERIC_FIRST_WORDS = {
        "baking", "cooking", "ground", "fresh", "dried", "frozen",
        "heavy", "light", "dark", "extra", "raw", "cooked", "all",
        "half", "whole", "large", "small", "medium",
    }

    # Words too generic to use as a last-word seed — common kitchen tool/vessel
    # terms that appear in directions regardless of any specific ingredient.
    _GENERIC_LAST_WORDS = {
        "sheet", "pan", "dish", "bowl", "pot", "rack", "tray", "tin",
        "skillet", "mold", "mould", "foil", "paper",
    }

    # Seed with full item; for multi-word items also try first and last word
    # so "vanilla extract" matches "vanilla" and "all-purpose flour" matches "flour"
    words = item.split()
    seeds = {item}
    if len(words) > 1:
        if len(words[-1]) >= 2 and words[-1] not in _GENERIC_LAST_WORDS:
            seeds.add(words[-1])
        if len(words[0]) >= 3 and words[0] not in _GENERIC_FIRST_WORDS:
            seeds.add(words[0])

    variants = set()
    for seed in seeds:
        variants.add(seed)
        if seed.endswith("ies"):
            variants.add(seed[:-3] + "y")      # berries → berry
        elif seed.endswith("ves"):
            variants.add(seed[:-3] + "f")      # leaves → leaf
            variants.add(seed[:-3] + "fe")
        elif seed.endswith("es") and len(seed) > 4:
            variants.add(seed[:-2])             # tomatoes → tomato
        elif seed.endswith("s") and len(seed) > 3:
            variants.add(seed[:-1])             # eggs → egg

    # Also add plurals of any singular forms
    for v in list(variants):
        if not v.endswith("s"):
            variants.add(v + "s")

    # Sort longest first so more-specific variants match preferentially
    pattern_str = "|".join(re.escape(v) for v in sorted(variants, key=len, reverse=True))
    return re.compile(rf"\b({pattern_str})\b", re.IGNORECASE)


def annotate_directions(directions: list[str], ingredients: list[dict]) -> list[dict]:
    """
    For each direction step, split the text into typed segments:
      { "type": "text", "content": "..." }
      { "type": "ref", "ingredient_id": "0", "matched_text": "eggs" }
    """
    # Pre-build patterns; skip ingredients with no parseable item
    patterns = []
    for ing in ingredients:
        item = ing.get("item", "")
        pat = build_pattern(item)
        if pat:
            patterns.append((ing["id"], pat))

    result = []
    for step in directions:
        segments = _split_step(step, patterns)
        result.append({"segments": segments})
    return result


def _split_step(text: str, patterns: list) -> list[dict]:
    """
    Iteratively finds the earliest (and longest, on ties) match across all
    ingredient patterns, splits the text into segments, and ensures each
    ingredient is annotated at most once per step.

    Deduplication works by position: when multiple ingredient patterns match
    at the same start position (e.g. three "butter" entries all matching the
    same word "butter"), all of them are blocked after the first annotation.
    Patterns that match at a DIFFERENT position (e.g. "sugar" at pos 20 vs
    "brown sugar" at pos 14) are NOT blocked by each other.
    """
    segments = []
    remaining = text
    annotated_ids = set()

    while remaining:
        # Collect all matches grouped by their start position
        matches_by_pos: dict[int, list] = {}
        for ing_id, pat in patterns:
            if ing_id in annotated_ids:
                continue
            m = pat.search(remaining)
            if m:
                matches_by_pos.setdefault(m.start(), []).append((ing_id, m))

        if not matches_by_pos:
            segments.append({"type": "text", "content": remaining})
            break

        # Pick the earliest position; among ties prefer the longest match
        best_start = min(matches_by_pos)
        competing = matches_by_pos[best_start]
        best_id, best_match = max(competing, key=lambda x: len(x[1].group(0)))

        if best_start > 0:
            segments.append({"type": "text", "content": remaining[:best_start]})

        matched_text = best_match.group(0)
        segments.append({
            "type": "ref",
            "ingredient_id": best_id,
            "matched_text": matched_text,
        })

        # Block all ids that competed at this exact position — they all refer
        # to the same occurrence of the word and shouldn't be matched again.
        for other_id, _ in competing:
            annotated_ids.add(other_id)

        remaining = remaining[best_start + len(matched_text):]

    return segments
