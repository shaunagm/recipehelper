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

    # Seed with full item and, for multi-word items, the last word
    words = item.split()
    seeds = {item}
    if len(words) > 1 and len(words[-1]) >= 2:
        seeds.add(words[-1])

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
    Iteratively finds the earliest match across all ingredient patterns
    and splits the text into segments. Each ingredient is annotated at
    most once per step.
    """
    segments = []
    remaining = text
    annotated_ids = set()

    while remaining:
        best_match = None
        best_id = None
        best_start = len(remaining)

        for ing_id, pat in patterns:
            if ing_id in annotated_ids:
                continue
            m = pat.search(remaining)
            if m and m.start() < best_start:
                best_match = m
                best_id = ing_id
                best_start = m.start()

        if best_match is None:
            segments.append({"type": "text", "content": remaining})
            break

        if best_match.start() > 0:
            segments.append({"type": "text", "content": remaining[:best_match.start()]})

        matched_text = best_match.group(0)
        segments.append({
            "type": "ref",
            "ingredient_id": best_id,
            "matched_text": matched_text,
        })

        # Mark all ingredients whose pattern matches this same word as used,
        # so duplicate-named ingredients (e.g. three "butter" entries) don't
        # re-annotate later occurrences of the same word in this step.
        for other_id, other_pat in patterns:
            if other_pat.search(matched_text):
                annotated_ids.add(other_id)

        remaining = remaining[best_match.end():]

    return segments
