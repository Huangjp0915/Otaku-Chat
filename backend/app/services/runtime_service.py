from __future__ import annotations

import json

from app.config import RUNTIME_DIR, settings


class RuntimeService:
    def __init__(self) -> None:
        self.path = RUNTIME_DIR / "runtime_settings.json"
        if not self.path.exists():
            self.save(self._defaults())

    def _defaults(self) -> dict:
        return {
            "llm_mode": settings.llm_mode,
            "ollama_model": settings.ollama_model,
            "send_shortcut": "enter",
            "detail_panel_default_open": False,
            "auto_check_interval_seconds": 20,
        }

    def load(self) -> dict:
        data = self._defaults()
        if self.path.exists():
            try:
                stored = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(stored, dict):
                    data.update(stored)
            except Exception:
                pass
        return data

    def save(self, data: dict) -> None:
        safe = self._defaults()
        safe.update({k: v for k, v in data.items() if v is not None})
        self.path.write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")

    def update(
        self,
        llm_mode: str | None = None,
        ollama_model: str | None = None,
        send_shortcut: str | None = None,
        detail_panel_default_open: bool | None = None,
        auto_check_interval_seconds: int | None = None,
    ) -> dict:
        data = self.load()
        if llm_mode is not None:
            data["llm_mode"] = llm_mode
        if ollama_model is not None:
            data["ollama_model"] = ollama_model
        if send_shortcut is not None:
            data["send_shortcut"] = send_shortcut
        if detail_panel_default_open is not None:
            data["detail_panel_default_open"] = bool(detail_panel_default_open)
        if auto_check_interval_seconds is not None:
            data["auto_check_interval_seconds"] = max(5, min(int(auto_check_interval_seconds), 600))
        self.save(data)
        return data

    def get_llm_mode(self) -> str:
        return str(self.load().get("llm_mode", settings.llm_mode))

    def get_ollama_model(self) -> str:
        return str(self.load().get("ollama_model", settings.ollama_model))
