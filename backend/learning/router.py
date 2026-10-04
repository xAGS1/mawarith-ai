"""Read-only educational resources; POST /ask remains the execution entry point."""
from fastapi import APIRouter, HTTPException

from backend.learning.catalogs import list_concepts, list_examples, list_paths

router = APIRouter(prefix="/learn", tags=["learning"])


def find_record(records: list[dict], key: str, identifier: str) -> dict:
    for record in records:
        if record[key] == identifier:
            return record
    raise HTTPException(status_code=404, detail="Learning resource not found")


@router.get("/concepts")
def concepts():
    return list_concepts()


@router.get("/concepts/{concept_id}")
def concept(concept_id: str):
    return find_record(list_concepts(), "concept_id", concept_id)


@router.get("/paths")
def paths():
    return list_paths()


@router.get("/paths/{path_id}")
def path(path_id: str):
    return find_record(list_paths(), "path_id", path_id)


@router.get("/examples")
def examples():
    return list_examples()


@router.get("/examples/{example_id}")
def example(example_id: str):
    return find_record(list_examples(), "example_id", example_id)
