"""FastAPI routes for catalog. Frontend teammate includes this router.

    from services.catalog_router import router as catalog_router
    app.include_router(catalog_router)
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from services.catalog import CatalogError, get_catalog

router = APIRouter(prefix="/v1/temples", tags=["catalog"])


def _call(fn, temple_id: str):
    try:
        return fn(temple_id)
    except CatalogError as exc:
        raise HTTPException(status_code=exc.status, detail={"code": exc.code, "message": exc.message}) from exc


@router.get("/{temple_id}")
def temple(temple_id: str):
    return _call(get_catalog().get_temple, temple_id)


@router.get("/{temple_id}/costs")
def costs(temple_id: str):
    return _call(get_catalog().get_costs, temple_id)


@router.get("/{temple_id}/hotels")
def hotels(temple_id: str):
    return _call(get_catalog().get_hotels, temple_id)


@router.get("/{temple_id}/restaurants")
def restaurants(temple_id: str):
    return _call(get_catalog().get_restaurants, temple_id)


@router.get("/{temple_id}/travel")
def travel(temple_id: str):
    return _call(get_catalog().get_travel, temple_id)


@router.get("/{temple_id}/emergency")
def emergency(temple_id: str):
    return _call(get_catalog().get_emergency, temple_id)
