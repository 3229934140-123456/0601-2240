from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Exhibit
from ..schemas import ExhibitCreate, ExhibitUpdate, ExhibitOut

router = APIRouter(prefix="/api/exhibits", tags=["展品管理"])


@router.post("", response_model=ExhibitOut)
def create_exhibit(data: ExhibitCreate, db: Session = Depends(get_db)):
    exhibit = Exhibit(**data.model_dump())
    db.add(exhibit)
    db.commit()
    db.refresh(exhibit)
    return exhibit


@router.get("", response_model=List[ExhibitOut])
def list_exhibits(
    hall_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    is_published: Optional[bool] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(Exhibit)
    if hall_id is not None:
        q = q.filter(Exhibit.hall_id == hall_id)
    if category is not None:
        q = q.filter(Exhibit.category == category)
    if is_published is not None:
        q = q.filter(Exhibit.is_published == is_published)
    return q.offset(skip).limit(limit).all()


@router.get("/{exhibit_id}", response_model=ExhibitOut)
def get_exhibit(exhibit_id: int, db: Session = Depends(get_db)):
    exhibit = db.query(Exhibit).filter(Exhibit.id == exhibit_id).first()
    if not exhibit:
        raise HTTPException(status_code=404, detail="展品不存在")
    return exhibit


@router.put("/{exhibit_id}", response_model=ExhibitOut)
def update_exhibit(exhibit_id: int, data: ExhibitUpdate, db: Session = Depends(get_db)):
    exhibit = db.query(Exhibit).filter(Exhibit.id == exhibit_id).first()
    if not exhibit:
        raise HTTPException(status_code=404, detail="展品不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(exhibit, key, value)
    db.commit()
    db.refresh(exhibit)
    return exhibit


@router.delete("/{exhibit_id}")
def delete_exhibit(exhibit_id: int, db: Session = Depends(get_db)):
    exhibit = db.query(Exhibit).filter(Exhibit.id == exhibit_id).first()
    if not exhibit:
        raise HTTPException(status_code=404, detail="展品不存在")
    db.delete(exhibit)
    db.commit()
    return {"detail": "已删除"}
