from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from app.config import RUNTIME_DIR
from app.schemas import MomentComment, MomentFeedItem, StoredMoment
from app.services.character_service import CharacterService
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.services.prompt_service import PromptService
from app.services.special_date_service import SpecialDateService


class MomentService:
    def __init__(self, data_path: Path | None = None) -> None:
        self.data_path = data_path or (RUNTIME_DIR / "moments.json")
        self.character_service = CharacterService()
        self.memory_service = MemoryService()
        self.prompt_service = PromptService()
        self.llm_service = LLMService()
        self.special_date_service = SpecialDateService()
        self.data_path.parent.mkdir(parents=True, exist_ok=True)

    def _seed_records(self) -> list[StoredMoment]:
        return [
            StoredMoment(
                id="moment_rem_001",
                character_id="rem",
                content="今天把房间重新整理了一遍。明明只是日常的小事，但收拾整齐以后，心也会跟着安静下来呢。",
                created_at="2026-03-20T21:15:00",
                relationship_phase_hint="stranger",
                topic_refs=["日常", "整理"],
            ),
            StoredMoment(
                id="moment_rem_002",
                character_id="rem",
                content="如果一个人最近总说自己很累，那大概不是在抱怨，只是希望有人能听见吧。",
                created_at="2026-03-22T22:10:00",
                relationship_phase_hint="familiar",
                topic_refs=["关心", "情绪"],
            ),
            StoredMoment(
                id="moment_misaka_001",
                character_id="misaka_mikoto",
                content="自动贩卖机又吞硬币了，气死我了。明明只是想买个饮料，为什么每次都像在打架一样啊……",
                created_at="2026-03-21T18:40:00",
                relationship_phase_hint="stranger",
                topic_refs=["日常", "吐槽"],
            ),
            StoredMoment(
                id="moment_misaka_002",
                character_id="misaka_mikoto",
                content="有些人明明嘴上说没事，脸上却写得特别明显。……算了，真有事的话还是早点说出来比较好吧。",
                created_at="2026-03-22T20:25:00",
                relationship_phase_hint="familiar",
                topic_refs=["关心", "嘴硬"],
            ),
            StoredMoment(
                id="moment_chika_001",
                character_id="fujiwara_chika",
                content="今天突然超级想吃点甜的！认真工作之后就应该认真奖励自己，这才是健康又积极的人生节奏呀！",
                created_at="2026-03-21T16:30:00",
                relationship_phase_hint="stranger",
                topic_refs=["日常", "甜点"],
            ),
            StoredMoment(
                id="moment_chika_002",
                character_id="fujiwara_chika",
                content="聊天最有意思的地方就是——本来只是随口一说，结果最后会变成只属于两个人的暗号！这种感觉超棒的！",
                created_at="2026-03-23T10:00:00",
                relationship_phase_hint="close",
                topic_refs=["关系", "聊天"],
            ),
        ]

    def _load_records(self) -> list[StoredMoment]:
        if not self.data_path.exists():
            self._save_records(self._seed_records())
        raw = json.loads(self.data_path.read_text(encoding="utf-8"))
        return [StoredMoment(**item) for item in raw]

    def _save_records(self, records: list[StoredMoment]) -> None:
        payload = [item.model_dump() for item in records]
        self.data_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _last_moment_time(self, records: list[StoredMoment], character_id: str) -> datetime | None:
        values = [item.created_at for item in records if item.character_id == character_id]
        if not values:
            return None
        try:
            return max(datetime.fromisoformat(item) for item in values)
        except Exception:
            return None

    def _pick_related_topics(self, state, character) -> list[str]:
        topics: list[str] = []

        if getattr(state, "relationship_memory", None):
            topics.extend(state.relationship_memory.recent_topics or [])

        if getattr(state, "user_impression", None):
            topics.extend(state.user_impression.likes or [])

        topics.extend(character.moment_topics or [])
        topics = [item.strip() for item in topics if isinstance(item, str) and item.strip()]
        return list(dict.fromkeys(topics))[:4]

    def _should_generate_moment(self, state, last_moment_at: datetime | None, has_special_event: bool) -> bool:
        if has_special_event:
            return True

        now = datetime.now()
        if last_moment_at and (now - last_moment_at) < timedelta(hours=14):
            return False

        phase_base = {
            "stranger": 0.08,
            "familiar": 0.16,
            "close": 0.26,
        }.get(state.relationship_phase, 0.12)

        if state.relationship_momentum > 0:
            phase_base += min(0.12, state.relationship_momentum * 0.01)

        if last_moment_at and (now - last_moment_at) > timedelta(hours=24):
            phase_base += 0.12

        return random.random() < min(0.55, phase_base)
    
    def generate_due_moments_for_all(self, user_id: str) -> None:
        records = self._load_records()
        changed = False

        for character in self.character_service.list_characters():
            state = self.memory_service.load(user_id, character.id)
            if not state.is_friend:
                continue

            today_events = self.special_date_service.list_today_events(character, state)
            event_for_moment = next(
                (
                    item for item in today_events
                    if not self.special_date_service.has_sent(state, f"moment:{item.event_key}")
                ),
                None,
            )

            last_moment_at = self._last_moment_time(records, character.id)
            if not self._should_generate_moment(state, last_moment_at, has_special_event=bool(event_for_moment)):
                continue

            related_topics = self._pick_related_topics(state, character)
            prompt_hint = event_for_moment.prompt_hint if event_for_moment else (related_topics[0] if related_topics else "最近的小事")
            moment_type = "festival" if event_for_moment else "chat_linked" if related_topics else "daily"

            messages = self.prompt_service.build_moment_generation_messages(
                character,
                state,
                moment_type=moment_type,
                prompt_hint=prompt_hint,
                related_topics=related_topics,
            )

            content = self.llm_service.generate_proactive_reply(
                messages,
                character,
                state,
                proactive_type="proactive_share",
                hook_text=prompt_hint,
            ).strip()

            if not content:
                continue

            topic_refs = list(dict.fromkeys(([event_for_moment.display_name] if event_for_moment else []) + related_topics[:3]))

            records.append(
                StoredMoment(
                    id=f"moment_{uuid4().hex[:12]}",
                    character_id=character.id,
                    content=content,
                    relationship_phase_hint=state.relationship_phase,
                    topic_refs=topic_refs,
                    moment_type=moment_type,
                    auto_generated=True,
                    generated_from_topics=related_topics[:3],
                )
            )

            state.last_moment_at = datetime.now().isoformat(timespec="seconds")
            if event_for_moment:
                self.special_date_service.mark_sent(state, f"moment:{event_for_moment.event_key}")

            self.memory_service.save(state)
            changed = True

        if changed:
            self._save_records(records)

    def list_feed(self, user_id: str, character_id: str | None = None) -> list[MomentFeedItem]:
        records = self._load_records()
        records.sort(key=lambda item: item.created_at, reverse=True)

        result: list[MomentFeedItem] = []
        for record in records:
            if character_id and record.character_id != character_id:
                continue

            state = self.memory_service.load(user_id, record.character_id)
            if not state.is_friend:
                continue

            character = self.character_service.get(record.character_id)
            result.append(
                MomentFeedItem(
                    id=record.id,
                    character_id=record.character_id,
                    character_name=character.name,
                    avatar=character.avatar,
                    source=character.source,
                    content=record.content,
                    created_at=record.created_at,
                    relationship_phase_hint=record.relationship_phase_hint,
                    topic_refs=record.topic_refs,
                    liked_by_me=user_id in record.like_user_ids,
                    like_count=len(record.like_user_ids),
                    comments=record.comments,
                )
            )

        return result

    def toggle_like(self, user_id: str, moment_id: str) -> bool:
        records = self._load_records()
        target = next((item for item in records if item.id == moment_id), None)
        if not target:
            raise KeyError(f"动态不存在: {moment_id}")

        if user_id in target.like_user_ids:
            target.like_user_ids.remove(user_id)
            liked = False
        else:
            target.like_user_ids.append(user_id)
            liked = True

        self._save_records(records)
        return liked

    def add_comment(self, user_id: str, moment_id: str, content: str) -> MomentComment:
        text = content.strip()
        if not text:
            raise ValueError("评论不能为空")

        records = self._load_records()
        target = next((item for item in records if item.id == moment_id), None)
        if not target:
            raise KeyError(f"动态不存在: {moment_id}")

        comment = MomentComment(
            id=f"comment_{uuid4().hex[:12]}",
            user_id=user_id,
            user_name="你",
            content=text,
            actor_type="user",
        )
        target.comments.append(comment)

        self._maybe_auto_reply_to_comment(user_id, target, comment)

        self._save_records(records)
        return comment
    
    def _maybe_auto_reply_to_comment(self, user_id: str, target: StoredMoment, user_comment: MomentComment) -> None:
        state = self.memory_service.load(user_id, target.character_id)
        if not state.is_friend:
            return

        last_comment = target.comments[-2] if len(target.comments) >= 2 else None
        if last_comment and last_comment.actor_type == "character":
            return

        probability = {
            "stranger": 0.28,
            "familiar": 0.46,
            "close": 0.68,
        }.get(state.relationship_phase, 0.35)

        if random.random() > probability:
            return

        character = self.character_service.get(target.character_id)
        messages = self.prompt_service.build_comment_reply_messages(
            character,
            state,
            moment_content=target.content,
            user_comment=user_comment.content,
        )

        reply_text = self.llm_service.generate_proactive_reply(
            messages,
            character,
            state,
            proactive_type="proactive_share",
            hook_text=user_comment.content[:30],
        ).strip()

        if not reply_text:
            return

        target.comments.append(
            MomentComment(
                id=f"comment_{uuid4().hex[:12]}",
                user_id=character.id,
                user_name=character.name,
                content=reply_text,
                actor_type="character",
                character_id=character.id,
                reply_to_comment_id=user_comment.id,
            )
        )