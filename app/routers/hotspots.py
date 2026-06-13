from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Hotspot
from ..schemas import HotspotCreate, HotspotUpdate, HotspotOut

router = APIRouter(prefix="/api/hotspots", tags=["热点互动"])


@router.post("", response_model=HotspotOut)
def create_hotspot(data: HotspotCreate, db: Session = Depends(get_db)):
    hotspot = Hotspot(**data.model_dump())
    db.add(hotspot)
    db.commit()
    db.refresh(hotspot)
    return hotspot


@router.get("", response_model=List[HotspotOut])
def list_hotspots(
    hall_id: Optional[int] = Query(None),
    hotspot_type: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(Hotspot)
    if hall_id is not None:
        q = q.filter(Hotspot.hall_id == hall_id)
    if hotspot_type is not None:
        q = q.filter(Hotspot.hotspot_type == hotspot_type)
    return q.offset(skip).limit(limit).all()


@router.get("/{hotspot_id}", response_model=HotspotOut)
def get_hotspot(hotspot_id: int, db: Session = Depends(get_db)):
    hotspot = db.query(Hotspot).filter(Hotspot.id == hotspot_id).first()
    if not hotspot:
        raise HTTPException(status_code=404, detail="热点不存在")
    return hotspot


@router.put("/{hotspot_id}", response_model=HotspotOut)
def update_hotspot(hotspot_id: int, data: HotspotUpdate, db: Session = Depends(get_db)):
    hotspot = db.query(Hotspot).filter(Hotspot.id == hotspot_id).first()
    if not hotspot:
        raise HTTPException(status_code=404, detail="热点不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(hotspot, key, value)
    db.commit()
    db.refresh(hotspot)
    return hotspot


@router.delete("/{hotspot_id}")
def delete_hotspot(hotspot_id: int, db: Session = Depends(get_db)):
    hotspot = db.query(Hotspot).filter(Hotspot.id == hotspot_id).first()
    if not hotspot:
        raise HTTPException(status_code=404, detail="热点不存在")
    db.delete(hotspot)
    db.commit()
    return {"detail": "已删除"}
