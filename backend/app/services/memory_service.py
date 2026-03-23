from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from app.config import CONVERSATION_DIR
from app.schemas import ChatMessage, ConversationState, EventReviewItem, MemoryFact, TopicHook

POSITIVE_WORDS = ["喜欢", "想你", "谢谢", "开心", "高兴", "可爱", "厉害", "在意", "陪我"]
NEGATIVE_WORDS = ["讨厌", "烦", "滚", "生气", "难受", "痛苦", "失望", "无聊"]

PLAN_TRIGGERS = ["明天", "今天", "等会", "晚点", "周末", "最近", "准备", "打算", "要去", "要做", "考试", "上课", "工作", "图书馆"]
EMOTION_TRIGGERS = ["累", "困", "难过", "烦", "委屈", "焦虑", "紧张", "开心", "高兴", "失眠", "压力"]
QUESTION_TRIGGERS = ["吗", "呢", "怎么", "为什么", "要不要", "行不行", "好不好", "能不能"]


class MemoryService:
    def __init__(self, conversation_dir: Path = CONVERSATION_DIR) -> None:
        self.conversation_dir = conversation_dir
        self.conversation_dir.mkdir(parents=True, exist_ok=True)

    def _file_path(self, user_id: str, character_id: str) -> Path:
        safe_name = f"{user_id}__{character_id}.json".replace("/", "_")
        return self.conversation_dir / safe_name

    def load(self, user_id: str, character_id: str) -> ConversationState:
        path = self._file_path(user_id, character_id)
        if not path.exists():
            return ConversationState(user_id=user_id, character_id=character_id)
        data = json.loads(path.read_text(encoding="utf-8"))
        return ConversationState(**data)

    def save(self, state: ConversationState) -> None:
        path = self._file_path(state.user_id, state.character_id)
        path.write_text(state.model_dump_json(indent=2), encoding="utf-8")

    def delete(self, user_id: str, character_id: str) -> None:
        path = self._file_path(user_id, character_id)
        if path.exists():
            path.unlink()

    def reset(self, user_id: str, character_id: str) -> ConversationState:
        old = self.load(user_id, character_id)
        self.delete(user_id, character_id)
        return ConversationState(
            user_id=user_id,
            character_id=character_id,
            is_friend=old.is_friend,
            is_pinned=old.is_pinned,
            added_at=old.added_at,
        )

    def add_message(
        self,
        state: ConversationState,
        role: str,
        content: str,
        meta_type: str = "chat",
        proactive_type: str = "",
        proactive_reason: str = "",
    ) -> None:
        state.messages.append(
            ChatMessage(
                role=role,
                content=content,
                meta_type=meta_type,
                proactive_type=proactive_type,
                proactive_reason=proactive_reason,
            )
        )
        state.messages = state.messages[-120:]
        state.last_active_at = datetime.now().isoformat(timespec="seconds")
        if role == "user":
            state.last_user_message_at = datetime.now().isoformat(timespec="seconds")

    def remove_typing_messages(self, state: ConversationState) -> None:
        state.messages = [msg for msg in state.messages if msg.meta_type != "typing"]

    def mark_read(self, state: ConversationState) -> None:
        state.unread_count = 0
        state.last_read_at = datetime.now().isoformat(timespec="seconds")

    def increment_unread(self, state: ConversationState, count: int = 1) -> None:
        state.unread_count += count

    def update_state_from_user_message(self, state: ConversationState, message: str) -> None:
        self._extract_profile(state, message)
        self._update_emotion_scores(state, message)
        self._remember_general_fact(state, message)
        self._remember_habits_and_sensitivities(state, message)
        self._remember_recent_topics(state, message)
        self._register_followup_hooks(state, message)
        self._update_emotional_continuity(state, message)
        self._update_relationship_momentum(state, message)
        self._refresh_relationship_phase(state)
        self._refresh_layered_memory(state)
        self.refresh_memory_summary(state)
        state.last_active_at = datetime.now().isoformat(timespec="seconds")
        state.last_user_message_at = datetime.now().isoformat(timespec="seconds")

    def _extract_profile(self, state: ConversationState, message: str) -> None:
        likes_patterns = [r"我喜欢(.+)", r"我最喜欢(.+)"]
        dislikes_patterns = [r"我讨厌(.+)", r"我不喜欢(.+)"]

        for pattern in likes_patterns:
            m = re.search(pattern, message)
            if m:
                value = m.group(1).strip("。！!，, ")
                if value and value not in state.profile["likes"]:
                    state.profile["likes"].append(value)
                    self._append_memory(state, MemoryFact(type="like", value=value))

        for pattern in dislikes_patterns:
            m = re.search(pattern, message)
            if m:
                value = m.group(1).strip("。！!，, ")
                if value and value not in state.profile["dislikes"]:
                    state.profile["dislikes"].append(value)
                    self._append_memory(state, MemoryFact(type="dislike", value=value))

    def _remember_general_fact(self, state: ConversationState, message: str) -> None:
        triggers = ["我是", "我现在", "我今天", "我刚刚", "我来自", "我在", "我要", "我准备"]
        if any(t in message for t in triggers):
            compact = message.strip()
            if 4 <= len(compact) <= 80:
                self._append_memory(state, MemoryFact(type="fact", value=compact))
                if compact not in state.profile["facts"]:
                    state.profile["facts"].append(compact)
                    state.profile["facts"] = state.profile["facts"][-10:]

    def _remember_habits_and_sensitivities(self, state: ConversationState, message: str) -> None:
        compact = message.strip("。！!，, ")
        if not compact:
            return

        habit_triggers = ["平时", "经常", "总是", "习惯", "作息", "熬夜", "早起", "晚睡"]
        sensitivity_triggers = ["害怕", "怕", "焦虑", "紧张", "不敢", "压力", "失眠"]

        if any(token in compact for token in habit_triggers):
            self._append_memory(state, MemoryFact(type="habit", value=compact[:40]))

        if any(token in compact for token in sensitivity_triggers):
            self._append_memory(state, MemoryFact(type="sensitivity", value=compact[:40]))

    def _remember_recent_topics(self, state: ConversationState, message: str) -> None:
        parts = re.split(r"[，。！？!?；;\n]+", message)
        for part in parts:
            compact = part.strip()
            if 4 <= len(compact) <= 24 and compact not in state.recent_topics:
                state.recent_topics.append(compact)
        state.recent_topics = state.recent_topics[-12:]

    def _register_followup_hooks(self, state: ConversationState, message: str) -> None:
        compact = message.strip()
        if not (6 <= len(compact) <= 60):
            return

        category = None
        if any(word in compact for word in PLAN_TRIGGERS):
            category = "plan"
        elif any(word in compact for word in EMOTION_TRIGGERS):
            category = "emotion"
        elif any(word in compact for word in QUESTION_TRIGGERS) or compact.endswith(("？", "?")):
            category = "question"
        elif any(word in compact for word in ["今天", "刚刚", "现在", "最近"]):
            category = "daily"

        if not category:
            return

        existing = {item.text for item in state.followup_hooks if not item.resolved}
        if compact not in existing:
            state.followup_hooks.append(TopicHook(text=compact, category=category))
            state.followup_hooks = state.followup_hooks[-12:]

    def _append_memory(self, state: ConversationState, fact: MemoryFact) -> None:
        existing = {(item.type, item.value) for item in state.memories}
        if (fact.type, fact.value) not in existing:
            state.memories.append(fact)
            state.memories = state.memories[-30:]

    def _update_emotion_scores(self, state: ConversationState, message: str) -> None:
        positive_hits = sum(1 for word in POSITIVE_WORDS if word in message)
        negative_hits = sum(1 for word in NEGATIVE_WORDS if word in message)

        state.affection = max(0, min(100, state.affection + positive_hits * 2 - negative_hits * 2))
        state.trust = max(0, min(100, state.trust + positive_hits * 2 - negative_hits))

        if negative_hits >= 2:
            state.mood = "低落"
        elif positive_hits >= 2:
            state.mood = "开心"
        elif "累" in message or "困" in message:
            state.mood = "担心你"

    def _update_emotional_continuity(self, state: ConversationState, message: str) -> None:
        compact = message.strip()

        negative_triggers = ["累", "困", "烦", "难过", "焦虑", "失眠", "压力", "不开心", "委屈", "难受"]
        positive_triggers = ["喜欢你", "谢谢", "开心", "高兴", "想你", "期待", "好耶"]
        playful_triggers = ["哈哈", "嘿嘿", "一起玩", "有趣", "整活"]
        guarded_triggers = ["别管", "算了", "没事", "烦死了"]

        if any(x in compact for x in negative_triggers):
            state.emotional_state = "concerned"
            state.emotional_intensity = min(100, max(state.emotional_intensity, 45) + 10)
            state.last_emotion_reason = compact[:40]
            state.recent_sentiment_trend.append("negative")
        elif any(x in compact for x in positive_triggers):
            if "喜欢你" in compact:
                state.emotional_state = "flustered"
            else:
                state.emotional_state = "warm"
            state.emotional_intensity = min(100, max(state.emotional_intensity, 35) + 8)
            state.last_emotion_reason = compact[:40]
            state.recent_sentiment_trend.append("positive")
        elif any(x in compact for x in playful_triggers):
            state.emotional_state = "playful"
            state.emotional_intensity = min(100, max(state.emotional_intensity, 25) + 6)
            state.last_emotion_reason = compact[:40]
            state.recent_sentiment_trend.append("playful")
        elif any(x in compact for x in guarded_triggers):
            state.emotional_state = "guarded"
            state.emotional_intensity = min(100, max(state.emotional_intensity, 30) + 6)
            state.last_emotion_reason = compact[:40]
            state.recent_sentiment_trend.append("guarded")
        else:
            state.emotional_intensity = max(0, state.emotional_intensity - 4)
            if state.emotional_intensity <= 12:
                state.emotional_state = "neutral"
                state.last_emotion_reason = ""

        state.recent_sentiment_trend = state.recent_sentiment_trend[-8:]

    def _update_relationship_momentum(self, state: ConversationState, message: str) -> None:
        compact = message.strip()

        positive = ["谢谢", "喜欢", "想你", "一起", "陪我", "相信你", "在意你"]
        negative = ["讨厌", "烦", "滚", "别管", "无聊", "算了"]

        delta = 0
        delta += sum(1 for x in positive if x in compact) * 2
        delta -= sum(1 for x in negative if x in compact) * 2

        if state.relationship_phase == "close":
            delta += 1
        if len(compact) >= 12:
            delta += 1

        state.relationship_momentum = max(-20, min(20, state.relationship_momentum + delta))

        if delta == 0:
            if state.relationship_momentum > 0:
                state.relationship_momentum -= 1
            elif state.relationship_momentum < 0:
                state.relationship_momentum += 1

    def _refresh_relationship_phase(self, state: ConversationState) -> None:
        user_msg_count = sum(1 for msg in state.messages if msg.role == "user")
        score = state.affection * 0.55 + state.trust * 0.45

        if score >= 78 or (score >= 68 and user_msg_count >= 12):
            state.relationship_phase = "close"
        elif score >= 58 or user_msg_count >= 4:
            state.relationship_phase = "familiar"
        else:
            state.relationship_phase = "stranger"

    def _tail_unique(self, items: list[str], limit: int) -> list[str]:
        cleaned = [item.strip() for item in items if isinstance(item, str) and item.strip()]
        return list(dict.fromkeys(cleaned))[-limit:]

    def _refresh_layered_memory(self, state: ConversationState) -> None:
        unresolved_topics = [item.text for item in state.followup_hooks if not item.resolved][-4:]

        recent_emotions: list[str] = []
        if state.last_emotion_reason:
            recent_emotions.append(f"{state.emotional_state}：{state.last_emotion_reason}")
        if state.recent_sentiment_trend:
            recent_emotions.append("趋势：" + " → ".join(state.recent_sentiment_trend[-4:]))

        interaction_trends: list[str] = []
        if state.relationship_momentum >= 6:
            interaction_trends.append("最近互动明显升温")
        elif state.relationship_momentum <= -4:
            interaction_trends.append("最近互动有些降温")
        else:
            interaction_trends.append("最近互动比较平稳")

        phase_note_map = {
            "stranger": "还在建立熟悉感",
            "familiar": "已经有持续上下文",
            "close": "互动明显更亲近",
        }
        interaction_trends.append(phase_note_map.get(state.relationship_phase, ""))

        state.relationship_memory.recent_topics = self._tail_unique(state.recent_topics[-4:], 4)
        state.relationship_memory.unresolved_topics = self._tail_unique(unresolved_topics, 4)
        state.relationship_memory.recent_emotions = self._tail_unique(recent_emotions, 3)
        state.relationship_memory.interaction_trends = self._tail_unique(interaction_trends, 3)

        habit_items = [item.value for item in state.memories if item.type == "habit"]
        sensitivity_items = [item.value for item in state.memories if item.type in {"sensitivity", "dislike"}]
        fact_items = state.profile.get("facts", []) + [item.value for item in state.memories if item.type == "fact"]

        state.user_impression.likes = self._tail_unique(state.profile.get("likes", []), 6)
        state.user_impression.dislikes = self._tail_unique(state.profile.get("dislikes", []), 6)
        state.user_impression.facts = self._tail_unique(fact_items, 8)
        state.user_impression.habits = self._tail_unique(habit_items, 4)
        state.user_impression.sensitivities = self._tail_unique(sensitivity_items, 4)

    def add_event_review(self, state: ConversationState, item: EventReviewItem) -> None:
        state.event_reviews.append(item)
        state.event_reviews = state.event_reviews[-30:]

    def get_last_preview(self, state: ConversationState) -> tuple[str, str]:
        if not state.messages:
            return "", ""
        for msg in reversed(state.messages):
            if msg.role == "system" or msg.meta_type == "typing":
                continue
            content = msg.content.replace("\n", " ").strip()
            if msg.role == "user":
                content = f"你：{content}"
            if len(content) > 28:
                content = content[:28] + "..."
            return content, msg.timestamp
        return "", ""

    def build_short_term_context_lines(self, state: ConversationState, limit: int = 6) -> list[str]:
        lines: list[str] = []
        for msg in state.messages:
            if msg.role == "system" or msg.meta_type == "typing":
                continue
            speaker = "用户" if msg.role == "user" else "角色"
            compact = msg.content.strip().replace("\n", " / ")
            if compact:
                lines.append(f"{speaker}：{compact[:60]}")
        return lines[-limit:]

    def build_mid_term_memory_lines(self, state: ConversationState) -> list[str]:
        self._refresh_layered_memory(state)
        memory = state.relationship_memory
        lines: list[str] = []

        if memory.recent_topics:
            lines.append("最近几次常聊：" + " / ".join(memory.recent_topics))
        if memory.unresolved_topics:
            lines.append("还可以继续接的话题：" + " / ".join(memory.unresolved_topics))
        if memory.recent_emotions:
            lines.append("最近互动情绪：" + " / ".join(memory.recent_emotions))
        if memory.interaction_trends:
            lines.append("最近关系走势：" + " / ".join(memory.interaction_trends))

        return lines[:6]

    def build_long_term_memory_lines(self, state: ConversationState) -> list[str]:
        self._refresh_layered_memory(state)
        impression = state.user_impression
        lines: list[str] = []

        if impression.likes:
            lines.append("用户偏好：" + "、".join(impression.likes[-4:]))
        if impression.dislikes:
            lines.append("用户回避：" + "、".join(impression.dislikes[-4:]))
        if impression.facts:
            lines.append("稳定近况：" + " / ".join(impression.facts[-4:]))
        if impression.habits:
            lines.append("用户习惯或作息：" + " / ".join(impression.habits[-3:]))
        if impression.sensitivities:
            lines.append("用户敏感点：" + " / ".join(impression.sensitivities[-3:]))

        return lines[:6]

    def build_memory_digest(self, state: ConversationState) -> list[str]:
        self._refresh_layered_memory(state)
        self.refresh_memory_summary(state)
        return state.memory_summary

    def refresh_memory_summary(self, state: ConversationState) -> None:
        self._refresh_layered_memory(state)

        mid_lines = self.build_mid_term_memory_lines(state)
        long_lines = self.build_long_term_memory_lines(state)

        summary: list[str] = []
        summary.extend([f"[中期] {item}" for item in mid_lines[:3]])
        summary.extend([f"[长期] {item}" for item in long_lines[:3]])

        if state.emotional_state != "neutral":
            summary.append(f"[情绪] {state.emotional_state} / 强度 {state.emotional_intensity}")

        state.memory_summary = summary[:7]

    def pick_followup_hook(self, state: ConversationState) -> TopicHook | None:
        now = datetime.now()

        candidates = []
        for item in state.followup_hooks:
            if item.resolved:
                continue

            if item.last_used_at:
                last_used = datetime.fromisoformat(item.last_used_at)
                if now - last_used < timedelta(hours=4):
                    continue

            candidates.append(item)

        if not candidates:
            return None

        candidates.sort(key=lambda x: x.created_at, reverse=True)
        return candidates[0]

    def mark_hook_used(self, state: ConversationState, hook_text: str, resolve: bool = False) -> None:
        for item in state.followup_hooks:
            if item.text == hook_text and not item.resolved:
                item.last_used_at = datetime.now().isoformat(timespec="seconds")
                if resolve:
                    item.resolved = True
                break

    def apply_rival_attention_hit(
        self,
        state: ConversationState,
        intensity: int = 1,
        feeling: str = "left_out",
    ) -> None:
        state.rival_attention_score = min(10, state.rival_attention_score + intensity)
        state.last_rival_feeling = feeling
        state.last_rival_trigger_at = datetime.now().isoformat(timespec="seconds")

        if feeling == "left_out":
            state.relationship_momentum = max(-10, state.relationship_momentum - intensity)
            if state.emotional_state in {"warm", "playful"}:
                state.emotional_state = "guarded"
            elif state.emotional_state == "neutral":
                state.emotional_state = "guarded"
        elif feeling == "jealous":
            state.relationship_momentum = max(-10, state.relationship_momentum - max(1, intensity))
            state.emotional_state = "guarded"

        self._refresh_layered_memory(state)
        self.refresh_memory_summary(state)

    def clear_rival_attention(self, state: ConversationState) -> None:
        state.rival_attention_score = 0
        state.last_rival_feeling = ""
        state.last_rival_trigger_at = None

    def acknowledge_priority_reply(self, state: ConversationState) -> None:
        if state.rival_attention_score > 0:
            state.rival_attention_score = max(0, state.rival_attention_score - 2)
        if state.relationship_momentum < 0:
            state.relationship_momentum = min(10, state.relationship_momentum + 1)

    def should_trigger_rival_followup(self, state: ConversationState) -> bool:
        if state.rival_attention_score <= 0:
            return False
        if not state.last_rival_trigger_at:
            return True
        try:
            last_time = datetime.fromisoformat(state.last_rival_trigger_at)
            return (datetime.now() - last_time).total_seconds() >= 1800
        except Exception:
            return True

    def register_manual_followup_hook(self, state: ConversationState, text: str, category: str = "daily") -> None:
        compact = text.strip()
        if not (4 <= len(compact) <= 60):
            return

        existing = {item.text for item in state.followup_hooks if not item.resolved}
        if compact not in existing:
            state.followup_hooks.append(TopicHook(text=compact, category=category))
            state.followup_hooks = state.followup_hooks[-12:]