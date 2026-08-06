from typing import List, Dict, Any
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from travel_graph import run_trip_workflow


app = FastAPI(title="QuanTrip AI LangGraph Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TripRequest(BaseModel):
    destination: str = ""
    interests: List[str] = Field(default_factory=list)
    days: int = 0
    travelers: int = 0
    budget_type: str = ""
    members: List[Dict[str, Any]] = Field(default_factory=list)


class ChatRequest(BaseModel):
    session_id: str = ""
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    extracted_state: Dict[str, Any]
    result: Dict[str, Any]


chat_sessions: Dict[str, Dict[str, Any]] = {}


def to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()


@app.get("/")
def home():
    return {
        "message": "QuanTrip AI backend is running",
        "architecture": "LangGraph + JSONL Data",
        "routes": [
            "/plan-trip",
            "/chatbot",
            "/debug-data",
            "/debug-destinations"
        ]
    }


@app.get("/debug-data")
def debug_data():
    from travel_tools import load_jsonl_data

    data = load_jsonl_data()

    if not data:
        return {
            "total_records": 0,
            "sample_record": {},
            "available_keys": []
        }

    return {
        "total_records": len(data),
        "sample_record": data[0],
        "available_keys": list(data[0].keys())
    }


@app.get("/debug-destinations")
def debug_destinations():
    from travel_tools import load_jsonl_data

    data = load_jsonl_data()

    destinations = []

    for item in data:
        destinations.append({
            "destination": item.get("destination", ""),
            "name": item.get("name", ""),
            "category": item.get("category", ""),
            "description": item.get("description", "")
        })

    return {
        "total_records": len(data),
        "destinations_sample": destinations[:100]
    }


@app.post("/plan-trip")
def plan_trip(request: TripRequest):
    return run_trip_workflow(to_dict(request))


def extract_trip_info_from_message(message: str) -> Dict[str, Any]:
    text = message.lower().strip()

    extracted = {
        "destination": "",
        "interests": [],
        "days": 0,
        "travelers": 0,
        "budget_type": "",
        "members": []
    }

    known_destinations = [
        "goa",
        "delhi",
        "new delhi",
        "jaipur",
        "manali",
        "mumbai",
        "kerala",
        "udaipur",
        "shimla",
        "rishikesh",
        "varanasi",
        "bangalore",
        "bengaluru",
        "mysore",
        "ooty",
        "pondicherry",
        "agra",
        "darjeeling",
        "ladakh",
        "leh",
        "kashmir",
        "amritsar",
        "amristar",
        "chandigarh",
        "hyderabad",
        "chennai",
        "kolkata",
        "pune"
    ]

    for destination in known_destinations:
        if destination in text:
            if destination == "bengaluru":
                extracted["destination"] = "Bangalore"
            elif destination == "amristar":
                extracted["destination"] = "Amritsar"
            elif destination == "new delhi":
                extracted["destination"] = "Delhi"
            else:
                extracted["destination"] = destination.title()
            break

    if not extracted["destination"]:
        words = text.replace(",", " ").replace(".", " ").split()

        travel_words = [
            "to",
            "visit"
        ]

        ignore_words = [
            "with",
            "for",
            "days",
            "day",
            "people",
            "person",
            "travelers",
            "traveler",
            "traveller",
            "travellers",
            "budget",
            "economic",
            "economy",
            "cheap",
            "affordable",
            "itinerary",
            "itineary",
            "itenary",
            "give"
        ]

        for index, word in enumerate(words):
            if word in travel_words and index + 1 < len(words):
                candidate = words[index + 1]

                if candidate not in ignore_words and not candidate.isdigit():
                    extracted["destination"] = candidate.title()
                    break

    interest_keywords = [
        "beach",
        "adventure",
        "nature",
        "food",
        "history",
        "culture",
        "nightlife",
        "shopping",
        "photography",
        "trekking",
        "peace",
        "snow",
        "temple",
        "museum",
        "waterfall",
        "fort",
        "cafe",
        "market",
        "heritage",
        "religious",
        "monument",
        "memorial"
    ]

    for interest in interest_keywords:
        if interest in text:
            extracted["interests"].append(interest)

    words = text.replace(",", " ").replace(".", " ").split()

    for index, word in enumerate(words):
        if word.isdigit():
            number = int(word)

            if index + 1 < len(words):
                next_word = words[index + 1]

                if next_word in [
                    "day",
                    "days"
                ]:
                    extracted["days"] = number

                if next_word in [
                    "person",
                    "people",
                    "traveler",
                    "travelers",
                    "traveller",
                    "travellers",
                    "member",
                    "members",
                    "guest",
                    "guests"
                ]:
                    extracted["travelers"] = number

    if "luxury" in text:
        extracted["budget_type"] = "luxury"

    elif (
        "mid-range" in text
        or "mid range" in text
        or "medium" in text
        or "moderate" in text
    ):
        extracted["budget_type"] = "mid-range"

    elif (
        "budget" in text
        or "cheap" in text
        or "low cost" in text
        or "affordable" in text
        or "economic" in text
        or "economy" in text
    ):
        extracted["budget_type"] = "budget"

    return extracted


def apply_context_for_single_number(
    old_state: Dict[str, Any],
    new_data: Dict[str, Any],
    message: str
) -> Dict[str, Any]:
    text = message.strip()

    if not text.isdigit():
        return new_data

    number = int(text)

    if not old_state.get("days"):
        new_data["days"] = number

    elif not old_state.get("travelers"):
        new_data["travelers"] = number

    return new_data


def merge_trip_state(
    old_state: Dict[str, Any],
    new_data: Dict[str, Any]
) -> Dict[str, Any]:
    merged = old_state.copy()

    for key, value in new_data.items():
        if isinstance(value, list):
            if value:
                old_list = merged.get(key, [])
                merged[key] = list(set(old_list + value))

        elif value:
            merged[key] = value

    return merged


def format_recommended_places(
    destination: str,
    recommended_places: List[Dict[str, Any]]
) -> str:
    if not recommended_places:
        return (
            f"No recommended places found for {destination}.\n"
            "Please check whether your JSONL data has matching destination/city/location/state values."
        )

    reply = f"Recommended places for {destination}:\n\n"

    for index, place in enumerate(recommended_places[:10], start=1):
        reply += f"{index}. {place.get('name', 'Recommended Place')}\n"
        reply += f"   Destination: {place.get('destination', 'Not available')}\n"
        reply += f"   Category: {place.get('category', 'general')}\n"
        reply += f"   Description: {place.get('description', 'Not available')}\n"
        reply += f"   Cost: ₹{place.get('cost', 'Not available')}\n"
        reply += f"   Time Required: {place.get('time_required', 'Not available')}\n\n"

    return reply


def format_itinerary(
    destination: str,
    days: int,
    itinerary: Dict[str, Any]
) -> str:
    if not itinerary:
        return (
            "Itinerary is not available yet. "
            "Please provide destination, days, travelers, and budget type."
        )

    reply = f"Here is your {days}-day itinerary for {destination}:\n\n"

    for day, plan in itinerary.items():
        day_title = day.replace("_", " ").title()

        reply += f"{day_title}:\n"
        reply += f"Morning: {plan.get('morning', 'Not available')}\n"
        reply += f"Afternoon: {plan.get('afternoon', 'Not available')}\n"
        reply += f"Evening: {plan.get('evening', 'Not available')}\n"

        main_place = plan.get("main_place", {})

        if isinstance(main_place, dict) and main_place:
            reply += f"Main Place: {main_place.get('name', 'Recommended Place')}\n"
            reply += f"Destination: {main_place.get('destination', 'Not available')}\n"
            reply += f"Category: {main_place.get('category', 'general')}\n"
            reply += f"Description: {main_place.get('description', 'Not available')}\n"
            reply += f"Cost: ₹{main_place.get('cost', 'Not available')}\n"
            reply += f"Time Required: {main_place.get('time_required', 'Not available')}\n"

        reply += "\n"

    return reply


def format_budget(
    destination: str,
    days: int,
    budget: Dict[str, Any]
) -> str:
    if not budget:
        return (
            "Budget is not available yet. "
            "Please provide days, travelers, and budget type."
        )

    reply = f"Budget estimate for your {days}-day trip to {destination}:\n\n"
    reply += f"Hotel: ₹{budget.get('hotel', 0)}\n"
    reply += f"Food: ₹{budget.get('food', 0)}\n"
    reply += f"Transport: ₹{budget.get('transport', 0)}\n"
    reply += f"Activities: ₹{budget.get('activities', 0)}\n"
    reply += f"Total: ₹{budget.get('total', 0)}\n"
    reply += f"Per Person: ₹{budget.get('per_person', 0)}\n"

    return reply


def create_chat_reply(
    result: Dict[str, Any],
    user_message: str = ""
) -> str:
    if not result:
        return (
            "I could not generate a trip response. "
            "Please provide your destination and trip details."
        )

    user_message = user_message.lower()
    status = result.get("status", "")

    destination = result.get("destination", "your destination")
    days = result.get("days", 0)
    recommended_places = result.get("recommended_places", [])
    itinerary = result.get("itinerary", {})
    budget = result.get("budget_breakdown", {})

    wants_recommendation = (
        "recommend" in user_message
        or "recommended" in user_message
        or "place" in user_message
        or "places" in user_message
        or "suggest" in user_message
        or "attraction" in user_message
        or "attractions" in user_message
    )

    wants_itinerary = (
        "itinerary" in user_message
        or "itineary" in user_message
        or "itenary" in user_message
        or "itinery" in user_message
        or "schedule" in user_message
        or "day wise" in user_message
        or "day-wise" in user_message
        or "travel plan" in user_message
        or "trip plan" in user_message
    )

    wants_budget = (
        "budget" in user_message
        or "cost" in user_message
        or "price" in user_message
        or "expense" in user_message
        or "money" in user_message
    )

    if status == "missing_input":
        questions = result.get("questions", [])

        if questions:
            return "I need a few more details. " + " ".join(questions)

        return "Please provide your trip details."

    if status == "partial_response":
        missing_fields = result.get("missing_fields", [])

        if wants_itinerary:
            if "days" in missing_fields:
                return (
                    "I can generate the itinerary, but I need the number of days first. "
                    "For example: 3 days"
                )

            if "travelers" in missing_fields:
                return (
                    "I can generate the itinerary, but I need the number of travelers first. "
                    "For example: 3 travelers"
                )

            if "budget_type" in missing_fields:
                return (
                    "I can generate the itinerary, but I need the budget type first. "
                    "For example: economic budget"
                )

            return "I can generate the itinerary after all required details are available."

        if wants_recommendation:
            reply = format_recommended_places(destination, recommended_places)

            if missing_fields:
                reply += "To generate budget and itinerary, please provide: "
                reply += ", ".join(missing_fields)

            return reply

        place_names = []

        for place in recommended_places[:5]:
            if isinstance(place, dict):
                place_names.append(place.get("name", "Recommended Place"))

        reply = f"I found some good places for {destination}. "

        if place_names:
            reply += "Recommended places are: " + ", ".join(place_names) + ". "

        if missing_fields:
            reply += (
                "Please provide "
                + ", ".join(missing_fields)
                + " to generate budget and itinerary."
            )

        return reply

    if status == "success":
        if wants_recommendation:
            return format_recommended_places(destination, recommended_places)

        if wants_itinerary:
            return format_itinerary(destination, days, itinerary)

        if wants_budget:
            return format_budget(destination, days, budget)

        total_budget = budget.get("total", 0)

        return (
            f"Your {days}-day trip plan for {destination} is ready.\n"
            f"Estimated total budget is ₹{total_budget}.\n\n"
            "You can ask:\n"
            "- recommend places\n"
            "- give me itinerary\n"
            "- show budget"
        )

    if status == "error":
        return "Something went wrong: " + result.get("message", "")

    return (
        "I processed your message. "
        "You can ask for recommendation, itinerary, or budget."
    )


@app.post("/chatbot", response_model=ChatResponse)
def chatbot(request: ChatRequest):
    session_id = request.session_id
    message = request.message.strip()
    message_lower = message.lower()

    if message_lower in [
        "reset",
        "clear",
        "new trip",
        "start new trip"
    ]:
        session_id = str(uuid4())

        chat_sessions[session_id] = {
            "destination": "",
            "interests": [],
            "days": 0,
            "travelers": 0,
            "budget_type": "",
            "members": []
        }

        return {
            "session_id": session_id,
            "reply": "New trip started. Please tell me your destination.",
            "extracted_state": chat_sessions[session_id],
            "result": {}
        }

    if not session_id:
        session_id = str(uuid4())

    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "destination": "",
            "interests": [],
            "days": 0,
            "travelers": 0,
            "budget_type": "",
            "members": []
        }

    old_state = chat_sessions[session_id]

    extracted_data = extract_trip_info_from_message(message)

    extracted_data = apply_context_for_single_number(
        old_state=old_state,
        new_data=extracted_data,
        message=message
    )

    updated_state = merge_trip_state(
        old_state=old_state,
        new_data=extracted_data
    )

    chat_sessions[session_id] = updated_state

    try:
        result = run_trip_workflow(updated_state)

        if result is None:
            result = {
                "status": "error",
                "message": "Workflow returned no result."
            }

    except Exception as e:
        result = {
            "status": "error",
            "message": str(e)
        }

    reply = create_chat_reply(
        result=result,
        user_message=message
    )

    return {
        "session_id": session_id,
        "reply": reply,
        "extracted_state": updated_state,
        "result": result
    }