from datetime import datetime, timedelta
from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Hall,
    VisitorSession,
    DwellRecord,
    Favorite,
    DisconnectRecord,
    Exhibit,
    QAResult,
    EventRegistration,
)
from ..schemas import OnlineCountOut, PopularExhibitOut, DisconnectRecordOut, HallOverviewOut

router = APIRouter(prefix="/api/stats", tags=["数据统计"])


def _time_range_bounds(time_range: Literal["today", "7d", "custom"], start_date, end_date):
    now = datetime.utcnow()
    if time_range == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        label = f"{start.date()} 至今"
    elif time_range == "7d":
        start = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        label = f"{start.date()} ~ {now.date()}"
    else:
        start = start_date or (now - timedelta(days=30))
        end = end_date or now
        label = f"{start.date()} ~ {end.date()}"
    return start, end, label


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


@router.get("/hall-overview", response_model=List[HallOverviewOut])
def get_hall_overview(
    hall_id: Optional[int] = Query(None),
    time_range: Literal["today", "7d", "custom"] = Query("today"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    start, end, label = _time_range_bounds(time_range, start_date, end_date)

    halls_q = db.query(Hall)
    if hall_id is not None:
        halls_q = halls_q.filter(Hall.id == hall_id)
    halls = halls_q.all()

    result = []
    for hall in halls:
        online_count = (
            db.query(func.count(VisitorSession.id))
            .filter(
                VisitorSession.hall_id == hall.id,
                VisitorSession.is_online == True,
            )
            .scalar()
            or 0
        )

        sessions_in_range = (
            db.query(VisitorSession)
            .filter(
                VisitorSession.hall_id == hall.id,
                VisitorSession.login_at >= start,
                VisitorSession.login_at <= end,
            )
        )
        session_ids = [s.id for s in sessions_in_range.all()]
        total_visits = len(session_ids)

        if session_ids:
            total_dwell = (
                db.query(func.coalesce(func.sum(DwellRecord.dwell_seconds), 0))
                .filter(DwellRecord.session_id.in_(session_ids))
                .scalar()
                or 0
            )
            avg_dwell = total_dwell / len(session_ids) if session_ids else 0.0

            total_favorites = (
                db.query(func.count(Favorite.id))
                .filter(Favorite.session_id.in_(session_ids))
                .scalar()
                or 0
            )

            qa_total = (
                db.query(func.count(QAResult.id))
                .filter(QAResult.session_id.in_(session_ids), QAResult.is_correct.isnot(None))
                .scalar()
                or 0
            )
            qa_correct = (
                db.query(func.count(QAResult.id))
                .filter(QAResult.session_id.in_(session_ids), QAResult.is_correct == True)
                .scalar()
                or 0
            )
            qa_rate = (qa_correct / qa_total) if qa_total > 0 else None
        else:
            avg_dwell = 0.0
            total_favorites = 0
            qa_rate = None

        total_registrations = (
            db.query(func.count(EventRegistration.id))
            .filter(
                EventRegistration.hall_id == hall.id,
                EventRegistration.registered_at >= start,
                EventRegistration.registered_at <= end,
            )
            .scalar()
            or 0
        )

        result.append(
            HallOverviewOut(
                hall_id=hall.id,
                hall_name=hall.name,
                time_range=label,
                online_count=online_count,
                total_visits=total_visits,
                avg_dwell_seconds=float(avg_dwell),
                total_favorites=total_favorites,
                qa_correct_rate=qa_rate,
                total_registrations=total_registrations,
            )
        )

    return result
