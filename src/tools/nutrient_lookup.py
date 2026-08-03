"""
Tool: look up nutrient/calorie info for a food via USDA FoodData Central.

Requires a free API key from https://fdc.nal.usda.gov/api-key-signup.html
Set it as the FDC_API_KEY environment variable.
"""
import os

import requests

FDC_API_KEY = os.environ.get("FDC_API_KEY", "DEMO_KEY")
SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

KEY_NUTRIENTS = {"Energy", "Protein", "Total lipid (fat)", "Carbohydrate, by difference", "Sodium, Na"}


def lookup_food(food_name: str) -> dict:
    """Return basic nutrient info for the best-matching food."""
    resp = requests.get(
        SEARCH_URL,
        params={"api_key": FDC_API_KEY, "query": food_name, "pageSize": 1},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    if not data.get("foods"):
        return {"error": f"No match found for '{food_name}'"}

    food = data["foods"][0]
    nutrients = {
        n["nutrientName"]: {"amount": n["value"], "unit": n["unitName"]}
        for n in food.get("foodNutrients", [])
        if n["nutrientName"] in KEY_NUTRIENTS
    }

    return {
        "food": food.get("description"),
        "fdc_id": food.get("fdcId"),
        "nutrients": nutrients,
    }


# --- Tool schema for agent registration (Anthropic tool-use format) ---
TOOL_SCHEMA = {
    "name": "nutrient_lookup",
    "description": (
        "Look up calorie and macronutrient info for a specific food item "
        "using the USDA FoodData Central database. Use for questions like "
        "'how many calories in X' or 'how much protein is in Y'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "food_name": {
                "type": "string",
                "description": "Name of the food to look up, e.g. 'banana' or 'grilled chicken breast'",
            }
        },
        "required": ["food_name"],
    },
}
