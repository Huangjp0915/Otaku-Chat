import json
from pathlib import Path
from typing import Dict, List

from app.config import CHARACTER_DIR
from app.schemas import CharacterCard
from app.services.avatar_service import AvatarService


class CharacterService:
    def __init__(self, character_dir: Path = CHARACTER_DIR) -> None:
        self.character_dir = character_dir
        self.avatar_service = AvatarService()
        self._cache: Dict[str, CharacterCard] = {}
        self.load_all()

    def load_all(self) -> None:
        self._cache.clear()
        for file in sorted(self.character_dir.glob("*.json")):
            data = json.loads(file.read_text(encoding="utf-8"))
            card = CharacterCard(**data)
            self._cache[card.id] = card

    def _with_avatar_override(self, card: CharacterCard) -> CharacterCard:
        avatar = self.avatar_service.resolve_avatar(card.id, card.avatar)
        return card.model_copy(update={"avatar": avatar})

    def list_characters(self) -> List[CharacterCard]:
        return [self._with_avatar_override(card) for card in self._cache.values()]

    def get(self, character_id: str) -> CharacterCard:
        if character_id not in self._cache:
            raise KeyError(f"角色不存在: {character_id}")
        return self._with_avatar_override(self._cache[character_id])