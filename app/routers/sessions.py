from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    VisitorSession,
    DisconnectRecord,
    PhotoSpot,
    PhotoRecord,
    Hall,
    DwellRecord,
    Favorite,
    QAResult,
    InteractionRecord,
    Exhibit,
    Hotspot,
)
from ..schemas import (
    SessionCreate,
    SessionOut,
    PhotoSpotCreate,
    PhotoSpotUpdate,
    PhotoSpotOut,
    PhotoRecordCreate,
    PhotoRecordOut,
    SessionTimelineOut,
    TimelineEvent,
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
    return q.order_by(PhotoSpot.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/photo-spots/{spot_id}", response_model=PhotoSpotOut)
def get_photo_spot(spot_id: int, db: Session = Depends(get_db)):
    spot = db.query(PhotoSpot).filter(PhotoSpot.id == spot_id).first()
    if not spot:
        raise HTTPException(status_code=404, detail="合影点位不存在")
    return spot


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
    photo_spot_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(PhotoRecord)
    if session_id is not None:
        q = q.filter(PhotoRecord.session_id == session_id)
    if photo_spot_id is not None:
        q = q.filter(PhotoRecord.photo_spot_id == photo_spot_id)
    return q.order_by(PhotoRecord.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/photo-records/{record_id}", response_model=PhotoRecordOut)
def get_photo_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(PhotoRecord).filter(PhotoRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="合影记录不存在")
    return record


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


@router.get("/{session_id}/timeline", response_model=SessionTimelineOut)
def get_session_timeline(session_id: int, db: Session = Depends(get_db)):
    session = db.query(VisitorSession).filter(VisitorSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    hall = db.query(Hall).filter(Hall.id == session.hall_id).first()
    hall_name = hall.name if hall else ""

    events: List[TimelineEvent] = []

    events.append(TimelineEvent(
        event_time=session.login_at,
        event_type="enter",
        event_name="进入展厅",
        detail={"展厅ID": session.hall_id, "展厅名称": hall_name},
    ))

    dwells = db.query(DwellRecord).filter(DwellRecord.session_id == session_id).all()
    exhibit_ids = {d.exhibit_id for d in dwells}
    favs = db.query(Favorite).filter(Favorite.session_id == session_id).all()
    exhibit_ids |= {f.exhibit_id for f in favs}
    exhibit_map = {}
    if exhibit_ids:
        for e in db.query(Exhibit).filter(Exhibit.id.in_(exhibit_ids)).all():
            exhibit_map[e.id] = e.name

    for d in dwells:
        name = f"查看展品-{exhibit_map.get(d.exhibit_id, '#'+str(d.exhibit_id))}"
        events.append(TimelineEvent(
            event_time=d.entered_at,
            event_type="dwell",
            event_name=name,
            detail={"展品ID": d.exhibit_id, "停留秒数": d.dwell_seconds},
        ))

    for f in favs:
        name = f"收藏展品-{exhibit_map.get(f.exhibit_id, '#'+str(f.exhibit_id))}"
        events.append(TimelineEvent(
            event_time=f.created_at,
            event_type="favorite",
            event_name=name,
            detail={"展品ID": f.exhibit_id},
        ))

    qas = db.query(QAResult).filter(QAResult.session_id == session_id).all()
    for q in qas:
        correct_flag = "正确" if q.is_correct else "错误" if q.is_correct is False else "未判定"
        events.append(TimelineEvent(
            event_time=q.answered_at,
            event_type="qa",
            event_name=f"问答-{correct_flag}",
            detail={"问题": q.question, "答案": q.answer, "是否正确": correct_flag},
        ))

    interactions = db.query(InteractionRecord).filter(InteractionRecord.session_id == session_id).all()
    hotspot_ids = {i.hotspot_id for i in interactions if i.hotspot_id}
    hotspot_map = {}
    if hotspot_ids:
        for h in db.query(Hotspot).filter(Hotspot.id.in_(hotspot_ids)).all():
            hotspot_map[h.id] = h.name

    for i in interactions:
        if i.hotspot_id:
            name = f"热点互动-{hotspot_map.get(i.hotspot_id, '#'+str(i.hotspot_id))}"
        else:
            name = f"互动-{i.interaction_type}"
        events.append(TimelineEvent(
            event_time=i.created_at,
            event_type="hotspot",
            event_name=name,
            detail={"类型": i.interaction_type, "内容": i.payload},
        ))

    photos = db.query(PhotoRecord).filter(PhotoRecord.session_id == session_id).all()
    photo_spot_ids = {p.photo_spot_id for p in photos}
    photo_spot_map = {}
    if photo_spot_ids:
        for ps in db.query(PhotoSpot).filter(PhotoSpot.id.in_(photo_spot_ids)).all():
            photo_spot_map[ps.id] = ps.name

    for p in photos:
        name = f"合影-{photo_spot_map.get(p.photo_spot_id, '#'+str(p.photo_spot_id))}"
        events.append(TimelineEvent(
            event_time=p.created_at,
            event_type="photo",
            event_name=name,
            detail={"点位ID": p.photo_spot_id, "图片URL": p.image_url},
        ))

    disconnect = db.query(DisconnectRecord).filter(DisconnectRecord.session_id == session_id).first()
    if disconnect:
        events.append(TimelineEvent(
            event_time=disconnect.disconnected_at,
            event_type="disconnect",
            event_name="异常掉线",
            detail={"原因": disconnect.reason},
        ))

    if session.logout_at:
        events.append(TimelineEvent(
            event_time=session.logout_at,
            event_type="leave",
            event_name="离开展厅",
            detail={"展厅ID": session.hall_id, "展厅名称": hall_name},
        ))

    events.sort(key=lambda e: e.event_time)

    return SessionTimelineOut(
        session_id=session.id,
        visitor_id=session.visitor_id,
        hall_id=session.hall_id,
        hall_name=hall_name,
        events=events,
    )
