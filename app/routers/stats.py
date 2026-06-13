from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Hall, VisitorSession, DwellRecord, Favorite, DisconnectRecord
from ..schemas import OnlineCountOut, PopularExhibitOut, DisconnectRecordOut

router = APIRouter(prefix="/api/stats", tags=["数据统计"])


@router.get("/online-count", response_model=List[OnlineCountOut])
def get_online_count(
    hall_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(
        Hall.id.label("hall_id"),
        Hall.name.label("hall_name"),
        func.count(VisitorSession.id).label("online_count"),
    ).outerjoin(
        VisitorSession,
        (VisitorSession.hall_id == Hall.id) & (VisitorSession.is_online == True),
    )

    if hall_id is not None:
        q = q.filter(Hall.id == hall_id)

    rows = q.group_by(Hall.id, Hall.name).all()
    return [
        OnlineCountOut(hall_id=r.hall_id, hall_name=r.hall_name, online_count=r.online_count)
        for r in rows
    ]


@router.get("/popular-exhibits", response_model=List[PopularExhibitOut])
def get_popular_exhibits(
    hall_id: Optional[int] = Query(None),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
):
    dwell_q = db.query(
        DwellRecord.exhibit_id,
        func.sum(DwellRecord.dwell_seconds).label("total_dwell_seconds"),
    ).group_by(DwellRecord.exhibit_id).subquery()

    fav_q = db.query(
        Favorite.exhibit_id,
        func.count(Favorite.id).label("favorite_count"),
    ).group_by(Favorite.exhibit_id).subquery()

    from ..models import Exhibit

    q = (
        db.query(
            Exhibit.id.label("exhibit_id"),
            Exhibit.name.label("exhibit_name"),
            Exhibit.hall_id.label("hall_id"),
            func.coalesce(dwell_q.c.total_dwell_seconds, 0).label("total_dwell_seconds"),
            func.coalesce(fav_q.c.favorite_count, 0).label("favorite_count"),
        )
        .outerjoin(dwell_q, dwell_q.c.exhibit_id == Exhibit.id)
        .outerjoin(fav_q, fav_q.c.exhibit_id == Exhibit.id)
    )

    if hall_id is not None:
        q = q.filter(Exhibit.hall_id == hall_id)

    q = q.order_by(func.coalesce(dwell_q.c.total_dwell_seconds, 0).desc()).limit(limit)
    rows = q.all()
    return [
        PopularExhibitOut(
            exhibit_id=r.exhibit_id,
            exhibit_name=r.exhibit_name,
            hall_id=r.hall_id,
            total_dwell_seconds=r.total_dwell_seconds,
            favorite_count=r.favorite_count,
        )
        for r in rows
    ]


@router.get("/disconnects", response_model=List[DisconnectRecordOut])
def get_disconnect_records(
    hall_id: Optional[int] = Query(None),
    visitor_id: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(DisconnectRecord)
    if hall_id is not None:
        q = q.filter(DisconnectRecord.hall_id == hall_id)
    if visitor_id is not None:
        q = q.filter(DisconnectRecord.visitor_id == visitor_id)
    return q.order_by(DisconnectRecord.disconnected_at.desc()).offset(skip).limit(limit).all()
