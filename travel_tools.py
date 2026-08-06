from typing import Dict, Any, List
import os
import json


DATA_DIR = "data"


# --------------------------------------------------
# BASIC HELPERS
# --------------------------------------------------

def clean_text(value: Any) -> str:
    return str(value).lower().strip()


def get_first_value(data: Dict[str, Any], keys: List[str], default: Any = "") -> Any:
    for key in keys:
        if key in data and data[key] not in [None, ""]:
            return data[key]
    return default


def find_key_by_keywords(data: Dict[str, Any], keywords: List[str], default: Any = "") -> Any:
    """
    Finds value even if column name is slightly different.
    Example:
    tourist_spot_name, placeTitle, attractionName, city_name, etc.
    """

    for key, value in data.items():
        key_lower = key.lower().replace("_", " ").replace("-", " ")

        for keyword in keywords:
            if keyword in key_lower and value not in [None, ""]:
                return value

    return default


def place_to_search_text(place: Dict[str, Any]) -> str:
    parts = []

    for key, value in place.items():
        parts.append(f"{key}: {value}")

    return " ".join(parts).lower()


# --------------------------------------------------
# NORMALIZE JSONL RECORD
# --------------------------------------------------

def normalize_place(place: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts any JSONL row into common fields:
    destination, name, category, description, cost, time_required
    """

    normalized = place.copy()

    destination = get_first_value(
        place,
        [
            "destination",
            "Destination",
            "city",
            "City",
            "location",
            "Location",
            "place_city",
            "Place City",
            "state",
            "State",
            "district",
            "District"
        ],
        ""
    )

    if not destination:
        destination = find_key_by_keywords(
            place,
            [
                "destination",
                "city",
                "location",
                "state",
                "district"
            ],
            ""
        )

    name = get_first_value(
        place,
        [
            "name",
            "Name",
            "place_name",
            "Place Name",
            "place",
            "Place",
            "title",
            "Title",
            "attraction",
            "Attraction",
            "spot",
            "Spot",
            "tourist_place",
            "Tourist Place",
            "tourist_spot",
            "Tourist Spot",
            "monument",
            "Monument",
            "landmark",
            "Landmark"
        ],
        ""
    )

    if not name:
        name = find_key_by_keywords(
            place,
            [
                "place name",
                "place",
                "name",
                "title",
                "attraction",
                "spot",
                "tourist",
                "monument",
                "landmark"
            ],
            ""
        )

    category = get_first_value(
        place,
        [
            "category",
            "Category",
            "type",
            "Type",
            "tags",
            "Tags",
            "interest",
            "Interest",
            "theme",
            "Theme",
            "place_type",
            "Place Type"
        ],
        ""
    )

    if not category:
        category = find_key_by_keywords(
            place,
            [
                "category",
                "type",
                "tag",
                "theme",
                "interest"
            ],
            "general"
        )

    description = get_first_value(
        place,
        [
            "description",
            "Description",
            "about",
            "About",
            "details",
            "Details",
            "summary",
            "Summary",
            "info",
            "Info",
            "overview",
            "Overview"
        ],
        ""
    )

    if not description:
        description = find_key_by_keywords(
            place,
            [
                "description",
                "about",
                "detail",
                "summary",
                "info",
                "overview"
            ],
            "Explore this attraction."
        )

    cost = get_first_value(
        place,
        [
            "cost",
            "Cost",
            "price",
            "Price",
            "entry_fee",
            "Entry Fee",
            "ticket_price",
            "Ticket Price",
            "avg_cost",
            "Average Cost",
            "budget",
            "Budget"
        ],
        ""
    )

    if cost == "":
        cost = find_key_by_keywords(
            place,
            [
                "cost",
                "price",
                "fee",
                "ticket",
                "budget"
            ],
            500
        )

    time_required = get_first_value(
        place,
        [
            "time_required",
            "Time Required",
            "duration",
            "Duration",
            "visit_duration",
            "Visit Duration",
            "avg_time",
            "Average Time",
            "time",
            "Time"
        ],
        ""
    )

    if not time_required:
        time_required = find_key_by_keywords(
            place,
            [
                "time",
                "duration",
                "visit"
            ],
            "Not available"
        )

    normalized["destination"] = destination
    normalized["name"] = name if name else "Recommended Place"
    normalized["category"] = category if category else "general"
    normalized["description"] = description if description else "Explore this attraction."
    normalized["cost"] = cost if cost != "" else 500
    normalized["time_required"] = time_required if time_required else "Not available"

    return normalized


# --------------------------------------------------
# LOAD JSONL DATA
# --------------------------------------------------

def load_jsonl_data() -> List[Dict[str, Any]]:
    records = []

    if not os.path.exists(DATA_DIR):
        raise ValueError("data folder not found. Please create a data folder.")

    for file_name in os.listdir(DATA_DIR):
        if not file_name.endswith(".jsonl"):
            continue

        file_path = os.path.join(DATA_DIR, file_name)

        with open(file_path, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    raw_record = json.loads(line)
                    normalized_record = normalize_place(raw_record)
                    records.append(normalized_record)

                except json.JSONDecodeError as e:
                    print(f"Invalid JSON in {file_name}, line {line_number}: {e}")

    if not records:
        raise ValueError("No records found in .jsonl files inside data folder.")

    return records


# --------------------------------------------------
# ORCHESTRATOR
# --------------------------------------------------

def orchestrator(state: Dict[str, Any]) -> Dict[str, Any]:
    missing_fields = []

    destination = state.get("destination")
    days = state.get("days")
    travelers = state.get("travelers")
    budget_type = state.get("budget_type")

    if not destination:
        missing_fields.append("destination")

    if not days:
        missing_fields.append("days")

    if not travelers:
        missing_fields.append("travelers")

    if not budget_type:
        missing_fields.append("budget_type")

    if not destination:
        next_step = "ask_missing_value"
    elif missing_fields:
        next_step = "partial_plan"
    else:
        next_step = "full_plan"

    return {
        "missing_fields": missing_fields,
        "next_step": next_step
    }


# --------------------------------------------------
# ASK MISSING VALUE
# --------------------------------------------------

def ask_missing_value(state: Dict[str, Any]) -> Dict[str, Any]:
    missing_fields = state.get("missing_fields", [])

    questions = {
        "destination": "Please provide your travel destination.",
        "days": "How many days are you planning for the trip?",
        "travelers": "How many travelers are going?",
        "budget_type": "What is your budget type? Example: budget, mid-range, luxury."
    }

    return {
        "final_response": {
            "status": "missing_input",
            "message": "Some required information is missing.",
            "missing_fields": missing_fields,
            "questions": [
                questions[field]
                for field in missing_fields
                if field in questions
            ]
        }
    }


# --------------------------------------------------
# TOOL 1: RAG SEARCH
# --------------------------------------------------

def rag_search(state: Dict[str, Any]) -> Dict[str, Any]:
    destination = clean_text(state.get("destination", ""))

    all_places = load_jsonl_data()

    matched_places = []

    for place in all_places:
        place = normalize_place(place)

        place_destination = clean_text(place.get("destination", ""))
        search_text = place_to_search_text(place)

        if destination and (
            destination == place_destination
            or destination in place_destination
            or destination in search_text
        ):
            matched_places.append(place)

    retrieved_context = []

    for place in matched_places:
        retrieved_context.append({
            "content": json.dumps(place, ensure_ascii=False),
            "search_text": place_to_search_text(place),
            "metadata": place
        })

    return {
        "retrieved_context": retrieved_context
    }


# --------------------------------------------------
# TOOL 2: RECOMMEND PLACES
# --------------------------------------------------

def recommend_places(state: Dict[str, Any]) -> Dict[str, Any]:
    destination = clean_text(state.get("destination", ""))

    interests = [
        clean_text(item)
        for item in state.get("interests", [])
    ]

    retrieved_context = state.get("retrieved_context", [])
    recommended_places = []

    for item in retrieved_context:
        content = item.get("content", "")
        search_text = item.get("search_text", "")

        try:
            place_data = json.loads(content)
        except Exception:
            place_data = item.get("metadata", {})

        place_data = normalize_place(place_data)

        score = 0

        place_destination = clean_text(place_data.get("destination", ""))
        name = clean_text(place_data.get("name", ""))
        category = clean_text(place_data.get("category", ""))
        description = clean_text(place_data.get("description", ""))

        if destination and (
            destination == place_destination
            or destination in place_destination
            or destination in search_text
        ):
            score += 20

        if interests:
            for interest in interests:
                if interest in search_text:
                    score += 5

                if interest in name:
                    score += 3

                if interest in category:
                    score += 4

                if interest in description:
                    score += 2
        else:
            score += 1

        place_data["score"] = score
        recommended_places.append(place_data)

    recommended_places = sorted(
        recommended_places,
        key=lambda x: x.get("score", 0),
        reverse=True
    )

    return {
        "recommended_places": recommended_places
    }


# --------------------------------------------------
# PARTIAL RESPONSE
# --------------------------------------------------

def partial_response_node(state: Dict[str, Any]) -> Dict[str, Any]:
    recommended_places = state.get("recommended_places", [])

    if not recommended_places:
        return {
            "final_response": {
                "status": "partial_response",
                "message": "I could not find matching places for this destination in your JSONL data.",
                "destination": state.get("destination"),
                "recommended_places": [],
                "missing_fields": state.get("missing_fields", []),
                "suggestion": "Open /debug-data and check whether your JSONL has a destination/city/location/state field."
            }
        }

    return {
        "final_response": {
            "status": "partial_response",
            "message": "Recommended places are ready. Please provide missing details to generate budget and itinerary.",
            "destination": state.get("destination"),
            "recommended_places": recommended_places,
            "missing_fields": state.get("missing_fields", [])
        }
    }


# --------------------------------------------------
# TOOL 3: ESTIMATE BUDGET
# --------------------------------------------------

def estimate_budget(state: Dict[str, Any]) -> Dict[str, Any]:
    days = int(state.get("days", 1))
    travelers = int(state.get("travelers", 1))
    budget_type = clean_text(state.get("budget_type", "budget"))
    recommended_places = state.get("recommended_places", [])

    if days <= 0:
        days = 1

    if travelers <= 0:
        travelers = 1

    if budget_type == "luxury":
        hotel_per_day = 6000
        food_per_day = 1500
        transport_per_day = 1200

    elif budget_type == "mid-range":
        hotel_per_day = 3000
        food_per_day = 800
        transport_per_day = 700

    else:
        hotel_per_day = 1200
        food_per_day = 400
        transport_per_day = 300

    activity_total = 0

    for index in range(days):
        if recommended_places:
            place = recommended_places[index % len(recommended_places)]
            cost = place.get("cost", 500)

            try:
                activity_total += int(float(cost)) * travelers
            except Exception:
                activity_total += 500 * travelers

    hotel_total = hotel_per_day * days
    food_total = food_per_day * days * travelers
    transport_total = transport_per_day * days

    total = hotel_total + food_total + transport_total + activity_total

    return {
        "budget_breakdown": {
            "hotel": hotel_total,
            "food": food_total,
            "transport": transport_total,
            "activities": activity_total,
            "total": total,
            "per_person": round(total / travelers, 2)
        }
    }


# --------------------------------------------------
# TOOL 4: GENERATE ITINERARY
# --------------------------------------------------

def generate_itinerary(state: Dict[str, Any]) -> Dict[str, Any]:
    days = int(state.get("days", 1))
    recommended_places = state.get("recommended_places", [])

    if days <= 0:
        days = 1

    itinerary = {}

    if not recommended_places:
        for day in range(1, days + 1):
            itinerary[f"day_{day}"] = {
                "morning": "No matching place found in your JSONL data.",
                "afternoon": "Please check destination/city/location/state field in your data.",
                "evening": "Try another destination or update the dataset."
            }

        return {
            "itinerary": itinerary
        }

    for day in range(1, days + 1):
        place_index = (day - 1) % len(recommended_places)
        place = normalize_place(recommended_places[place_index])

        itinerary[f"day_{day}"] = {
            "morning": f"Visit {place.get('name', 'Recommended Place')}",
            "afternoon": f"Explore nearby {place.get('category', 'general')} attractions",
            "evening": "Try local food, shopping, or leisure walk",
            "main_place": {
                "name": place.get("name", "Recommended Place"),
                "destination": place.get("destination", ""),
                "category": place.get("category", "general"),
                "description": place.get("description", "Explore this attraction."),
                "cost": place.get("cost", "Not available"),
                "time_required": place.get("time_required", "Not available")
            }
        }

    return {
        "itinerary": itinerary
    }


# --------------------------------------------------
# TOOL 5: GROUP PLAN
# --------------------------------------------------

def group_plan(state: Dict[str, Any]) -> Dict[str, Any]:
    members = state.get("members", [])

    if not members:
        return {
            "group_plan_result": {
                "is_group_trip": False,
                "message": "Solo trip plan generated."
            }
        }

    interest_count = {}

    for member in members:
        for interest in member.get("interests", []):
            key = clean_text(interest)
            interest_count[key] = interest_count.get(key, 0) + 1

    common_interests = sorted(
        interest_count,
        key=interest_count.get,
        reverse=True
    )

    return {
        "group_plan_result": {
            "is_group_trip": True,
            "common_interests": common_interests,
            "message": "Group plan optimized using common interests."
        }
    }


# --------------------------------------------------
# FINAL RESPONSE
# --------------------------------------------------

def final_response_node(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "final_response": {
            "status": "success",
            "destination": state.get("destination"),
            "interests": state.get("interests", []),
            "days": state.get("days"),
            "travelers": state.get("travelers"),
            "budget_type": state.get("budget_type"),
            "recommended_places": state.get("recommended_places", []),
            "budget_breakdown": state.get("budget_breakdown", {}),
            "itinerary": state.get("itinerary", {}),
            "group_plan": state.get("group_plan_result", {})
        }
    }