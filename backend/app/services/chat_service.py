from __future__ import annotations

from datetime import datetime

from app.config import settings
from app.schemas import (
    AddContactResponse,
    CharacterSummary,
    ChatResponse,
    ConversationState,
    EventNode,
    EventReviewItem,
    FriendRequestListItem,
)
from app.services.character_service import CharacterService
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.services.prompt_service import PromptService
from app.services.runtime_service import RuntimeService
from app.services.simulation_service import SimulationService

STANDARD_VERIFY_PASS = "我通过了你的朋友验证请求，现在我们可以开始聊天了。"


class ChatService:
    def __init__(self) -> None:
        self.character_service = CharacterService()
        self.memory_service = MemoryService()
        self.prompt_service = PromptService()
        self.llm_service = LLMService()
        self.runtime_service = RuntimeService()
        self.simulation_service = SimulationService()

    def list_character_summaries(self, user_id: str) -> list[CharacterSummary]:
        summaries: list[CharacterSummary] = []
        for character in self.character_service.list_characters():
            state = self.memory_service.load(user_id, character.id)
            preview, preview_time = self.memory_service.get_last_preview(state)
            request_status = "accepted" if state.is_friend else self.simulation_service.get_friend_request_status(user_id, character.id)
            presence = self.simulation_service.get_presence_snapshot(user_id, character.id)

            summaries.append(
                CharacterSummary(
                    id=character.id,
                    name=character.name,
                    sort_letter=getattr(character, "sort_letter", "#"),
                    avatar=character.avatar,
                    title=character.title,
                    archetype=character.archetype,
                    source=character.source,
                    is_friend=state.is_friend,
                    is_pinned=state.is_pinned,
                    affection=state.affection,
                    trust=state.trust,
                    mood=state.mood,
                    story_stage=state.story_stage,
                    unread_count=state.unread_count,
                    last_message_preview=preview,
                    last_message_time=preview_time,
                    friend_request_status=request_status,
                    can_chat=state.is_friend,
                    presence_status=presence["presence_status"],
                    presence_text=presence["presence_text"],
                    last_seen_text=presence["last_seen_text"],
                )
            )
        return summaries

    def add_contact(self, user_id: str, character_id: str) -> AddContactResponse:
        character = self.character_service.get(character_id)
        state = self.memory_service.load(user_id, character_id)

        if state.is_friend:
            return AddContactResponse(
                character_id=character_id,
                success=True,
                status="accepted",
                message="已经是联系人了。",
                first_messages=[],
            )

        request = self.simulation_service.submit_friend_request(user_id, character)

        return AddContactResponse(
            character_id=character_id,
            success=True,
            status=request.status,
            message="好友申请已发送，正在等待对方通过验证。",
            first_messages=[],
        )
    
    def list_friend_requests(self, user_id: str) -> list[FriendRequestListItem]:
        requests = [
            item for item in self.simulation_service.load_friend_requests()
            if item.user_id == user_id
        ]
        requests.sort(key=lambda item: (item.requested_at, item.character_id), reverse=True)

        status_map = {
            "pending": "等待验证",
            "accepted": "已通过",
            "ignored": "已忽略",
            "rejected": "已拒绝",
        }

        items: list[FriendRequestListItem] = []

        for request in requests:
            character = self.character_service.get(request.character_id)
            state = self.memory_service.load(user_id, request.character_id)

            system_notice_text = ""
            result_text = ""
            reason_text = ""

            if request.status == "accepted":
                system_notice_text = getattr(character, "verify_system_notice", "") or STANDARD_VERIFY_PASS
                result_text = character.verify_accept_line
                reason_text = getattr(character, "verify_accept_reason", "") or ""
            elif request.status == "ignored":
                result_text = getattr(character, "verify_ignored_line", "") or "这次好友申请暂时没有收到回应。"
            elif request.status == "rejected":
                result_text = getattr(character, "verify_rejected_line", "") or "这次好友申请没有通过。"

            items.append(
                FriendRequestListItem(
                    character_id=character.id,
                    character_name=character.name,
                    avatar=character.avatar,
                    source=character.source,
                    requested_at=request.requested_at,
                    review_after=request.review_after,
                    resolved_at=request.resolved_at,
                    status=request.status,
                    status_text=status_map.get(request.status, "未知状态"),
                    is_friend=state.is_friend,
                    system_notice_text=system_notice_text,
                    result_text=result_text,
                    reason_text=reason_text,
                )
            )

        return items

    def delete_contact(self, user_id: str, character_id: str) -> None:
        self.memory_service.delete(user_id, character_id)

    def pin_contact(self, user_id: str, character_id: str, value: bool) -> None:
        state = self.memory_service.load(user_id, character_id)
        state.is_pinned = value
        self.memory_service.save(state)

    def increment_unread(self, user_id: str, character_id: str, count: int = 1) -> ConversationState:
        state = self.memory_service.load(user_id, character_id)
        if not state.is_friend:
            raise PermissionError("该角色还不是你的联系人，请先添加。")
        self.memory_service.increment_unread(state, max(1, count))
        self.memory_service.save(state)
        return state

    def get_conversation(self, user_id: str, character_id: str) -> ConversationState:
        state = self.memory_service.load(user_id, character_id)
        if not state.is_friend:
            raise PermissionError("该角色还不是你的联系人，请先添加。")
        self.memory_service.mark_read(state)
        self.memory_service.save(state)
        return state

    def chat(self, user_id: str, character_id: str, message: str) -> ChatResponse:
        character = self.character_service.get(character_id)
        state = self.memory_service.load(user_id, character_id)

        if not state.is_friend:
            raise PermissionError("该角色还不是你的联系人，请先等待对方通过验证。")

        self.memory_service.remove_typing_messages(state)
        self.memory_service.add_message(state, "user", message)
        self.memory_service.update_state_from_user_message(state, message)
        self.memory_service.save(state)

        job = self.simulation_service.queue_reply_job(user_id, character, message)

        return ChatResponse(
            character_id=character_id,
            reply="",
            additional_messages=[],
            triggered_events=[],
            story_stage=state.story_stage,
            affection=state.affection,
            trust=state.trust,
            mood=state.mood,
            mode=self.runtime_service.get_llm_mode(),
            queued=True,
            reply_job_status=job.status,
        )

    def reset_conversation(self, user_id: str, character_id: str) -> ConversationState:
        state = self.memory_service.reset(user_id, character_id)
        self.memory_service.save(state)
        return state

    def check_all_proactive(self, user_id: str, current_character_id: str | None = None) -> list[dict]:
        return self.simulation_service.process_tick(user_id, current_character_id)

    def _can_send_proactive(self, state: ConversationState) -> bool:
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

        return state.affection >= 55 or state.trust >= 55

    def _evaluate_events(self, character, state: ConversationState, user_message: str) -> list[EventNode]:
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
