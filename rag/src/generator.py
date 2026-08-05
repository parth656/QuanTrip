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
        content = response.content
        # Gemini may return a string OR a list of parts -> force a string
        if isinstance(content, list):
            return "".join(
                p["text"] if isinstance(p, dict) else str(p) for p in content
            )
        return content

    
    def parse_output(self, raw) -> dict:
        text = (raw or "").strip()

    
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
            text = re.sub(r"\s*```$", "", text).strip()

        try:
            return json.loads(text)
        except Exception:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass


        return {"summary": "", "itinerary": [], "notes": raw, "sources": []}

    def build_prompt(self, question: str, memory_context: str, rag_context: str) -> str:
        return f"""You are a smart travel itinerary planner. Create a realistic, day-by-day itinerary using ONLY the places in the Retrieved Context below. Do not invent places, prices, or facts not present in the Retrieved Context.

Conversation History:
{memory_context}

Retrieved Context (available places and details):
{rag_context}

User's Trip Request:
{question}

Instructions:
1. Use ONLY places from the Retrieved Context. Never add places not listed there.
2. Match places to the user's travel types. If multiple types, include a good mix.
3. Spread places across the exact number of days. Group nearby places logically.
4. Respect budget (economy/moderate/luxury) for places and food.
5. Do NOT repeat the same place on multiple days. If there are fewer places than days, reduce the number of days and explain honestly in "notes".
6. For each day give Morning / Afternoon / Evening with place, why it fits, best time, and a nearby food option from context.

OUTPUT FORMAT:
Return ONLY valid JSON, nothing else. Use EXACTLY this structure:
{{
  "destination": "string",
  "summary": "short trip overview",
  "itinerary": [
    {{
      "day": 1,
      "title": "short day title",
      "morning": "place + why + best time",
      "afternoon": "place + why + best time",
      "evening": "place + why + best time",
      "food": "nearby food option",
      "est_cost": "short cost note"
    }}
  ],
  "notes": "honest note if not enough places, else empty",
  "sources": []
}}

Now generate the itinerary as JSON:"""