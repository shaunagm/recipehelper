from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any
import json
import os
import httpx
from recipe_scrapers import scrape_html
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ingredient_parser import parse_ingredient
from annotator import annotate_directions

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# In production, set ALLOWED_ORIGINS to your GitHub Pages URL, e.g.:
# https://yourusername.github.io
# In development, leave unset to allow all origins.
_raw = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = ["*"] if _raw == "*" else [o.strip() for o in _raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["POST"],
    allow_headers=["*"],
)


class ScrapeRequest(BaseModel):
    url: str


class ParseJsonLdRequest(BaseModel):
    jsonld: Any  # accepts a JSON string or a pre-parsed object/array


_IMPERATIVE_COOKING_VERBS = frozenset({
    "add", "bake", "beat", "blend", "boil", "bring", "brush",
    "chill", "chop", "coat", "combine", "cook", "cool", "cover", "cream",
    "cut", "dice", "dissolve", "divide", "drain", "drizzle", "drop",
    "fill", "fold", "freeze", "fry", "garnish", "grease",
    "heat", "knead", "layer", "let", "line", "melt", "mix", "place",
    "pour", "preheat", "prepare", "press", "proof", "put", "refrigerate",
    "remove", "repeat", "rest", "roll", "roast", "saute", "sauté", "season",
    "serve", "set", "shape", "sift", "slice", "spread", "sprinkle", "stir",
    "store", "strain", "taste", "top", "transfer", "trim", "turn",
    "wash", "whisk",
})


def is_heading(text: str) -> bool:
    """Return True if a direction step looks like a section heading rather than an instruction."""
    text = text.strip()
    if not text:
        return False
    # Rule 1: ends with colon and is short — e.g. "For the filling:"
    if text.endswith(":") and len(text) <= 80 and len(text.split()) <= 8:
        return True
    # Rule 2: short title-like phrase — no sentence-ending punctuation, no digits,
    # and doesn't open with an imperative cooking verb.
    # e.g. "Making the Chocolate Fudge Cake" or "Chocolate Ganache"
    words = text.split()
    if (1 <= len(words) <= 5
            and text[-1] not in ".!?:"
            and not any(c.isdigit() for c in text)
            and words[0].lower() not in _IMPERATIVE_COOKING_VERBS):
        return True
    return False


def flat_list_to_sections(steps: list) -> list:
    """
    Split a flat list of step strings into sections using heuristic heading detection.
    Returns: [{"heading": str, "steps": [str]}]
    """
    sections = [{"heading": "", "steps": []}]
    for step in steps:
        if is_heading(step):
            sections.append({"heading": step.rstrip(":").strip(), "steps": []})
        else:
            sections[-1]["steps"].append(step)
    return [s for s in sections if s["steps"]]


def parse_instructions_to_sections(instructions) -> list:
    """
    Parse JSON-LD recipeInstructions into sections, preserving HowToSection structure
    when present. Falls back to flat_list_to_sections for unstructured lists.
    Returns: [{"heading": str, "steps": [str]}]
    """
    if isinstance(instructions, str):
        steps = [s.strip() for s in instructions.split("\n") if s.strip()]
        return flat_list_to_sections(steps)

    if not isinstance(instructions, list):
        return [{"heading": "", "steps": []}]

    has_sections = any(
        isinstance(item, dict) and "HowToSection" in str(item.get("@type", ""))
        for item in instructions
    )

    if has_sections:
        sections = [{"heading": "", "steps": []}]
        for item in instructions:
            if isinstance(item, str):
                sections[-1]["steps"].append(item.strip())
            elif isinstance(item, dict):
                if "HowToSection" in str(item.get("@type", "")):
                    heading = str(item.get("name", "")).strip()
                    sub_steps = []
                    for sub in (item.get("itemListElement") or []):
                        if isinstance(sub, str):
                            sub_steps.append(sub.strip())
                        elif isinstance(sub, dict) and sub.get("text"):
                            sub_steps.append(str(sub["text"]).strip())
                    if sub_steps:
                        sections.append({"heading": heading, "steps": sub_steps})
                elif item.get("text"):
                    sections[-1]["steps"].append(str(item["text"]).strip())
        return [s for s in sections if s["steps"]]

    # Flat list — extract text then apply heuristic
    steps = []
    for item in instructions:
        if isinstance(item, str):
            steps.append(item.strip())
        elif isinstance(item, dict):
            if item.get("text"):
                steps.append(str(item["text"]).strip())
            if item.get("itemListElement"):
                for sub in item["itemListElement"]:
                    if isinstance(sub, str):
                        steps.append(sub.strip())
                    elif isinstance(sub, dict) and sub.get("text"):
                        steps.append(str(sub["text"]).strip())
    return flat_list_to_sections([s for s in steps if s])


