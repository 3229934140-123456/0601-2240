import csv
import io
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import VisitorSession, DwellRecord, Favorite, QAResult, InteractionRecord, Exhibit

router = APIRouter(prefix="/api/export", tags=["数据导出"])


@router.get("/visit-details")
def export_visit_details(
    hall_id: int = Query(...),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            VisitorSession.id.label("session_id"),
            VisitorSession.visitor_id,
            VisitorSession.hall_id,
            VisitorSession.device_info,
            VisitorSession.login_at,
            VisitorSession.logout_at,
        )
        .filter(VisitorSession.hall_id == hall_id)
    )

    if start_date:
        q = q.filter(VisitorSession.login_at >= start_date)
    if end_date:
        q = q.filter(VisitorSession.login_at <= end_date)

    sessions = q.order_by(VisitorSession.login_at.desc()).all()

    session_ids = [s.session_id for s in sessions]
    if not session_ids:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["会话ID", "访客ID", "展厅ID", "设备信息", "登录时间", "登出时间", "展品名称", "停留秒数", "是否收藏", "互动类型"])
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=visit_details_hall_{hall_id}.csv"},
        )

    dwell_map = {}
    dwells = db.query(DwellRecord).filter(DwellRecord.session_id.in_(session_ids)).all()
    for d in dwells:
        dwell_map.setdefault(d.session_id, []).append(d)

    fav_set = set()
    favs = db.query(Favorite).filter(Favorite.session_id.in_(session_ids)).all()
    for f in favs:
        fav_set.add((f.session_id, f.exhibit_id))

    interact_map = {}
    interactions = db.query(InteractionRecord).filter(InteractionRecord.session_id.in_(session_ids)).all()
    for i in interactions:
        interact_map.setdefault(i.session_id, []).append(i)

    exhibit_names = {}
    exhibit_ids = set()
    for dwells_list in dwell_map.values():
        for d in dwells_list:
            exhibit_ids.add(d.exhibit_id)
    for f in favs:
        exhibit_ids.add(f.exhibit_id)
    if exhibit_ids:
        exhibits = db.query(Exhibit).filter(Exhibit.id.in_(exhibit_ids)).all()
        for e in exhibits:
            exhibit_names[e.id] = e.name

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["会话ID", "访客ID", "展厅ID", "设备信息", "登录时间", "登出时间", "展品名称", "停留秒数", "是否收藏", "互动类型"])

    for s in sessions:
        session_dwell = dwell_map.get(s.session_id, [])
        session_interact = interact_map.get(s.session_id, [])
        interact_types = ";".join({i.interaction_type for i in session_interact})

        if session_dwell:
            for d in session_dwell:
                is_fav = "是" if (s.session_id, d.exhibit_id) in fav_set else "否"
                writer.writerow([
                    s.session_id,
                    s.visitor_id,
                    s.hall_id,
                    s.device_info,
                    str(s.login_at),
                    str(s.logout_at) if s.logout_at else "",
                    exhibit_names.get(d.exhibit_id, ""),
                    d.dwell_seconds,
                    is_fav,
                    interact_types,
                ])
        else:
            writer.writerow([
                s.session_id,
                s.visitor_id,
                s.hall_id,
                s.device_info,
                str(s.login_at),
                str(s.logout_at) if s.logout_at else "",
                "",
                "",
                "",
                interact_types,
            ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=visit_details_hall_{hall_id}.csv"},
    )
