from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import EventRegistration
from ..schemas import EventRegistrationCreate, EventRegistrationOut

router = APIRouter(prefix="/api/events", tags=["活动报名"])


@router.post("/register", response_model=EventRegistrationOut)
def register_event(data: EventRegistrationCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(EventRegistration)
        .filter(
            EventRegistration.event_name == data.event_name,
            EventRegistration.visitor_id == data.visitor_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="已报名该活动")
    reg = EventRegistration(**data.model_dump())
    db.add(reg)
    db.commit()
    db.refresh(reg)
    return reg


@router.get("/registrations", response_model=List[EventRegistrationOut])
def list_registrations(
    event_name: Optional[str] = Query(None),
    hall_id: Optional[int] = Query(None),
    visitor_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(EventRegistration)
    if event_name is not None:
        q = q.filter(EventRegistration.event_name == event_name)
    if hall_id is not None:
        q = q.filter(EventRegistration.hall_id == hall_id)
    if visitor_id is not None:
        q = q.filter(EventRegistration.visitor_id == visitor_id)
    if status is not None:
        q = q.filter(EventRegistration.status == status)
    return q.offset(skip).limit(limit).all()


@router.put("/registrations/{reg_id}/cancel")
def cancel_registration(reg_id: int, db: Session = Depends(get_db)):
    reg = db.query(EventRegistration).filter(EventRegistration.id == reg_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="报名记录不存在")
    reg.status = "cancelled"
    db.commit()
    return {"detail": "已取消报名"}
