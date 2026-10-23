# QuanTrip AI Architecture

This is a high-level architecture guide for the travel-planning project. Confirm the actual router, tool, vector-store, and model names against the current source.

## Conceptual flow

```text
Travel request
    -> input parsing and preference extraction
    -> itinerary / budget / place tools
    -> retrieval from available travel data
    -> LLM orchestration
    -> structured itinerary and follow-up answer
```

## Components to document in source

- API routes and request/response schemas
- Data ingestion for places, blogs, and other travel sources
- Vector-store collections and embedding model
- LLM provider, prompt templates, and tool definitions
- Budget calculation and recommendation logic
- Error handling, caching, and persistent state

## Reliability boundaries

Use deterministic code for arithmetic such as budgets and totals. Treat model-generated recommendations as suggestions, not verified availability. Place details, prices, transport, and opening hours can change; surface sources and timestamps where possible.

## Testing

- Validate malformed and incomplete trip requests.
- Test budget boundaries and currency formatting.
- Test empty retrieval results and conflicting source records.
- Test model timeouts, rate limits, and unavailable tools.
- Verify that structured itinerary responses match the API schema.
- Add representative end-to-end tests with non-sensitive fixture data.

## Security

Keep model-provider credentials and database secrets in environment variables or deployment secret stores. Do not log personal travel details unnecessarily. Restrict tool permissions and avoid allowing untrusted retrieved text to trigger arbitrary actions.
