from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Hall
from ..schemas import HallCreate, HallUpdate, HallOut

router = APIRouter(prefix="/api/halls", tags=["展厅管理"])


@router.post("", response_model=HallOut)
def create_hall(data: HallCreate, db: Session = Depends(get_db)):
    hall = Hall(**data.model_dump())
    db.add(hall)
    db.commit()
    db.refresh(hall)
    return hall


@router.get("", response_model=List[HallOut])
def list_halls(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Hall).offset(skip).limit(limit).all()


@router.get("/{hall_id}", response_model=HallOut)
def get_hall(hall_id: int, db: Session = Depends(get_db)):
    hall = db.query(Hall).filter(Hall.id == hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="展厅不存在")
    return hall


@router.put("/{hall_id}", response_model=HallOut)
def update_hall(hall_id: int, data: HallUpdate, db: Session = Depends(get_db)):
    hall = db.query(Hall).filter(Hall.id == hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="展厅不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(hall, key, value)
    db.commit()
    db.refresh(hall)
    return hall


@router.delete("/{hall_id}")
def delete_hall(hall_id: int, db: Session = Depends(get_db)):
    hall = db.query(Hall).filter(Hall.id == hall_id).first()
    if not hall:
        raise HTTPException(status_code=404, detail="展厅不存在")
    db.delete(hall)
    db.commit()
    return {"detail": "已删除"}
