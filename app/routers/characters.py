from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import VirtualCharacter
from ..schemas import CharacterCreate, CharacterUpdate, CharacterOut

router = APIRouter(prefix="/api/characters", tags=["虚拟角色"])


@router.post("", response_model=CharacterOut)
def create_character(data: CharacterCreate, db: Session = Depends(get_db)):
    character = VirtualCharacter(**data.model_dump())
    db.add(character)
    db.commit()
    db.refresh(character)
    return character


@router.get("", response_model=List[CharacterOut])
def list_characters(
    hall_id: Optional[int] = Query(None),
    role: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(VirtualCharacter)
    if hall_id is not None:
        q = q.filter(VirtualCharacter.hall_id == hall_id)
    if role is not None:
        q = q.filter(VirtualCharacter.role == role)
    return q.offset(skip).limit(limit).all()


@router.get("/{character_id}", response_model=CharacterOut)
def get_character(character_id: int, db: Session = Depends(get_db)):
    character = db.query(VirtualCharacter).filter(VirtualCharacter.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="虚拟角色不存在")
    return character


@router.put("/{character_id}", response_model=CharacterOut)
def update_character(character_id: int, data: CharacterUpdate, db: Session = Depends(get_db)):
    character = db.query(VirtualCharacter).filter(VirtualCharacter.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="虚拟角色不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(character, key, value)
    db.commit()
    db.refresh(character)
    return character


@router.delete("/{character_id}")
def delete_character(character_id: int, db: Session = Depends(get_db)):
    character = db.query(VirtualCharacter).filter(VirtualCharacter.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="虚拟角色不存在")
    db.delete(character)
    db.commit()
    return {"detail": "已删除"}
