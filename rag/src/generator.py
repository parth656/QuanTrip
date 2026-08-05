import json
import re

from langchain_google_genai import ChatGoogleGenerativeAI


class Generator:

    def __init__(self, model_name: str, api_key: str):
        self.model = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0,
            google_api_key=api_key,
        )

    def generate(self, prompt: str) -> str:
        response = self.model.invoke(prompt)
        return response.content[0]["text"]

    def build_prompt(
        self,
        question: str,
        memory_context: str,
        rag_context: str,
    ) -> str:
        return f"""You are a smart travel itinerary planner. Your job is to create a clear, realistic, day-by-day travel itinerary using ONLY the places found in the Retrieved Context below. You must not invent places, prices, or facts that are not present in the Retrieved Context.

Conversation History:
{memory_context}

Retrieved Context (available places and their details):
{rag_context}

User's Trip Request:
{question}

Instructions:
1. Build the itinerary using ONLY places from the Retrieved Context. Never add places not listed there.
2. Match places to the user's chosen travel types. If multiple types are selected, include a good mix covering each.
3. Spread the plan across the exact number of days. Balance each day, group nearby places, keep a logical order.
4. Respect the budget level (economy / moderate / luxury) for places and food.
5. Keep the traveler count in mind (family / group / couple friendly) when the context provides it.
6. For each day give Morning / Afternoon / Evening with place, why it fits, ideal time, and any detail from context.
7. Suggest nearby food/restaurants from the context matching the budget.
8. If there are not enough places for all days, honestly say so in "notes" — do not invent places.

OUTPUT FORMAT:
Return ONLY valid JSON. No markdown, no commentary, nothing outside the JSON.

Use EXACTLY this structure:
{{
    "destination": "string",
    "days": 0,
    "budget": "string",
    "travelers": 0,
    "travel_types": ["string"],
    "summary": "short overview of the trip",
    "itinerary": [
        {{
            "day": 1,
            "title": "short title for the day",
            "morning": "place + why it fits + ideal time",
            "afternoon": "place + why it fits + ideal time",
            "evening": "place + why it fits + ideal time",
            "food": "food/restaurant suggestion matching the budget",
            "est_cost": "approximate cost note"
        }}
    ],
    "notes": "honest note if not enough places, else empty string",
    "sources": ["source file names from context if available"]
}}

Now generate the itinerary as JSON:"""

    # Safely turn the LLM's raw text into a Python dict
    @staticmethod
    def parse_output(raw: str) -> dict:
        text = (raw or "").strip()

        # Remove ```json ... ``` fences if the model added them
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
            text = re.sub(r"\s*```$", "", text).strip()

        # 1) Try to parse directly
        try:
            return json.loads(text)
        except Exception:
            pass

        # 2) Try to grab the first { ... } block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

        # 3) Fallback so nothing crashes
        return {
            "summary": "",
            "itinerary": [],
            "notes": raw,
            "sources": [],
        }