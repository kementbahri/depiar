import json
import os
from typing import Dict, Any
from fastapi import Request
from fastapi.responses import JSONResponse

class I18n:
    def __init__(self):
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.default_language = "tr"
        self.load_translations()

    def load_translations(self):
        """Dil dosyalarını yükle"""
        locales_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")
        for filename in os.listdir(locales_dir):
            if filename.endswith(".json"):
                language = filename.split(".")[0]
                with open(os.path.join(locales_dir, filename), "r", encoding="utf-8") as f:
                    self.translations[language] = json.load(f)

    def get_translation(self, key: str, language: str = None) -> str:
        """Belirtilen anahtar için çeviriyi getir"""
        if not language:
            language = self.default_language

        if language not in self.translations:
            language = self.default_language

        keys = key.split(".")
        translation = self.translations[language]

        for k in keys:
            if isinstance(translation, dict) and k in translation:
                translation = translation[k]
            else:
                return key

        return translation if isinstance(translation, str) else key

    def get_language_from_request(self, request: Request) -> str:
        """İstekten dil bilgisini al"""
        # Önce cookie'den kontrol et
        language = request.cookies.get("language")
        if language and language in self.translations:
            return language

        # Sonra Accept-Language header'ından kontrol et
        accept_language = request.headers.get("accept-language", "")
        if accept_language:
            preferred_language = accept_language.split(",")[0].split("-")[0]
            if preferred_language in self.translations:
                return preferred_language

        return self.default_language

    def set_language_cookie(self, response: JSONResponse, language: str):
        """Dil tercihini cookie olarak ayarla"""
        response.set_cookie(
            key="language",
            value=language,
            max_age=365 * 24 * 60 * 60,  # 1 yıl
            httponly=True,
            samesite="lax"
        )

# Global i18n instance
i18n = I18n()

def get_translation(key: str, language: str = None) -> str:
    """Global çeviri fonksiyonu"""
    return i18n.get_translation(key, language)

def get_language_from_request(request: Request) -> str:
    """Global dil alma fonksiyonu"""
    return i18n.get_language_from_request(request)

def set_language_cookie(response: JSONResponse, language: str):
    """Global dil ayarlama fonksiyonu"""
    i18n.set_language_cookie(response, language) 