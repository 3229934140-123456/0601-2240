import csv
import io
from datetime import datetime
from typing import Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    VisitorSession,
    DwellRecord,
    Favorite,
    QAResult,
    InteractionRecord,
    PhotoRecord,
    Exhibit,
    PhotoSpot,
    Hotspot,
)

router = APIRouter(prefix="/api/export", tags=["数据导出"])


def _collect_session_ids(db: Session, hall_id: int, start_date: Optional[datetime], end_date: Optional[datetime]):
    q = db.query(VisitorSession).filter(VisitorSession.hall_id == hall_id)
    if start_date:
        q = q.filter(VisitorSession.login_at >= start_date)
    if end_date:
        q = q.filter(VisitorSession.login_at <= end_date)
    sessions = q.order_by(VisitorSession.login_at.desc()).all()
    return sessions


@router.get("/visit-details")
def export_visit_details(
    hall_id: int = Query(...),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    sessions = _collect_session_ids(db, hall_id, start_date, end_date)
    session_ids = [s.id for s in sessions]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "会话ID",
        "访客ID",
        "展厅ID",
        "设备信息",
        "登录时间",
        "登出时间",
        "事件时间",
        "事件类型",
        "事件名称",
        "详情",
    ])

    def _session_rows(s):
        return [
            s.id,
            s.visitor_id,
            s.hall_id,
            s.device_info,
            str(s.login_at),
            str(s.logout_at) if s.logout_at else "",
        ]

    if not session_ids:
        for s in sessions:
            writer.writerow(_session_rows(s) + [str(s.login_at), "enter", "进入展厅", ""])
            if s.logout_at:
                writer.writerow(_session_rows(s) + [str(s.logout_at), "leave", "离开展厅", ""])
        output.seek(0)
        filename = f"visit_details_hall_{hall_id}.csv"
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
        )

    dwells = db.query(DwellRecord).filter(DwellRecord.session_id.in_(session_ids)).all()
    favs = db.query(Favorite).filter(Favorite.session_id.in_(session_ids)).all()
    qas = db.query(QAResult).filter(QAResult.session_id.in_(session_ids)).all()
    interactions = db.query(InteractionRecord).filter(InteractionRecord.session_id.in_(session_ids)).all()
    photos = db.query(PhotoRecord).filter(PhotoRecord.session_id.in_(session_ids)).all()

    exhibit_ids = set()
    for d in dwells:
        exhibit_ids.add(d.exhibit_id)
    for f in favs:
        exhibit_ids.add(f.exhibit_id)
    exhibit_map = {}
    if exhibit_ids:
        for e in db.query(Exhibit).filter(Exhibit.id.in_(exhibit_ids)).all():
            exhibit_map[e.id] = e.name

    hotspot_ids = {i.hotspot_id for i in interactions if i.hotspot_id}
    hotspot_map = {}
    if hotspot_ids:
        for h in db.query(Hotspot).filter(Hotspot.id.in_(hotspot_ids)).all():
            hotspot_map[h.id] = h.name

    photo_spot_ids = {p.photo_spot_id for p in photos}
    photo_spot_map = {}
    if photo_spot_ids:
        for ps in db.query(PhotoSpot).filter(PhotoSpot.id.in_(photo_spot_ids)).all():
            photo_spot_map[ps.id] = ps.name

    session_map = {s.id: s for s in sessions}

    events = []
    for s in sessions:
        events.append((s.login_at, s.id, "enter", "进入展厅", {}))
        if s.logout_at:
            events.append((s.logout_at, s.id, "leave", "离开展厅", {}))

    for d in dwells:
        name = f"停留-{exhibit_map.get(d.exhibit_id, '展品#'+str(d.exhibit_id))}"
        events.append(
            (d.entered_at, d.session_id, "dwell", name, {
                "展品ID": d.exhibit_id,
                "停留秒数": d.dwell_seconds,
            })
        )

    for f in favs:
        name = f"收藏-{exhibit_map.get(f.exhibit_id, '展品#'+str(f.exhibit_id))}"
        events.append(
            (f.created_at, f.session_id, "favorite", name, {"展品ID": f.exhibit_id})
        )

    for q in qas:
        events.append(
            (q.answered_at, q.session_id, "qa", "问答互动", {
                "问题": q.question,
                "答案": q.answer,
                "是否正确": "是" if q.is_correct else "否" if q.is_correct is False else "未判定",
            })
        )

    for i in interactions:
        if i.hotspot_id:
            name = f"热点互动-{hotspot_map.get(i.hotspot_id, '热点#'+str(i.hotspot_id))}"
        else:
            name = f"互动-{i.interaction_type}"
        events.append(
            (i.created_at, i.session_id, "hotspot", name, {
                "类型": i.interaction_type,
                "内容": i.payload,
            })
        )

    for p in photos:
        name = f"合影-{photo_spot_map.get(p.photo_spot_id, '点位#'+str(p.photo_spot_id))}"
        events.append(
            (p.created_at, p.session_id, "photo", name, {
                "点位ID": p.photo_spot_id,
                "图片URL": p.image_url,
            })
        )

    events.sort(key=lambda x: x[0])

    for ev in events:
        etime, sid, etype, ename, detail = ev
        s = session_map.get(sid)
        if not s:
            continue
        writer.writerow(
            _session_rows(s)
            + [str(etime), etype, ename, str(detail)]
        )

    output.seek(0)
    filename = f"visit_details_hall_{hall_id}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )
