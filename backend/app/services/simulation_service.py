from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from app.config import RUNTIME_DIR, settings
from app.schemas import (
    CharacterCard,
    EventNode,
    EventReviewItem,
    PendingFriendRequest,
    RivalAttentionEvent,
    PendingReplyJob,
    ProactiveDecision,
)
from app.services.character_service import CharacterService
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.services.prompt_service import PromptService
from app.services.moment_service import MomentService
from app.services.special_date_service import SpecialDateService

STANDARD_VERIFY_PASS = "我通过了你的朋友验证请求，现在我们可以开始聊天了。"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class SimulationService:
    def __init__(self) -> None:
        self.friend_request_path = RUNTIME_DIR / "pending_friend_requests.json"
        self.reply_jobs_path = RUNTIME_DIR / "pending_jobs.json"
        self.rival_events_path = RUNTIME_DIR / "rival_attention_events.json"
        self.rival_events_path.parent.mkdir(parents=True, exist_ok=True)
        self.character_service = CharacterService()
        self.memory_service = MemoryService()
        self.prompt_service = PromptService()
        self.llm_service = LLMService()
        self._ensure_runtime_files()
        self.special_date_service = SpecialDateService()
        self.moment_service = MomentService()

    def _ensure_runtime_files(self) -> None:
        for path in [self.friend_request_path, self.reply_jobs_path]:
            if not path.exists():
                path.write_text("[]", encoding="utf-8")

    def _load_json_list(self, path: Path) -> list[dict]:
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8") or "[]")
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _save_json_list(self, path: Path, items: list[dict]) -> None:
        path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_friend_requests(self) -> list[PendingFriendRequest]:
        return [PendingFriendRequest(**item) for item in self._load_json_list(self.friend_request_path)]

    def save_friend_requests(self, items: list[PendingFriendRequest]) -> None:
        self._save_json_list(self.friend_request_path, [item.model_dump() for item in items])

    def load_reply_jobs(self) -> list[PendingReplyJob]:
        return [PendingReplyJob(**item) for item in self._load_json_list(self.reply_jobs_path)]

    def save_reply_jobs(self, items: list[PendingReplyJob]) -> None:
        self._save_json_list(self.reply_jobs_path, [item.model_dump() for item in items])

    def get_friend_request_status(self, user_id: str, character_id: str) -> str:
        matches = [
            item for item in self.load_friend_requests()
            if item.user_id == user_id and item.character_id == character_id
        ]
        if not matches:
            return "none"
        return matches[-1].status

    def submit_friend_request(self, user_id: str, character: CharacterCard) -> PendingFriendRequest:
        requests = self.load_friend_requests()
        for item in reversed(requests):
            if item.user_id == user_id and item.character_id == character.id and item.status == "pending":
                return item

        behavior = character.friend_behavior
        delay_seconds = random.randint(behavior.min_review_delay_seconds, behavior.max_review_delay_seconds)

        request = PendingFriendRequest(
            user_id=user_id,
            character_id=character.id,
            status="pending",
            review_after=(datetime.now() + timedelta(seconds=delay_seconds)).isoformat(timespec="seconds"),
        )
        requests.append(request)
        self.save_friend_requests(requests)
        return request

    def queue_reply_job(self, user_id: str, character: CharacterCard, user_message: str) -> PendingReplyJob:
        behavior = character.reply_behavior
        now = datetime.now()
        pace_roll = random.random()

        if pace_roll < behavior.fast_reply_probability:
            read_delay = random.randint(
                behavior.min_read_delay_seconds,
                min(25, behavior.max_read_delay_seconds),
            )
        elif pace_roll < behavior.fast_reply_probability + behavior.delayed_reply_probability:
            read_delay = random.randint(
                max(behavior.min_read_delay_seconds, max(10, behavior.max_read_delay_seconds // 2)),
                behavior.max_read_delay_seconds,
            )
        else:
            read_delay = random.randint(behavior.min_read_delay_seconds, behavior.max_read_delay_seconds)

        should_ignore = (random.random() < behavior.ignore_probability) or (random.random() > behavior.base_reply_probability)

        hold_extra = 0
        if not should_ignore and random.random() < behavior.read_but_hold_probability:
            hold_extra = random.randint(30, behavior.max_hold_delay_seconds)

        typing_delay = random.randint(behavior.min_typing_delay_seconds, behavior.max_typing_delay_seconds)
        send_gap = random.randint(2, max(4, behavior.max_typing_delay_seconds))

        read_after = now + timedelta(seconds=read_delay)
        typing_after = None if should_ignore else read_after + timedelta(seconds=typing_delay + hold_extra)
        send_after = None if should_ignore else typing_after + timedelta(seconds=send_gap)

        burst_count = 1
        if not should_ignore and random.random() < behavior.multi_message_probability:
            burst_count = 2 if random.random() < 0.8 else 3

        job = PendingReplyJob(
            id=f"reply_{int(now.timestamp() * 1000)}_{random.randint(1000, 9999)}",
            user_id=user_id,
            character_id=character.id,
            user_message=user_message,
            status="queued",
            read_after=read_after.isoformat(timespec="seconds"),
            typing_after=typing_after.isoformat(timespec="seconds") if typing_after else None,
            send_after=send_after.isoformat(timespec="seconds") if send_after else None,
            ignore=should_ignore,
            burst_count=burst_count,
        )

        jobs = self.load_reply_jobs()
        jobs.append(job)
        self.save_reply_jobs(jobs)
        return job

    def process_tick(self, user_id: str, current_character_id: str | None = None) -> list[dict]:
        items: dict[str, dict] = {}
        for character in self.character_service.list_characters():
            state = self.memory_service.load(user_id, character.id)
            items[character.id] = {
                "character_id": character.id,
                "sent": False,
                "message": "",
                "unread_count": state.unread_count,
            }

        self._process_friend_requests(user_id, items)
        self._process_reply_jobs(user_id, items, current_character_id)

        # 只把“主动来找你”的消息纳入竞争事件
        # 已经在回复你自己的消息，不算竞争
        sent_before = [cid for cid, meta in items.items() if meta.get("sent")]

        self._process_special_dates(user_id, items, current_character_id)
        self._process_proactive(user_id, items, current_character_id)

        sent_after = [cid for cid, meta in items.items() if meta.get("sent")]
        new_sent = [cid for cid in sent_after if cid not in sent_before]

        self._maybe_create_rival_event(user_id, new_sent)
        self._process_rival_reactions(user_id, items, current_character_id)

        self.moment_service.generate_due_moments_for_all(user_id)

        for character in self.character_service.list_characters():
            snapshot = self.get_presence_snapshot(user_id, character.id)
            state = self.memory_service.load(user_id, character.id)
            items[character.id]["unread_count"] = state.unread_count
            items[character.id].update(snapshot)

        return list(items.values())

    def _process_friend_requests(self, user_id: str, items: dict[str, dict]) -> None:
        requests = self.load_friend_requests()
        changed = False
        now = datetime.now()

        for request in requests:
            if request.user_id != user_id or request.status != "pending":
                continue
            if now < datetime.fromisoformat(request.review_after):
                continue

            character = self.character_service.get(request.character_id)
            behavior = character.friend_behavior
            roll = random.random()

            accept_cut = max(0.0, min(1.0, behavior.base_accept_probability))
            ignore_cut = accept_cut + max(0.0, min(1.0 - accept_cut, behavior.ignore_request_probability))

            if roll < accept_cut:
                request.status = "accepted"
                request.resolved_at = now_iso()

                state = self.memory_service.load(user_id, request.character_id)
                if not state.is_friend:
                    state.is_friend = True
                    state.added_at = now_iso()

                    verify_notice = getattr(character, "verify_system_notice", "") or STANDARD_VERIFY_PASS
                    verify_reason = getattr(character, "verify_accept_reason", "").strip()

                    self.memory_service.add_message(state, "assistant", verify_notice, meta_type="system")
                    self.memory_service.add_message(state, "assistant", character.verify_accept_line, meta_type="verify")

                    unread_delta = 2
                    if verify_reason:
                        self.memory_service.add_message(state, "assistant", verify_reason, meta_type="verify")
                        unread_delta += 1

                    self.memory_service.increment_unread(state, unread_delta)
                    self.memory_service.save(state)

                items[request.character_id]["sent"] = True
                items[request.character_id]["message"] = character.verify_accept_line
                items[request.character_id]["unread_count"] = self.memory_service.load(user_id, request.character_id).unread_count
                changed = True

            elif roll < ignore_cut:
                request.status = "ignored"
                request.resolved_at = now_iso()
                items[request.character_id]["sent"] = True
                changed = True

            else:
                request.status = "rejected"
                request.resolved_at = now_iso()
                items[request.character_id]["sent"] = True
                changed = True

        if changed:
            self.save_friend_requests(requests)

    def _process_reply_jobs(self, user_id: str, items: dict[str, dict], current_character_id: str | None) -> None:
        jobs = self.load_reply_jobs()
        changed = False
        now = datetime.now()

        for job in jobs:
            if job.user_id != user_id or job.status in {"sent", "ignored"}:
                continue

            state = self.memory_service.load(user_id, job.character_id)
            if not state.is_friend:
                job.status = "ignored"
                job.resolved_at = now_iso()
                changed = True
                continue

            if job.ignore and now >= datetime.fromisoformat(job.read_after):
                character = self.character_service.get(job.character_id)
                if random.random() < character.reply_behavior.late_followup_probability:
                    self.memory_service.register_manual_followup_hook(state, job.user_message, category="daily")
                    self.memory_service.save(state)

                job.status = "ignored"
                job.resolved_at = now_iso()
                changed = True
                continue

            if job.status == "queued" and job.typing_after and now >= datetime.fromisoformat(job.typing_after):
                self.memory_service.remove_typing_messages(state)
                self.memory_service.add_message(state, "assistant", "正在输入...", meta_type="typing")
                self.memory_service.save(state)
                job.status = "typing"
                items[job.character_id]["sent"] = True
                items[job.character_id]["unread_count"] = state.unread_count
                changed = True
                continue

            if job.status == "typing" and job.send_after and now >= datetime.fromisoformat(job.send_after):
                self.memory_service.remove_typing_messages(state)
                character = self.character_service.get(job.character_id)

                created_at = datetime.fromisoformat(job.created_at)
                behavior_mode = "delayed_reply" if (now - created_at).total_seconds() >= 90 else "normal_reply"

                prompt_messages = self.prompt_service.build_ollama_messages(
                    character,
                    state,
                    job.user_message,
                    behavior_mode=behavior_mode,
                )
                reply = self.llm_service.generate_reply(
                    prompt_messages,
                    character,
                    state,
                    job.user_message,
                    behavior_mode=behavior_mode,
                )

                reply_parts = self.llm_service.split_reply_messages(
                    character,
                    state,
                    reply,
                    max_parts=max(1, job.burst_count),
                )

                for part in reply_parts:
                    self.memory_service.add_message(state, "assistant", part)

                triggered_nodes = self._evaluate_events(character, state, job.user_message)
                extra_unread = max(1, len(reply_parts))

                for node in triggered_nodes:
                    event_message = f"【事件解锁：{node.title}】\n{node.reply}"
                    self.memory_service.add_message(state, "assistant", event_message, meta_type="event")
                    self.memory_service.add_event_review(
                        state,
                        EventReviewItem(
                            event_id=node.id,
                            title=node.title,
                            description=node.description,
                            reply=node.reply,
                        ),
                    )
                    extra_unread += 1

                if current_character_id == job.character_id:
                    self.memory_service.mark_read(state)
                else:
                    self.memory_service.increment_unread(state, extra_unread)

                self.memory_service.save(state)
                items[job.character_id]["sent"] = True
                items[job.character_id]["message"] = reply_parts[-1] if reply_parts else reply
                items[job.character_id]["unread_count"] = state.unread_count
                job.status = "sent"
                job.resolved_at = now_iso()
                changed = True

        if changed:
            self.save_reply_jobs(jobs)

    def _process_special_dates(self, user_id: str, items: dict[str, dict], current_character_id: str | None) -> None:
        for character in self.character_service.list_characters():
            state = self.memory_service.load(user_id, character.id)
            if not state.is_friend:
                continue

            today_events = self.special_date_service.list_today_events(character, state)
            if not today_events:
                continue

            event = next(
                (
                    item for item in today_events
                    if not self.special_date_service.has_sent(state, f"chat:{item.event_key}")
                ),
                None,
            )
            if not event:
                continue

            messages = self.prompt_service.build_special_event_messages(character, state, event)
            message = self.llm_service.generate_proactive_reply(
                messages,
                character,
                state,
                proactive_type="proactive_emotion",
                hook_text=event.prompt_hint,
            )

            self.memory_service.add_message(
                state,
                "assistant",
                message,
                meta_type="special",
                proactive_type=f"special_{event.event_type}",
                proactive_reason=event.message_reason,
            )
            state.last_proactive_at = now_iso()
            self.special_date_service.mark_sent(state, f"chat:{event.event_key}")

            if current_character_id == character.id:
                self.memory_service.mark_read(state)
            else:
                self.memory_service.increment_unread(state)

            self.memory_service.save(state)
            items[character.id]["sent"] = True
            items[character.id]["message"] = message
            items[character.id]["unread_count"] = state.unread_count
    
    def _process_proactive(self, user_id: str, items: dict[str, dict], current_character_id: str | None) -> None:
        for character in self.character_service.list_characters():
            state = self.memory_service.load(user_id, character.id)
            if not state.is_friend:
                continue

            decision = self._build_proactive_decision(character, state)
            if not decision:
                continue

            if not self._can_send_proactive(character, state, decision):
                continue

            proactive_messages = self.prompt_service.build_proactive_messages(
                character,
                state,
                proactive_type=decision.proactive_type,
                hook_text=decision.hook_text,
                reason_text=decision.reason_text,
                prompt_hint=decision.prompt_hint,
            )
            message = self.llm_service.generate_proactive_reply(
                proactive_messages,
                character,
                state,
                proactive_type=decision.proactive_type,
                hook_text=decision.hook_text,
            )

            self.memory_service.add_message(
                state,
                "assistant",
                message,
                meta_type="proactive",
                proactive_type=decision.proactive_type,
                proactive_reason=decision.reason_text,
            )
            state.last_proactive_at = now_iso()

            if decision.proactive_type in {"proactive_care", "proactive_emotion"}:
                state.care_cooldown_until = (datetime.now() + timedelta(hours=3)).isoformat(timespec="seconds")

            if decision.hook_text:
                self.memory_service.mark_hook_used(state, decision.hook_text, resolve=False)

            if current_character_id == character.id:
                self.memory_service.mark_read(state)
            else:
                self.memory_service.increment_unread(state)

            self.memory_service.save(state)
            items[character.id]["sent"] = True
            items[character.id]["message"] = message
            items[character.id]["unread_count"] = state.unread_count

    def _can_send_proactive(self, character: CharacterCard, state, decision: ProactiveDecision | None = None) -> bool:
        if len(state.messages) < 2:
            return False

        now = datetime.now()
        last_active = datetime.fromisoformat(state.last_active_at)
        if (now - last_active).total_seconds() < settings.proactive_cooldown_seconds:
            return False

        if state.last_proactive_at:
            last_proactive = datetime.fromisoformat(state.last_proactive_at)
            if (now - last_proactive).total_seconds() < settings.proactive_cooldown_seconds:
                return False

        behavior = character.proactive_behavior
        rhythm = character.daily_rhythm

        hour = now.hour
        chance = behavior.base_proactive_probability_per_check
        chance += max(0, state.affection - 50) / 50 * 0.06 * behavior.affection_multiplier
        chance += max(0, state.trust - 50) / 50 * 0.04 * behavior.trust_multiplier

        if state.relationship_momentum > 0:
            chance += min(0.08, state.relationship_momentum * 0.006)

        if decision:
            decision_bonus = {
                "proactive_followup": 0.08,
                "proactive_care": 0.10,
                "proactive_share": 0.05,
                "proactive_checkin": 0.07,
                "proactive_emotion": 0.06,
            }
            chance += decision_bonus.get(decision.proactive_type, 0.0)

        if state.emotional_state == "concerned":
            chance += 0.04

        silence_seconds = (now - last_active).total_seconds()
        if silence_seconds >= behavior.silence_trigger_hours * 3600:
            chance += 0.03

        if hour in rhythm.sleep_hours:
            chance *= 0.18
        elif hour in rhythm.busy_hours:
            chance *= 0.55
        elif hour in rhythm.active_hours:
            chance *= 1.2

        chance = max(0.0, min(0.62, chance))
        return random.random() < chance
    
    def _build_proactive_decision(self, character: CharacterCard, state) -> ProactiveDecision | None:
        now = datetime.now()
        last_active = datetime.fromisoformat(state.last_active_at)
        silence_seconds = (now - last_active).total_seconds()

        relationship_memory = getattr(state, "relationship_memory", None)
        user_impression = getattr(state, "user_impression", None)

        unresolved_topics = []
        if relationship_memory and getattr(relationship_memory, "unresolved_topics", None):
            unresolved_topics = [item for item in relationship_memory.unresolved_topics if item]
        else:
            unresolved_topics = [item.text for item in state.followup_hooks if not item.resolved][-4:]

        recent_topics = []
        if relationship_memory and getattr(relationship_memory, "recent_topics", None):
            recent_topics = [item for item in relationship_memory.recent_topics if item]
        else:
            recent_topics = state.recent_topics[-4:]

        likes = []
        habits = []
        sensitivities = []

        if user_impression:
            likes = list(getattr(user_impression, "likes", []) or [])
            habits = list(getattr(user_impression, "habits", []) or [])
            sensitivities = list(getattr(user_impression, "sensitivities", []) or [])

        if not likes:
            likes = list(state.profile.get("likes", []) or [])
        if not sensitivities:
            sensitivities = list(state.profile.get("dislikes", []) or [])

        hook = self.memory_service.pick_followup_hook(state)
        if hook:
            return ProactiveDecision(
                proactive_type="proactive_followup",
                reason_text=f"用户之前提到“{hook.text}”，这件事还没有真正聊完。",
                hook_text=hook.text,
                prompt_hint=hook.text,
            )

        if state.emotional_state == "concerned" and self._care_cooldown_ready(state):
            base_reason = state.last_emotion_reason or "用户前面状态不太好"
            return ProactiveDecision(
                proactive_type="proactive_care",
                reason_text=f"用户前面提到“{base_reason}”，现在适合主动关心一下。",
                prompt_hint=base_reason,
            )

        if silence_seconds >= max(6, character.proactive_behavior.silence_trigger_hours) * 3600 * 1.4:
            return ProactiveDecision(
                proactive_type="proactive_checkin",
                reason_text="已经有一段时间没聊天了，适合轻一点地来看看用户在不在。",
                prompt_hint="先轻轻试探，不要一上来太满",
            )

        share_seed = ""
        if likes:
            share_seed = likes[-1]
        elif recent_topics:
            share_seed = recent_topics[-1]
        elif habits:
            share_seed = habits[-1]

        if share_seed and state.relationship_phase in {"familiar", "close"}:
            return ProactiveDecision(
                proactive_type="proactive_share",
                reason_text=f"角色想到了一件和用户偏好或最近话题有关的事：{share_seed}",
                prompt_hint=share_seed,
            )

        if state.relationship_phase in {"familiar", "close"} and (
            state.emotional_state in {"warm", "playful", "flustered"} or state.relationship_momentum >= 7
        ):
            emotion_seed = state.last_emotion_reason or (recent_topics[-1] if recent_topics else "突然想到用户")
            return ProactiveDecision(
                proactive_type="proactive_emotion",
                reason_text="当前关系气氛比较热，角色自己也更容易主动想起用户。",
                prompt_hint=emotion_seed,
            )

        if sensitivities and self._care_cooldown_ready(state):
            seed = sensitivities[-1]
            return ProactiveDecision(
                proactive_type="proactive_care",
                reason_text=f"角色记得用户在“{seed}”这类事上会更敏感，所以想主动问一下。",
                prompt_hint=seed,
            )

        if recent_topics:
            seed = recent_topics[-1]
            return ProactiveDecision(
                proactive_type="proactive_share",
                reason_text=f"角色想起了最近聊过的话题“{seed}”，适合顺手分享一句。",
                prompt_hint=seed,
            )

        return None


    def _care_cooldown_ready(self, state) -> bool:
        if not state.care_cooldown_until:
            return True
        try:
            return datetime.now() >= datetime.fromisoformat(state.care_cooldown_until)
        except Exception:
            return True

    def _evaluate_events(self, character: CharacterCard, state, user_message: str) -> list[EventNode]:
        triggered: list[EventNode] = []
        for node in character.event_nodes:
            if node.once and node.id in state.unlocked_events:
                continue
            if state.affection < node.min_affection or state.trust < node.min_trust:
                continue
            if node.trigger_keywords and not any(keyword in user_message for keyword in node.trigger_keywords):
                continue
            state.unlocked_events.append(node.id)
            state.affection = min(100, state.affection + node.reward_affection)
            state.trust = min(100, state.trust + node.reward_trust)
            if node.next_stage:
                state.story_stage = node.next_stage
            triggered.append(node)
        return triggered
    
    def _format_last_seen_text(self, state) -> str:
        if not state.last_active_at:
            return ""

        now = datetime.now()
        last_active = datetime.fromisoformat(state.last_active_at)
        delta = now - last_active

        seconds = int(delta.total_seconds())
        if seconds < 120:
            return "刚刚在线"
        if seconds < 3600:
            return f"{seconds // 60} 分钟前在线"
        if seconds < 86400:
            return f"{seconds // 3600} 小时前在线"
        return f"{seconds // 86400} 天前在线"
    
    def get_presence_snapshot(self, user_id: str, character_id: str) -> dict:
        character = self.character_service.get(character_id)
        state = self.memory_service.load(user_id, character_id)
        jobs = [
            job for job in self.load_reply_jobs()
            if job.user_id == user_id and job.character_id == character_id and job.status in {"queued", "typing"}
        ]

        now = datetime.now()
        hour = now.hour

        default_texts = {
            "online": "在线",
            "busy": "忙碌中",
            "idle": "空闲中",
            "sleeping": "休息中",
            "typing": "正在输入...",
        }
        custom_texts = {**default_texts, **character.status_texts}

        status = "idle"

        if any(job.status == "typing" for job in jobs):
            status = "typing"
        elif hour in character.daily_rhythm.sleep_hours:
            status = "sleeping"
        elif hour in character.daily_rhythm.busy_hours:
            status = "busy"
        else:
            recent_seconds = (now - datetime.fromisoformat(state.last_active_at)).total_seconds()
            if recent_seconds <= 1800:
                status = "online"
            else:
                status = "idle"

        last_seen_text = ""
        if status in {"idle", "busy", "sleeping"}:
            last_seen_text = self._format_last_seen_text(state)

        return {
            "presence_status": status,
            "presence_text": custom_texts.get(status, default_texts[status]),
            "last_seen_text": last_seen_text,
        }
    
    def load_rival_events(self) -> list[RivalAttentionEvent]:
        if not self.rival_events_path.exists():
            self.save_rival_events([])
        raw = json.loads(self.rival_events_path.read_text(encoding="utf-8"))
        return [RivalAttentionEvent(**item) for item in raw]

    def save_rival_events(self, events: list[RivalAttentionEvent]) -> None:
        self.rival_events_path.write_text(
            json.dumps([item.model_dump() for item in events], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _maybe_create_rival_event(self, user_id: str, sent_character_ids: list[str]) -> None:
        valid_ids = []
        for character_id in sent_character_ids:
            state = self.memory_service.load(user_id, character_id)
            if state.is_friend:
                valid_ids.append(character_id)

        if len(valid_ids) < 2:
            return

        events = self.load_rival_events()

        active_recent = [
            item for item in events
            if item.is_active and item.resolved_at is None
        ]
        if active_recent:
            return

        initiator = valid_ids[0]
        rivals = valid_ids[1:]

        event = RivalAttentionEvent(
            event_id=f"rival_{uuid.uuid4().hex[:12]}",
            initiator_character_id=initiator,
            rival_character_ids=rivals,
        )
        events.append(event)
        self.save_rival_events(events)

        all_ids = [initiator] + rivals
        for cid in all_ids:
            state = self.memory_service.load(user_id, cid)
            state.last_competition_event_id = event.event_id
            self.memory_service.save(state)

    def resolve_rival_event_on_user_reply(self, user_id: str, replied_character_id: str) -> None:
        events = self.load_rival_events()
        target = next(
            (
                item for item in reversed(events)
                if item.is_active and item.resolved_at is None and (
                    item.initiator_character_id == replied_character_id or replied_character_id in item.rival_character_ids
                )
            ),
            None,
        )
        if not target:
            return

        target.user_replied_character_id = replied_character_id
        target.resolved_at = now_iso()
        target.is_active = False

        affected_ids = [target.initiator_character_id] + target.rival_character_ids
        for cid in affected_ids:
            state = self.memory_service.load(user_id, cid)
            if cid == replied_character_id:
                self.memory_service.acknowledge_priority_reply(state)
            else:
                intensity = 1
                if state.relationship_phase == "close":
                    intensity = 2
                feeling = "jealous" if state.relationship_phase == "close" else "left_out"
                self.memory_service.apply_rival_attention_hit(state, intensity=intensity, feeling=feeling)
            self.memory_service.save(state)

        self.save_rival_events(events)

    def _process_rival_reactions(self, user_id: str, items: dict[str, dict], current_character_id: str | None) -> None:
        for character in self.character_service.list_characters():
            state = self.memory_service.load(user_id, character.id)
            if not state.is_friend:
                continue

            if not self.memory_service.should_trigger_rival_followup(state):
                continue

            if state.rival_attention_score <= 0:
                continue

            if state.last_proactive_at:
                try:
                    last_proactive = datetime.fromisoformat(state.last_proactive_at)
                    if (datetime.now() - last_proactive).total_seconds() < 3600:
                        continue
                except Exception:
                    pass

            character_obj = self.character_service.get(character.id)
            messages = self.prompt_service.build_rival_reaction_messages(character_obj, state)
            message = self.llm_service.generate_proactive_reply(
                messages,
                character_obj,
                state,
                proactive_type="rival_reaction",
                hook_text=state.last_rival_feeling or "在意",
            )

            self.memory_service.add_message(
                state,
                "assistant",
                message,
                meta_type="proactive",
                proactive_type="rival_reaction",
                proactive_reason="用户刚刚优先回应了别的角色，角色产生了轻微在意反应。",
            )
            state.last_proactive_at = now_iso()

            if current_character_id == character.id:
                self.memory_service.mark_read(state)
            else:
                self.memory_service.increment_unread(state)

            self.memory_service.clear_rival_attention(state)
            self.memory_service.save(state)

            items[character.id]["sent"] = True
            items[character.id]["message"] = message
            items[character.id]["unread_count"] = state.unread_count