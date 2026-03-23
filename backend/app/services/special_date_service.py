from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from app.config import RUNTIME_DIR
from app.schemas import (
    CharacterCard,
    ConversationState,
    SpecialCalendarEvent,
    UserProfileSettings,
)


class SpecialDateService:
    def __init__(self, profile_path: Path | None = None) -> None:
        self.profile_path = profile_path or (RUNTIME_DIR / "user_profile.json")
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)

    def load_user_profile(self) -> UserProfileSettings:
        if not self.profile_path.exists():
            self.save_user_profile(UserProfileSettings())
        raw = json.loads(self.profile_path.read_text(encoding="utf-8"))
        return UserProfileSettings(**raw)

    def save_user_profile(self, profile: UserProfileSettings) -> UserProfileSettings:
        self.profile_path.write_text(
            json.dumps(profile.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return profile

    def has_sent(self, state: ConversationState, scoped_event_key: str) -> bool:
        return scoped_event_key in state.special_event_history

    def mark_sent(self, state: ConversationState, scoped_event_key: str) -> None:
        if scoped_event_key not in state.special_event_history:
            state.special_event_history.append(scoped_event_key)
            state.special_event_history = state.special_event_history[-80:]

    def list_today_events(
        self,
        character: CharacterCard,
        state: ConversationState,
        today: date | None = None,
    ) -> list[SpecialCalendarEvent]:
        today = today or date.today()
        month_day = today.strftime("%m-%d")
        year = today.strftime("%Y")
        events: list[SpecialCalendarEvent] = []

        profile = self.load_user_profile()

        fixed_events = [
            ("new_year", "新年", "01-01", "新的一年", "今天是新年，适合主动送上新年问候。", "新年动态"),
            ("valentine", "情人节", "02-14", "情人节", "今天是情人节，适合主动表达一点特别的在意。", "情人节动态"),
            ("christmas", "圣诞节", "12-25", "圣诞节", "今天是圣诞节，适合发一条带节日气氛的消息。", "圣诞动态"),
        ]

        for key, display_name, md, hint, message_reason, moment_reason in fixed_events:
            if md == month_day:
                events.append(
                    SpecialCalendarEvent(
                        event_key=f"{key}:{year}",
                        event_type=key,
                        display_name=display_name,
                        prompt_hint=hint,
                        message_reason=message_reason,
                        moment_reason=moment_reason,
                    )
                )

        if profile.birthday_month_day and profile.birthday_month_day == month_day:
            events.append(
                SpecialCalendarEvent(
                    event_key=f"user_birthday:{year}",
                    event_type="user_birthday",
                    display_name="用户生日",
                    prompt_hint="今天是用户生日",
                    message_reason="今天是用户生日，适合主动送上更有陪伴感的祝福。",
                    moment_reason="生日氛围动态",
                )
            )

        if state.added_at:
            try:
                added_date = datetime.fromisoformat(state.added_at).date()
                delta_days = (today - added_date).days
                if delta_days in {7, 30}:
                    events.append(
                        SpecialCalendarEvent(
                            event_key=f"friendship_{delta_days}:{character.id}:{today.isoformat()}",
                            event_type=f"friendship_{delta_days}",
                            display_name=f"加好友满 {delta_days} 天",
                            prompt_hint=f"和用户加好友满 {delta_days} 天",
                            message_reason=f"今天是和用户加好友满 {delta_days} 天，适合主动提起这个节点。",
                            moment_reason=f"关系纪念日动态（{delta_days}天）",
                        )
                    )
            except Exception:
                pass

        for item in character.anniversary_dates:
            if item.month_day == month_day:
                events.append(
                    SpecialCalendarEvent(
                        event_key=f"character_anniversary:{character.id}:{item.key}:{year}",
                        event_type="character_anniversary",
                        display_name=item.name,
                        prompt_hint=item.prompt_hint or item.name,
                        message_reason=f"今天是和角色有关的纪念日：{item.name}。",
                        moment_reason=f"{item.name}纪念动态",
                    )
                )

        return events