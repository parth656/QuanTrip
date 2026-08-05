import os
import sys
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from rag.pipeline import RAGPipeline



load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
RAG_DIR = BASE_DIR / "rag"

# Let "from src.xxx" and "from pipeline import ..." work from the root
sys.path.insert(0, str(RAG_DIR))

 


# ---------------------------------------------------------
# Config (auto-find data / chroma_db)
# ---------------------------------------------------------
def _resolve(folder_name):
    rag_path = RAG_DIR / folder_name
    root_path = BASE_DIR / folder_name

    if rag_path.exists():
        return str(rag_path)

    if root_path.exists():
        return str(root_path)

    # Default location if not built yet
    return str(rag_path)


DATA_FOLDER = _resolve("data")
CHROMA_DIR = _resolve("chroma_db")

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GEMINI_MODEL = "gemini-3.1-flash-lite"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ---------------------------------------------------------
# Build the pipeline ONCE at startup
# ---------------------------------------------------------
pipeline = RAGPipeline(
    data_folder=DATA_FOLDER,
    chroma_dir=CHROMA_DIR,
    embedding_model=EMBEDDING_MODEL,
    gemini_model=GEMINI_MODEL,
    gemini_api_key=GEMINI_API_KEY,
)


# ---------------------------------------------------------
# FastAPI
# ---------------------------------------------------------
app = FastAPI(title="QuanTrip AI")

templates = Jinja2Templates(
    directory=str(BASE_DIR / "frontend" / "templates")
)

app.mount(
    "/static",
    StaticFiles(
        directory=str(BASE_DIR / "frontend" / "static")
    ),
    name="static",
)


class ItineraryRequest(BaseModel):
    destination: str
    days: int = Field(ge=1, le=30)
    budget: str = "moderate"
    traveller_count: int = Field(default=1, ge=1, le=50)
    interests: List[str] = []


def itinerary_to_text(data: dict) -> str:
    lines = []

    if data.get("summary"):
        lines += [data["summary"], ""]

    for day in data.get("itinerary", []):
        lines.append(
            f"Day {day.get('day', '')}: {day.get('title', '')}"
        )

        for key, label in [
            ("morning", "Morning"),
            ("afternoon", "Afternoon"),
            ("evening", "Evening"),
            ("food", "Food"),
            ("est_cost", "Est. cost"),
        ]:
            if day.get(key):
                lines.append(f"  {label}: {day[key]}")

        lines.append("")

    if data.get("notes"):
        lines.append(f"Note: {data['notes']}")

    return "\n".join(lines).strip()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )


@app.post("/api/itinerary")
async def api_itinerary(req: ItineraryRequest):
    try:
        data, raw = pipeline.run(
            city=req.destination,
            days=req.days,
            budget=req.budget,
            travelers=req.traveller_count,
            travel_types=req.interests or ["sightseeing"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    return {
        "status": "ok",
        "data": data,
        "plan": itinerary_to_text(data),
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
    }