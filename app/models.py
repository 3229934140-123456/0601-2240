from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from .database import Base


class Hall(Base):
    __tablename__ = "halls"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    capacity = Column(Integer, default=100)
    scene_config = Column(Text, default="")
    cover_image = Column(String(500), default="")
    status = Column(String(20), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    exhibits = relationship("Exhibit", back_populates="hall")
    routes = relationship("TourRoute", back_populates="hall")
    hotspots = relationship("Hotspot", back_populates="hall")
    photo_spots = relationship("PhotoSpot", back_populates="hall")


class Exhibit(Base):
    __tablename__ = "exhibits"

    id = Column(Integer, primary_key=True, index=True)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    category = Column(String(100), default="")
    model_url = Column(String(500), default="")
    image_url = Column(String(500), default="")
    audio_url = Column(String(500), default="")
    narration_text = Column(Text, default="")
    position_x = Column(Float, default=0.0)
    position_y = Column(Float, default=0.0)
    position_z = Column(Float, default=0.0)
    is_published = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hall = relationship("Hall", back_populates="exhibits")
    dwell_records = relationship("DwellRecord", back_populates="exhibit")
    favorites = relationship("Favorite", back_populates="exhibit")


class VirtualCharacter(Base):
    __tablename__ = "virtual_characters"

    id = Column(Integer, primary_key=True, index=True)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=True)
    name = Column(String(200), nullable=False)
    avatar_url = Column(String(500), default="")
    model_url = Column(String(500), default="")
    role = Column(String(100), default="guide")
    greeting = Column(Text, default="")
    voice_config = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TourRoute(Base):
    __tablename__ = "tour_routes"

    id = Column(Integer, primary_key=True, index=True)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    waypoints = Column(Text, default="")
    duration_minutes = Column(Integer, default=30)
    difficulty = Column(String(20), default="easy")
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hall = relationship("Hall", back_populates="routes")


class Hotspot(Base):
    __tablename__ = "hotspots"

    id = Column(Integer, primary_key=True, index=True)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=False)
    exhibit_id = Column(Integer, ForeignKey("exhibits.id"), nullable=True)
    name = Column(String(200), nullable=False)
    hotspot_type = Column(String(50), default="info")
    position_x = Column(Float, default=0.0)
    position_y = Column(Float, default=0.0)
    position_z = Column(Float, default=0.0)
    interaction_config = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    hall = relationship("Hall", back_populates="hotspots")


class PhotoSpot(Base):
    __tablename__ = "photo_spots"

    id = Column(Integer, primary_key=True, index=True)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    camera_position = Column(Text, default="")
    camera_rotation = Column(Text, default="")
    background_template = Column(String(500), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    hall = relationship("Hall", back_populates="photo_spots")


class VisitorSession(Base):
    __tablename__ = "visitor_sessions"

    id = Column(Integer, primary_key=True, index=True)
    visitor_id = Column(String(200), nullable=False, index=True)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("virtual_characters.id"), nullable=True)
    route_id = Column(Integer, ForeignKey("tour_routes.id"), nullable=True)
    device_info = Column(Text, default="")
    is_online = Column(Boolean, default=True)
    login_at = Column(DateTime, default=datetime.utcnow)
    logout_at = Column(DateTime, nullable=True)

    dwell_records = relationship("DwellRecord", back_populates="session")
    favorites = relationship("Favorite", back_populates="session")
    qa_results = relationship("QAResult", back_populates="session")
    interactions = relationship("InteractionRecord", back_populates="session")
    photo_records = relationship("PhotoRecord", back_populates="session")


class DwellRecord(Base):
    __tablename__ = "dwell_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("visitor_sessions.id"), nullable=False)
    exhibit_id = Column(Integer, ForeignKey("exhibits.id"), nullable=False)
    dwell_seconds = Column(Integer, default=0)
    entered_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)

    session = relationship("VisitorSession", back_populates="dwell_records")
    exhibit = relationship("Exhibit", back_populates="dwell_records")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("visitor_sessions.id"), nullable=False)
    exhibit_id = Column(Integer, ForeignKey("exhibits.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("VisitorSession", back_populates="favorites")
    exhibit = relationship("Exhibit", back_populates="favorites")


class QAResult(Base):
    __tablename__ = "qa_results"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("visitor_sessions.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, default="")
    is_correct = Column(Boolean, default=None)
    answered_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("VisitorSession", back_populates="qa_results")


class InteractionRecord(Base):
    __tablename__ = "interaction_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("visitor_sessions.id"), nullable=False)
    hotspot_id = Column(Integer, ForeignKey("hotspots.id"), nullable=True)
    interaction_type = Column(String(50), nullable=False)
    payload = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("VisitorSession", back_populates="interactions")


class PhotoRecord(Base):
    __tablename__ = "photo_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("visitor_sessions.id"), nullable=False)
    photo_spot_id = Column(Integer, ForeignKey("photo_spots.id"), nullable=False)
    image_url = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("VisitorSession", back_populates="photo_records")


class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String(200), nullable=False)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=False)
    visitor_id = Column(String(200), nullable=False, index=True)
    visitor_name = Column(String(200), default="")
    visitor_phone = Column(String(50), default="")
    status = Column(String(20), default="registered")
    registered_at = Column(DateTime, default=datetime.utcnow)
    checked_in_at = Column(DateTime, nullable=True)


class DisconnectRecord(Base):
    __tablename__ = "disconnect_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("visitor_sessions.id"), nullable=False)
    visitor_id = Column(String(200), nullable=False)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=False)
    reason = Column(String(200), default="unknown")
    disconnected_at = Column(DateTime, default=datetime.utcnow)
