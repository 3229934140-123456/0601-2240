from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import VisitorSession, DisconnectRecord, PhotoSpot, PhotoRecord
from ..schemas import (
    SessionCreate,
    SessionOut,
    PhotoSpotCreate,
    PhotoSpotUpdate,
    PhotoSpotOut,
    PhotoRecordCreate,
    PhotoRecordOut,
)

router = APIRouter(prefix="/api/sessions", tags=["访客会话与合影"])


@router.post("", response_model=SessionOut)
def create_session(data: SessionCreate, db: Session = Depends(get_db)):
    session = VisitorSession(**data.model_dump())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("", response_model=List[SessionOut])
def list_sessions(
    hall_id: Optional[int] = Query(None),
    visitor_id: Optional[str] = Query(None),
    is_online: Optional[bool] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(VisitorSession)
    if hall_id is not None:
        q = q.filter(VisitorSession.hall_id == hall_id)
    if visitor_id is not None:
        q = q.filter(VisitorSession.visitor_id == visitor_id)
    if is_online is not None:
        q = q.filter(VisitorSession.is_online == is_online)
    return q.offset(skip).limit(limit).all()


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(VisitorSession).filter(VisitorSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return session


@router.post("/{session_id}/logout")
def logout_session(session_id: int, reason: str = "normal", db: Session = Depends(get_db)):
    session = db.query(VisitorSession).filter(VisitorSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    session.is_online = False
    session.logout_at = datetime.utcnow()
    db.commit()

    if reason != "normal":
        disconnect = DisconnectRecord(
            session_id=session.id,
            visitor_id=session.visitor_id,
            hall_id=session.hall_id,
            reason=reason,
            disconnected_at=datetime.utcnow(),
        )
        db.add(disconnect)
        db.commit()

    return {"detail": "已登出"}


@router.post("/photo-spots", response_model=PhotoSpotOut)
def create_photo_spot(data: PhotoSpotCreate, db: Session = Depends(get_db)):
    spot = PhotoSpot(**data.model_dump())
    db.add(spot)
    db.commit()
    db.refresh(spot)
    return spot


@router.get("/photo-spots", response_model=List[PhotoSpotOut])
def list_photo_spots(
    hall_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(PhotoSpot)
    if hall_id is not None:
        q = q.filter(PhotoSpot.hall_id == hall_id)
    return q.offset(skip).limit(limit).all()


@router.put("/photo-spots/{spot_id}", response_model=PhotoSpotOut)
def update_photo_spot(spot_id: int, data: PhotoSpotUpdate, db: Session = Depends(get_db)):
    spot = db.query(PhotoSpot).filter(PhotoSpot.id == spot_id).first()
    if not spot:
        raise HTTPException(status_code=404, detail="合影点位不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(spot, key, value)
    db.commit()
    db.refresh(spot)
    return spot


@router.delete("/photo-spots/{spot_id}")
def delete_photo_spot(spot_id: int, db: Session = Depends(get_db)):
    spot = db.query(PhotoSpot).filter(PhotoSpot.id == spot_id).first()
    if not spot:
        raise HTTPException(status_code=404, detail="合影点位不存在")
    db.delete(spot)
    db.commit()
    return {"detail": "已删除"}


@router.post("/photo-records", response_model=PhotoRecordOut)
def create_photo_record(data: PhotoRecordCreate, db: Session = Depends(get_db)):
    record = PhotoRecord(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/photo-records", response_model=List[PhotoRecordOut])
def list_photo_records(
    session_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(PhotoRecord)
    if session_id is not None:
        q = q.filter(PhotoRecord.session_id == session_id)
    return q.offset(skip).limit(limit).all()
