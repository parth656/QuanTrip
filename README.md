# QuanTrip AI

QuanTrip AI is an AI-assisted travel-planning project intended to turn a user's trip request into a structured itinerary. The project portfolio describes a Python/FastAPI backend using LLM tooling.

## Intended capabilities

- Interpret a travel request in natural language.
- Recommend places and organize an itinerary.
- Help reason about budget and travel preferences.
- Answer follow-up questions using the application's travel knowledge sources.

The exact endpoints, data sources, and available tools must be confirmed against the current source code; planned features should not be described as complete until tested.

## Technology

- Python
- FastAPI
- LangChain / LLM integrations
- Retrieval or vector-store components where configured

## Getting started

```bash
git clone https://github.com/parth656/QuanTrip.git
cd QuanTrip
```

Inspect the repository's dependency manifest and application entry point before installing. Recommended local setup:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install the dependencies listed by the project, configure required API keys as environment variables, and start the FastAPI app using the actual module path. If the application uses Uvicorn, the command typically follows the form `uvicorn <module>:app --reload`; replace the placeholder with the verified module path.

## Configuration

Create a local `.env` from a sanitized example file if the project uses dotenv. Never commit API keys, database credentials, user travel data, or generated local indexes.

## API documentation

When running locally, FastAPI commonly exposes interactive API docs at `/docs` and an OpenAPI schema at `/openapi.json`, provided the application has not disabled these endpoints.

## Validation checklist

- [ ] Add a sample request and response for each public endpoint.
- [ ] Test invalid dates, unavailable destinations, and incomplete trip requests.
- [ ] Validate budget arithmetic deterministically rather than relying on LLM prose.
- [ ] Explain the source and freshness of place information.
- [ ] Add tests for recommendation and itinerary generation.
- [ ] Document deployment and persistent storage.

## Limitations

Travel recommendations and prices may be stale or incomplete. Users should independently verify opening hours, bookings, transport, and current costs before travel.
