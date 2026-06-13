import csv
import io
from datetime import datetime
from typing import List, Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import EventRegistration
from ..schemas import EventRegistrationCreate, EventRegistrationOut

router = APIRouter(prefix="/api/events", tags=["活动报名"])

_STATUS_LABEL = {
    "registered": "已报名",
    "cancelled": "已取消",
    "checked_in": "已签到",
}


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
    return q.order_by(EventRegistration.registered_at.desc()).offset(skip).limit(limit).all()


@router.put("/registrations/{reg_id}/checkin", response_model=EventRegistrationOut)
def checkin_registration(reg_id: int, db: Session = Depends(get_db)):
    reg = db.query(EventRegistration).filter(EventRegistration.id == reg_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="报名记录不存在")
    if reg.status == "cancelled":
        raise HTTPException(status_code=400, detail="已取消报名，无法签到")
    reg.status = "checked_in"
    reg.checked_in_at = datetime.utcnow()
    db.commit()
    db.refresh(reg)
    return reg


@router.put("/registrations/{reg_id}/cancel", response_model=EventRegistrationOut)
def cancel_registration(reg_id: int, db: Session = Depends(get_db)):
    reg = db.query(EventRegistration).filter(EventRegistration.id == reg_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="报名记录不存在")
    reg.status = "cancelled"
    db.commit()
    db.refresh(reg)
    return reg


@router.get("/export/attendance")
def export_attendance(
    event_name: str = Query(...),
    hall_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(EventRegistration).filter(EventRegistration.event_name == event_name)
    if hall_id is not None:
        q = q.filter(EventRegistration.hall_id == hall_id)
    regs = q.order_by(EventRegistration.registered_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "报名ID",
        "活动名称",
        "展厅ID",
        "访客ID",
        "访客姓名",
        "联系电话",
        "状态",
        "状态说明",
        "报名时间",
        "签到时间",
    ])

    for r in regs:
        writer.writerow([
            r.id,
            r.event_name,
            r.hall_id,
            r.visitor_id,
            r.visitor_name,
            r.visitor_phone,
            r.status,
            _STATUS_LABEL.get(r.status, r.status),
            str(r.registered_at),
            str(r.checked_in_at) if r.checked_in_at else "",
        ])

    output.seek(0)
    safe_name = quote(event_name)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''attendance_{safe_name}.csv"},
    )