def annotate_sections(instruction_sections: list, all_ingredients: list) -> list:
    """Annotate each section's steps and return direction_sections."""
    result = []
    for section in instruction_sections:
        result.append({
            "heading": section["heading"],
            "steps": annotate_directions(section["steps"], all_ingredients),
        })
    return result


def build_recipe_response(scraper) -> dict:
    """Shared logic: extract + parse a recipe from a recipe-scrapers scraper object."""
    try:
        title = scraper.title()
    except Exception:
        title = "Untitled Recipe"

    all_ingredients = []
    subrecipes = []
    idx = 0

    try:
        groups = scraper.ingredient_groups()
    except Exception:
        groups = None

    if groups:
        for group in groups:
            group_ingredients = [parse_ingredient(raw, i + idx) for i, raw in enumerate(group.ingredients)]
            idx += len(group_ingredients)
            all_ingredients.extend(group_ingredients)
            subrecipes.append({
                "name": group.purpose or "",
                "ingredients": group_ingredients,
            })
    else:
        try:
            raw_ingredients = scraper.ingredients()
        except Exception:
            raw_ingredients = []
        all_ingredients = [parse_ingredient(raw, i) for i, raw in enumerate(raw_ingredients)]
        subrecipes = [{"name": "", "ingredients": all_ingredients}]

    # Prefer raw JSON-LD schema to preserve HowToSection structure.
    # schema.data is a property in some versions and a method in others.
    instruction_sections = None
    try:
        d = scraper.schema.data
        schema_data = d() if callable(d) else d
        raw_instructions = schema_data.get("recipeInstructions") if isinstance(schema_data, dict) else None
        if raw_instructions:
            instruction_sections = parse_instructions_to_sections(raw_instructions)
    except Exception:
        pass

    if not instruction_sections:
        try:
            raw_steps = scraper.instructions_list()
        except Exception:
            try:
                raw_steps = [scraper.instructions()]
            except Exception:
                raw_steps = []
        instruction_sections = flat_list_to_sections(raw_steps)

    direction_sections = annotate_sections(instruction_sections, all_ingredients)

    return {"title": title, "subrecipes": subrecipes, "direction_sections": direction_sections}


@app.post("/api/scrape")
@limiter.limit("10/minute")
async def scrape(request: Request, req: ScrapeRequest):
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                )
            },
        ) as client:
            response = await client.get(req.url)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Recipe site returned {e.response.status_code}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Could not reach {req.url}: {e}")

    try:
        scraper = scrape_html(response.text, org_url=req.url, wild_mode=True)
    except Exception as e:
        msg = str(e)
        if "No Recipe Schema" in msg or "SchemaOrg" in msg or "schema" in msg.lower():
            raise HTTPException(
                status_code=422,
                detail="No recipe data found on this page. The site may not use standard recipe markup (schema.org/Recipe).",
            )
        raise HTTPException(status_code=422, detail=f"Could not parse recipe: {e}")

    return build_recipe_response(scraper)


def find_recipe_object(data):
    """Recursively search JSON-LD data for an object with @type Recipe."""
    if isinstance(data, list):
        for item in data:
            result = find_recipe_object(item)
            if result:
                return result
        return None
    if not isinstance(data, dict):
        return None
    types = data.get("@type", "")
    if isinstance(types, str):
        types = [types]
    if "Recipe" in types:
        return data
    if "@graph" in data:
        return find_recipe_object(data["@graph"])
    return None


@app.post("/api/parse-jsonld")
@limiter.limit("10/minute")
async def parse_jsonld(request: Request, req: ParseJsonLdRequest):
    # Accept either a raw JSON string or a pre-parsed object/array
    if isinstance(req.jsonld, str):
        try:
            data = json.loads(req.jsonld)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=422, detail=f"Invalid JSON: {e}")
    else:
        data = req.jsonld

    recipe = find_recipe_object(data)
    if not recipe:
        raise HTTPException(status_code=422, detail="No Recipe object found in the provided JSON-LD")

    title = recipe.get("name") or "Untitled Recipe"

    raw_ingredients = recipe.get("recipeIngredient", [])
    if isinstance(raw_ingredients, str):
        raw_ingredients = [raw_ingredients]

    all_ingredients = [parse_ingredient(raw, i) for i, raw in enumerate(raw_ingredients)]
    subrecipes = [{"name": "", "ingredients": all_ingredients}]

    instruction_sections = parse_instructions_to_sections(recipe.get("recipeInstructions", []))
    direction_sections = annotate_sections(instruction_sections, all_ingredients)

    return {"title": title, "subrecipes": subrecipes, "direction_sections": direction_sections}
