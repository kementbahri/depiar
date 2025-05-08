from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List
from ..utils.i18n import get_translation, get_language_from_request, set_language_cookie
from ..models import User
from ..auth import get_current_user

router = APIRouter()

@router.post("/language/{language}")
async def change_language(
    language: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Dil tercihini değiştir"""
    if language not in ["tr", "en"]:
        raise HTTPException(status_code=400, detail=get_translation("settings.invalid_language"))
    
    response = JSONResponse(content={
        "message": get_translation("settings.language_changed"),
        "language": language
    })
    
    set_language_cookie(response, language)
    return response

@router.get("/available-languages")
async def get_available_languages():
    """Kullanılabilir dilleri listele"""
    return {
        "languages": [
            {"code": "tr", "name": "Türkçe"},
            {"code": "en", "name": "English"}
        ]
    } 