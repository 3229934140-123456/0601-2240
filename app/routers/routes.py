from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import TourRoute
from ..schemas import RouteCreate, RouteUpdate, RouteOut

router = APIRouter(prefix="/api/routes", tags=["参观路线"])


@router.post("", response_model=RouteOut)
def create_route(data: RouteCreate, db: Session = Depends(get_db)):
    route = TourRoute(**data.model_dump())
    db.add(route)
    db.commit()
    db.refresh(route)
    return route


@router.get("", response_model=List[RouteOut])
def list_routes(
    hall_id: Optional[int] = Query(None),
    is_published: Optional[bool] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(TourRoute)
    if hall_id is not None:
        q = q.filter(TourRoute.hall_id == hall_id)
    if is_published is not None:
        q = q.filter(TourRoute.is_published == is_published)
    return q.offset(skip).limit(limit).all()


@router.get("/{route_id}", response_model=RouteOut)
def get_route(route_id: int, db: Session = Depends(get_db)):
    route = db.query(TourRoute).filter(TourRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="参观路线不存在")
    return route


@router.put("/{route_id}", response_model=RouteOut)
def update_route(route_id: int, data: RouteUpdate, db: Session = Depends(get_db)):
    route = db.query(TourRoute).filter(TourRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="参观路线不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(route, key, value)
    db.commit()
    db.refresh(route)
    return route


@router.delete("/{route_id}")
def delete_route(route_id: int, db: Session = Depends(get_db)):
    route = db.query(TourRoute).filter(TourRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="参观路线不存在")
    db.delete(route)
    db.commit()
    return {"detail": "已删除"}
