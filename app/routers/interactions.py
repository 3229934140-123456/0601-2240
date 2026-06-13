from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import DwellRecord, Favorite, QAResult, InteractionRecord
from ..schemas import (
    DwellRecordCreate,
    DwellRecordOut,
    FavoriteCreate,
    FavoriteOut,
    QAResultCreate,
    QAResultOut,
    InteractionCreate,
    InteractionOut,
)

router = APIRouter(prefix="/api/interactions", tags=["互动记录"])


@router.post("/dwell", response_model=DwellRecordOut)
def create_dwell_record(data: DwellRecordCreate, db: Session = Depends(get_db)):
    record = DwellRecord(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/dwell", response_model=List[DwellRecordOut])
def list_dwell_records(
    session_id: Optional[int] = Query(None),
    exhibit_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(DwellRecord)
    if session_id is not None:
        q = q.filter(DwellRecord.session_id == session_id)
    if exhibit_id is not None:
        q = q.filter(DwellRecord.exhibit_id == exhibit_id)
    return q.offset(skip).limit(limit).all()


@router.post("/favorites", response_model=FavoriteOut)
def create_favorite(data: FavoriteCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(Favorite)
        .filter(Favorite.session_id == data.session_id, Favorite.exhibit_id == data.exhibit_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="已收藏该展品")
    favorite = Favorite(**data.model_dump())
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


@router.get("/favorites", response_model=List[FavoriteOut])
def list_favorites(
    session_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(Favorite)
    if session_id is not None:
        q = q.filter(Favorite.session_id == session_id)
    return q.offset(skip).limit(limit).all()


@router.delete("/favorites/{favorite_id}")
def delete_favorite(favorite_id: int, db: Session = Depends(get_db)):
    favorite = db.query(Favorite).filter(Favorite.id == favorite_id).first()
    if not favorite:
        raise HTTPException(status_code=404, detail="收藏记录不存在")
    db.delete(favorite)
    db.commit()
    return {"detail": "已取消收藏"}


@router.post("/qa", response_model=QAResultOut)
def create_qa_result(data: QAResultCreate, db: Session = Depends(get_db)):
    record = QAResult(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/qa", response_model=List[QAResultOut])
def list_qa_results(
    session_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(QAResult)
    if session_id is not None:
        q = q.filter(QAResult.session_id == session_id)
    return q.offset(skip).limit(limit).all()


@router.post("/records", response_model=InteractionOut)
def create_interaction(data: InteractionCreate, db: Session = Depends(get_db)):
    record = InteractionRecord(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/records", response_model=List[InteractionOut])
def list_interactions(
    session_id: Optional[int] = Query(None),
    interaction_type: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(InteractionRecord)
    if session_id is not None:
        q = q.filter(InteractionRecord.session_id == session_id)
    if interaction_type is not None:
        q = q.filter(InteractionRecord.interaction_type == interaction_type)
    return q.offset(skip).limit(limit).all()
