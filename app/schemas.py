from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class HallCreate(BaseModel):
    name: str
    description: str = ""
    capacity: int = 100
    scene_config: str = ""
    cover_image: str = ""
    status: str = "draft"


class HallUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    capacity: Optional[int] = None
    scene_config: Optional[str] = None
    cover_image: Optional[str] = None
    status: Optional[str] = None


class HallOut(BaseModel):
    id: int
    name: str
    description: str
    capacity: int
    scene_config: str
    cover_image: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExhibitCreate(BaseModel):
    hall_id: int
    name: str
    description: str = ""
    category: str = ""
    model_url: str = ""
    image_url: str = ""
    audio_url: str = ""
    narration_text: str = ""
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0
    is_published: bool = False
    sort_order: int = 0


class ExhibitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    model_url: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    narration_text: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_z: Optional[float] = None
    is_published: Optional[bool] = None
    sort_order: Optional[int] = None


class ExhibitOut(BaseModel):
    id: int
    hall_id: int
    name: str
    description: str
    category: str
    model_url: str
    image_url: str
    audio_url: str
    narration_text: str
    position_x: float
    position_y: float
    position_z: float
    is_published: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CharacterCreate(BaseModel):
    hall_id: Optional[int] = None
    name: str
    avatar_url: str = ""
    model_url: str = ""
    role: str = "guide"
    greeting: str = ""
    voice_config: str = ""
    is_active: bool = True


class CharacterUpdate(BaseModel):
    hall_id: Optional[int] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    model_url: Optional[str] = None
    role: Optional[str] = None
    greeting: Optional[str] = None
    voice_config: Optional[str] = None
    is_active: Optional[bool] = None


class CharacterOut(BaseModel):
    id: int
    hall_id: Optional[int]
    name: str
    avatar_url: str
    model_url: str
    role: str
    greeting: str
    voice_config: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RouteCreate(BaseModel):
    hall_id: int
    name: str
    description: str = ""
    waypoints: str = ""
    duration_minutes: int = 30
    difficulty: str = "easy"
    is_published: bool = False


class RouteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    waypoints: Optional[str] = None
    duration_minutes: Optional[int] = None
    difficulty: Optional[str] = None
    is_published: Optional[bool] = None


class RouteOut(BaseModel):
    id: int
    hall_id: int
    name: str
    description: str
    waypoints: str
    duration_minutes: int
    difficulty: str
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HotspotCreate(BaseModel):
    hall_id: int
    exhibit_id: Optional[int] = None
    name: str
    hotspot_type: str = "info"
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0
    interaction_config: str = ""
    is_active: bool = True


class HotspotUpdate(BaseModel):
    name: Optional[str] = None
    hotspot_type: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_z: Optional[float] = None
    interaction_config: Optional[str] = None
    is_active: Optional[bool] = None


class HotspotOut(BaseModel):
    id: int
    hall_id: int
    exhibit_id: Optional[int]
    name: str
    hotspot_type: str
    position_x: float
    position_y: float
    position_z: float
    interaction_config: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PhotoSpotCreate(BaseModel):
    hall_id: int
    name: str
    description: str = ""
    camera_position: str = ""
    camera_rotation: str = ""
    background_template: str = ""
    is_active: bool = True


class PhotoSpotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    camera_position: Optional[str] = None
    camera_rotation: Optional[str] = None
    background_template: Optional[str] = None
    is_active: Optional[bool] = None


class PhotoSpotOut(BaseModel):
    id: int
    hall_id: int
    name: str
    description: str
    camera_position: str
    camera_rotation: str
    background_template: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionCreate(BaseModel):
    visitor_id: str
    hall_id: int
    character_id: Optional[int] = None
    route_id: Optional[int] = None
    device_info: str = ""


class SessionOut(BaseModel):
    id: int
    visitor_id: str
    hall_id: int
    character_id: Optional[int]
    route_id: Optional[int]
    device_info: str
    is_online: bool
    login_at: datetime
    logout_at: Optional[datetime]

    model_config = {"from_attributes": True}


class DwellRecordCreate(BaseModel):
    session_id: int
    exhibit_id: int
    dwell_seconds: int = 0
    entered_at: Optional[datetime] = None
    left_at: Optional[datetime] = None


class DwellRecordOut(BaseModel):
    id: int
    session_id: int
    exhibit_id: int
    dwell_seconds: int
    entered_at: datetime
    left_at: Optional[datetime]

    model_config = {"from_attributes": True}


class FavoriteCreate(BaseModel):
    session_id: int
    exhibit_id: int


class FavoriteOut(BaseModel):
    id: int
    session_id: int
    exhibit_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class QAResultCreate(BaseModel):
    session_id: int
    question: str
    answer: str = ""
    is_correct: Optional[bool] = None


class QAResultOut(BaseModel):
    id: int
    session_id: int
    question: str
    answer: str
    is_correct: Optional[bool]
    answered_at: datetime

    model_config = {"from_attributes": True}


class InteractionCreate(BaseModel):
    session_id: int
    hotspot_id: Optional[int] = None
    interaction_type: str
    payload: str = ""


class InteractionOut(BaseModel):
    id: int
    session_id: int
    hotspot_id: Optional[int]
    interaction_type: str
    payload: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PhotoRecordCreate(BaseModel):
    session_id: int
    photo_spot_id: int
    image_url: str = ""


class PhotoRecordOut(BaseModel):
    id: int
    session_id: int
    photo_spot_id: int
    image_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EventRegistrationCreate(BaseModel):
    event_name: str
    hall_id: int
    visitor_id: str
    visitor_name: str = ""
    visitor_phone: str = ""


class EventRegistrationOut(BaseModel):
    id: int
    event_name: str
    hall_id: int
    visitor_id: str
    visitor_name: str
    visitor_phone: str
    status: str
    registered_at: datetime
    checked_in_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DisconnectRecordOut(BaseModel):
    id: int
    session_id: int
    visitor_id: str
    hall_id: int
    reason: str
    disconnected_at: datetime

    model_config = {"from_attributes": True}


class OnlineCountOut(BaseModel):
    hall_id: int
    hall_name: str
    online_count: int


class PopularExhibitOut(BaseModel):
    exhibit_id: int
    exhibit_name: str
    hall_id: int
    total_dwell_seconds: int
    favorite_count: int


class HallOverviewOut(BaseModel):
    hall_id: int
    hall_name: str
    time_range: str
    online_count: int
    total_visits: int
    avg_dwell_seconds: float
    total_favorites: int
    qa_correct_rate: Optional[float]
    total_registrations: int


class TimelineEvent(BaseModel):
    event_time: datetime
    event_type: str
    event_name: str
    detail: dict = {}


class SessionTimelineOut(BaseModel):
    session_id: int
    visitor_id: str
    hall_id: int
    hall_name: str
    events: List[TimelineEvent]

