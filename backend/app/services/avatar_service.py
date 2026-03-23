from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from fastapi import UploadFile

from app.config import RUNTIME_DIR, UPLOAD_DIR
from app.schemas import AvatarUploadResponse

USER_AVATAR_KEY = "__user__"
ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg"}


class AvatarService:
    def __init__(self) -> None:
        self.mapping_path = RUNTIME_DIR / "avatar_overrides.json"
        if not self.mapping_path.exists():
            self.mapping_path.write_text("{}", encoding="utf-8")

    def _load_mapping(self) -> dict:
        try:
            data = json.loads(self.mapping_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {}

    def _save_mapping(self, data: dict) -> None:
        self.mapping_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _validate_suffix(self, filename: str) -> str:
        suffix = Path(filename or "").suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise ValueError("仅支持 png / jpg / jpeg / svg")
        return suffix

    def _save_file(self, key: str, file: UploadFile) -> str:
        suffix = self._validate_suffix(file.filename or "")
        filename = f"{key}_{int(time.time())}{suffix}"
        target = UPLOAD_DIR / filename
        with target.open("wb") as fh:
            shutil.copyfileobj(file.file, fh)
        return f"/user-content/uploads/{filename}"

    def resolve_avatar(self, character_id: str, default_avatar: str) -> str:
        data = self._load_mapping()
        return data.get(character_id, default_avatar)

    def resolve_user_avatar(self) -> str:
        data = self._load_mapping()
        return str(data.get(USER_AVATAR_KEY, ""))

    async def save_upload(self, character_id: str, file: UploadFile) -> AvatarUploadResponse:
        avatar_url = self._save_file(character_id, file)
        data = self._load_mapping()
        data[character_id] = avatar_url
        self._save_mapping(data)
        return AvatarUploadResponse(character_id=character_id, avatar_url=avatar_url)

    async def save_user_upload(self, file: UploadFile) -> AvatarUploadResponse:
        avatar_url = self._save_file("user", file)
        data = self._load_mapping()
        data[USER_AVATAR_KEY] = avatar_url
        self._save_mapping(data)
        return AvatarUploadResponse(character_id="user", avatar_url=avatar_url)

    def reset_avatar(self, character_id: str) -> None:
        data = self._load_mapping()
        if character_id in data:
            del data[character_id]
            self._save_mapping(data)

    def reset_user_avatar(self) -> None:
        data = self._load_mapping()
        if USER_AVATAR_KEY in data:
            del data[USER_AVATAR_KEY]
            self._save_mapping(data)
