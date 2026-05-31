"""Session-wide pytest configuration.

State isolation is handled by the FastAPI lifespan: each TestClient call to
create_app() gets its own app.state with a fresh InMemorySimulationRepository,
so no cross-test cleanup is required here.
"""
