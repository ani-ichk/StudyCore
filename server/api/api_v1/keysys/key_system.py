from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

router = APIRouter(prefix="/key_system", tags=["Ключница"])


keys_db: Dict[str, dict] = {
    "key_101": {"id": "key_101", "room": "Кабинет 101", "available": True},
    "key_102": {"id": "key_102", "room": "Кабинет 102", "available": True},
    "key_gym": {"id": "key_gym", "room": "Спортзал", "available": True},
    "key_lib": {"id": "key_lib", "room": "Библиотека", "available": False},
}

active_issuances: Dict[str, dict] = {}
issuance_history: List[dict] = []
allowed_roles = ["администратор", "завуч", "охранник", "учитель"]

class KeyInfo(BaseModel):
    id: str
    room: str
    available: bool

class KeyIssueRequest(BaseModel):
    user_id: str
    user_role: str
    key_id: str

class KeyReturnRequest(BaseModel):
    user_id: str
    key_id: str

@router.get("/keys", response_model=List[KeyInfo])
def list_keys():
    return [KeyInfo(**key) for key in keys_db.values()]

@router.get("/keys/available", response_model=List[KeyInfo])
def list_available_keys():
    return [KeyInfo(**key) for key in keys_db.values() if key["available"]]

@router.post("/issue")
def issue_key(request: KeyIssueRequest):
    if request.user_role not in allowed_roles:
        raise HTTPException(status_code=403, detail="У вас нет прав брать ключи")
    
    key = keys_db.get(request.key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Ключ не найден")
    if not key["available"]:
        raise HTTPException(status_code=400, detail="Ключ уже выдан")
    
    key["available"] = False
    now = datetime.now()
    
    record = {
        "key_id": request.key_id,
        "room": key["room"],
        "taken_by": request.user_id,
        "taken_at": now,
        "returned_at": None,
    }
    active_issuances[request.key_id] = record
    issuance_history.append(record)
    
    return {"status": "success", "message": f"Ключ от {key['room']} выдан", "issued_at": now}

@router.post("/return")
def return_key(request: KeyReturnRequest):
    key = keys_db.get(request.key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Ключ не найден")
    if key["available"]:
        raise HTTPException(status_code=400, detail="Ключ не был выдан")
    
    key["available"] = True
    
    if request.key_id in active_issuances:
        active_issuances[request.key_id]["returned_at"] = datetime.now()
        del active_issuances[request.key_id]
    
    for record in issuance_history:
        if record["key_id"] == request.key_id and record["returned_at"] is None:
            record["returned_at"] = datetime.now()
            break
    
    return {"status": "success", "message": f"Ключ от {key['room']} возвращён"}

@router.get("/history")
def get_history():
    return issuance_history

@router.get("/active")
def get_active_issuances():
    return list(active_issuances.values())
