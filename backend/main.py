from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any
import json
import httpx
from recipe_scrapers import scrape_html

from ingredient_parser import parse_ingredient
from annotator import annotate_directions

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


class ScrapeRequest(BaseModel):
    url: str


class ParseJsonLdRequest(BaseModel):
    jsonld: Any  # accepts a JSON string or a pre-parsed object/array


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

    try:
        raw_directions = scraper.instructions_list()
    except Exception:
        try:
            raw_directions = [scraper.instructions()]
        except Exception:
            raw_directions = []

    directions = annotate_directions(raw_directions, all_ingredients)

    return {"title": title, "subrecipes": subrecipes, "directions": directions}


@app.post("/api/scrape")
async def scrape(req: ScrapeRequest):
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
        scraper = scrape_html(response.text, org_url=req.url)
    except Exception as e:
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


def flatten_instructions(instructions):
    """Normalize recipeInstructions into a flat list of strings."""
    if isinstance(instructions, str):
        return [s.strip() for s in instructions.split("\n") if s.strip()]
    steps = []
    for item in instructions if isinstance(instructions, list) else []:
        if isinstance(item, str):
            steps.append(item.strip())
        elif isinstance(item, dict):
            if item.get("text"):
                steps.append(str(item["text"]).strip())
            if item.get("itemListElement"):
                steps.extend(flatten_instructions(item["itemListElement"]))
    return [s for s in steps if s]


@app.post("/api/parse-jsonld")
async def parse_jsonld(req: ParseJsonLdRequest):
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

    raw_directions = flatten_instructions(recipe.get("recipeInstructions", []))

    all_ingredients = [parse_ingredient(raw, i) for i, raw in enumerate(raw_ingredients)]
    subrecipes = [{"name": "", "ingredients": all_ingredients}]
    directions = annotate_directions(raw_directions, all_ingredients)

    return {"title": title, "subrecipes": subrecipes, "directions": directions}
