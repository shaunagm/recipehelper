import re

UNITS = {
    # volume
    "cup", "cups", "c",
    "tablespoon", "tablespoons", "tbsp", "tbs",
    "teaspoon", "teaspoons", "tsp",
    "fluid ounce", "fluid ounces", "fl oz",
    "pint", "pints", "pt",
    "quart", "quarts", "qt",
    "gallon", "gallons", "gal",
    "milliliter", "milliliters", "ml",
    "liter", "liters", "l",
    # weight
    "ounce", "ounces", "oz",
    "pound", "pounds", "lb", "lbs",
    "gram", "grams", "g",
    "kilogram", "kilograms", "kg",
    # count/misc
    "pinch", "pinches",
    "dash", "dashes",
    "handful", "handfuls",
    "slice", "slices",
    "piece", "pieces",
    "clove", "cloves",
    "sprig", "sprigs",
    "stalk", "stalks",
    "can", "cans",
    "package", "packages", "pkg",
    "bag", "bags",
    "jar", "jars",
    "bottle", "bottles",
}

# Matches: integer, decimal, fraction (1/2), mixed number (1 1/2 or "2 and 3/4")
NUMBER_RE = re.compile(
    r"""
    (?:
        \d+\s+and\s+\d+/\d+  # "2 and 3/4"
        | \d+\s+\d+/\d+       # mixed number: 1 1/2
        | \d+/\d+              # fraction: 1/2
        | \d+\.?\d*            # integer or decimal: 2, 2.5
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Unicode fraction map
UNICODE_FRACTIONS = {
    "\u00bc": "1/4",
    "\u00bd": "1/2",
    "\u00be": "3/4",
    "\u2153": "1/3",
    "\u2154": "2/3",
    "\u2155": "1/5",
    "\u2156": "2/5",
    "\u2157": "3/5",
    "\u2158": "4/5",
    "\u2159": "1/6",
    "\u215a": "5/6",
    "\u2150": "1/7",
    "\u215b": "1/8",
    "\u215c": "3/8",
    "\u215d": "5/8",
    "\u215e": "7/8",
}


WORD_AMOUNTS = {
    "a": "1",
    "an": "1",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "couple": "2",
    "half": "1/2",
    "quarter": "1/4",
    "eighth": "1/8",
}

WORD_AMOUNT_RE = re.compile(
    r"^(" + "|".join(WORD_AMOUNTS.keys()) + r")\b",
    re.IGNORECASE,
)


def normalize_unicode(text: str) -> str:
    for char, replacement in UNICODE_FRACTIONS.items():
        text = text.replace(char, " " + replacement)
    return text


def normalize_word_amounts(text: str) -> str:
    m = WORD_AMOUNT_RE.match(text)
    if m:
        word = m.group(1).lower()
        return WORD_AMOUNTS[word] + text[m.end():]
    return text


def fraction_to_float(s: str) -> float:
    s = s.strip()
    # Normalize "2 and 3/4" → "2 3/4"
    s = re.sub(r'\s+and\s+', ' ', s, flags=re.IGNORECASE)
    if "/" in s:
        parts = s.split()
        if len(parts) == 2:
            # mixed number: "1 1/2"
            whole, frac = parts
            num, den = frac.split("/")
            return float(whole) + float(num) / float(den)
        else:
            # plain fraction: "1/2"
            num, den = s.split("/")
            return float(num) / float(den)
    return float(s)


def parse_ingredient(raw: str, idx: int) -> dict:
    text = normalize_word_amounts(normalize_unicode(raw.strip()).strip())

    # Extract leading number(s)
    amount = None
    unit = ""
    item = text

    match = NUMBER_RE.match(text)
    if match:
        amount_str = match.group(0).strip()
        try:
            amount = fraction_to_float(amount_str)
        except Exception:
            amount = None
        remainder = text[match.end():].strip()

        # Check if next token is a known unit
        words = remainder.split()
        if words:
            # try two-word units first (e.g. "fluid ounce")
            if len(words) >= 2 and (words[0] + " " + words[1]).lower() in UNITS:
                unit = words[0] + " " + words[1]
                item = " ".join(words[2:])
            elif words[0].lower() in UNITS:
                unit = words[0]
                item = " ".join(words[1:])
            else:
                item = remainder
        else:
            item = remainder

    # Strip trailing parenthetical notes e.g. "(344g)"
    item_clean = re.sub(r"\s*\(.*?\)", "", item).strip()
    # Strip trailing comma clauses e.g. ", plus more as needed", ", to taste", ", divided"
    item_clean = item_clean.split(",")[0].strip()
    # Strip leading descriptors like "large", "small", "medium", "fresh", etc.
    item_clean = re.sub(
        r"^(large|small|medium|extra-large|extra large|fresh|dried|frozen|cooked|raw|whole|ground|minced|chopped|sliced|diced)\s+",
        "",
        item_clean,
        flags=re.IGNORECASE,
    )

    return {
        "id": str(idx),
        "original": raw.strip(),
        "amount": amount,
        "unit": unit,
        "item": item_clean or item,
    }
