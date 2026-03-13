from fastapi import status
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str = Field(description="Human-readable error detail.")


class ValidationErrorItem(BaseModel):
    loc: list[str | int]
    msg: str
    type: str


class ValidationErrorResponse(BaseModel):
    detail: list[ValidationErrorItem]


def _error_response(description: str) -> dict[str, object]:
    return {
        "model": ErrorResponse,
        "description": description,
    }


def merge_responses(
    *response_maps: dict[int, dict[str, object]],
) -> dict[int, dict[str, object]]:
    merged: dict[int, dict[str, object]] = {}
    for response_map in response_maps:
        merged.update(response_map)
    return merged


RESPONSE_401_UNAUTHORIZED = {
    status.HTTP_401_UNAUTHORIZED: _error_response(
        "Missing, invalid, or expired bearer token.",
    )
}

RESPONSE_404_NOT_FOUND = {
    status.HTTP_404_NOT_FOUND: _error_response("Requested resource was not found.")
}

RESPONSE_404_NOT_FOUND_OR_NOT_OWNED = {
    status.HTTP_404_NOT_FOUND: _error_response(
        "Requested resource was not found (or is not owned by the current user).",
    )
}

RESPONSE_409_CONFLICT = {
    status.HTTP_409_CONFLICT: _error_response(
        "Request conflicts with the current resource state.",
    )
}

RESPONSE_422_VALIDATION = {
    422: {
        "model": ValidationErrorResponse,
        "description": "Request validation failed.",
    }
}
