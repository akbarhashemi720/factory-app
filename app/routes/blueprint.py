"""
Product Blueprint — internal test route (Puzzle 5, AI Factory v2 planning).

POST /blueprint/draft is an ISOLATED, BACKEND-ONLY test endpoint for the
future AI Factory v2 thinking layer. It exists purely so the rule-based
generator (app/blueprint/generator.py) can be exercised over real HTTP
during development, before anything is shown to users.

What this endpoint does NOT do:
  - It does not call Claude or any external API.
  - It does not touch the database — nothing is read or written.
  - It does not affect, read, or modify any project/version/understanding.
  - It does not influence website_intent, pm_agent, the builder, or export.
  - It is not registered anywhere in the frontend (index.html is untouched).

Path safety: this router is registered with prefix "/blueprint", which is
a completely separate top-level path from the existing "/projects" router
(see app/routes/projects.py) — so there is no possibility of colliding
with dynamic routes like /projects/{project_id}.

Puzzle 5.5 — access gate: this endpoint is otherwise public with no
auth anywhere in the app, so it is now gated behind a single environment
flag, ENABLE_INTERNAL_BLUEPRINT_ENDPOINT. When unset/not "true", the
route returns 404 (not 403) so the endpoint stays undiscoverable rather
than revealing that a protected resource exists here. This gate affects
ONLY this one route — nothing else in the app changes.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.blueprint.generator import generate_product_blueprint
from app.blueprint.models import ProductBlueprint

router = APIRouter(prefix="/blueprint", tags=["blueprint-internal-test"])


class BlueprintDraftRequest(BaseModel):
    raw_text: str


def _internal_blueprint_endpoint_enabled() -> bool:
    return os.getenv("ENABLE_INTERNAL_BLUEPRINT_ENDPOINT", "").lower() == "true"


@router.post("/draft", response_model=ProductBlueprint)
def draft_blueprint(body: BlueprintDraftRequest) -> ProductBlueprint:
    """
    Internal/dev-only: run the isolated rule-based Product Blueprint
    generator on raw_text and return the result. Stateless — nothing is
    saved, nothing is read from or written to the database.

    Gated behind ENABLE_INTERNAL_BLUEPRINT_ENDPOINT — returns 404 when
    the flag is missing, empty, or not exactly "true".
    """
    if not _internal_blueprint_endpoint_enabled():
        raise HTTPException(status_code=404, detail="Not found")
    return generate_product_blueprint(body.raw_text)
