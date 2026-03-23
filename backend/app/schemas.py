from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal

from pydantic import BaseModel, Field


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class EventNode(BaseModel):
    id: str
    title: str
    description: str
    trigger_keywords: List[str] = Field(default_factory=list)
    min_affection: int = 0
    min_trust: int = 0
    once: bool = True
    reply: str
    next_stage: str = ""
    reward_affection: int = 0
    reward_trust: int = 0


class EventReviewItem(BaseModel):
    event_id: str
    title: str
    description: str
    reply: str
    timestamp: str = Field(default_factory=now_iso)

class TopicHook(BaseModel):
    text: str
    category: Literal["plan", "emotion", "question", "daily", "event"] = "daily"
    created_at: str = Field(default_factory=now_iso)
    last_used_at: str | None = None
    resolved: bool = False

class FriendBehavior(BaseModel):
    base_accept_probability: float = 0.8
    min_review_delay_seconds: int = 60
    max_review_delay_seconds: int = 1800
    ignore_request_probability: float = 0.05
    reject_probability: float = 0.02


class ReplyBehavior(BaseModel):
    base_reply_probability: float = 0.9
    fast_reply_probability: float = 0.3
    delayed_reply_probability: float = 0.45
    ignore_probability: float = 0.08
    min_read_delay_seconds: int = 5
    max_read_delay_seconds: int = 180
    min_typing_delay_seconds: int = 2
    max_typing_delay_seconds: int = 25

    multi_message_probability: float = 0.22
    read_but_hold_probability: float = 0.12
    late_followup_probability: float = 0.08
    max_hold_delay_seconds: int = 900


class ProactiveBehavior(BaseModel):
    base_proactive_probability_per_check: float = 0.03
    affection_multiplier: float = 1.6
    trust_multiplier: float = 1.3
    silence_trigger_hours: int = 6


class DailyRhythm(BaseModel):
    sleep_hours: List[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5, 6])
    active_hours: List[int] = Field(default_factory=lambda: [9, 10, 11, 12, 13, 19, 20, 21, 22, 23])
    busy_hours: List[int] = Field(default_factory=lambda: [14, 15, 16])

class EmotionProfile(BaseModel):
    concern_expression: str = ""
    warm_expression: str = ""
    guarded_expression: str = ""
    playful_expression: str = ""
    flustered_expression: str = ""


class CharacterCard(BaseModel):
    id: str
    name: str
    sort_letter: str = "#"
    avatar: str
    title: str
    archetype: str
    source: str = ""
    verify_accept_line: str
    verify_accept_reason: str = ""
    verify_system_notice: str = "我通过了你的朋友验证请求，现在我们可以开始聊天了。"
    verify_ignored_line: str = ""
    verify_rejected_line: str = ""
    personality: List[str]
    speech_style: List[str]
    speech_habits: List[str] = Field(default_factory=list)
    relationship_style: Dict[str, str] = Field(default_factory=dict)
    phase_language: Dict[str, List[str]] = Field(default_factory=lambda: {
        "stranger": [],
        "familiar": [],
        "close": [],
    })
    address_style_by_phase: Dict[str, str] = Field(default_factory=dict)
    perspective_knowledge: List[str] = Field(default_factory=list)
    topic_attitudes: Dict[str, str] = Field(default_factory=dict)
    sensitive_topics: List[str] = Field(default_factory=list)
    forbidden_phrases: List[str] = Field(default_factory=list)
    reply_examples: Dict[str, List[str]] = Field(default_factory=dict)
    canon_guardrails: List[str] = Field(default_factory=list)
    canon_relationships: List[str] = Field(default_factory=list)
    status_texts: Dict[str, str] = Field(default_factory=dict)
    emotion_profile: EmotionProfile = Field(default_factory=EmotionProfile)
    taboo: List[str]
    lore: str
    world_knowledge: List[str] = Field(default_factory=list)
    system_prompt: str
    greetings: List[str]
    favorite_topics: List[str] = Field(default_factory=list)
    starter_topics: List[str] = Field(default_factory=list)
    proactive_lines: List[str] = Field(default_factory=list)
    event_nodes: List[EventNode] = Field(default_factory=list)

    friend_behavior: FriendBehavior = Field(default_factory=FriendBehavior)
    reply_behavior: ReplyBehavior = Field(default_factory=ReplyBehavior)
    proactive_behavior: ProactiveBehavior = Field(default_factory=ProactiveBehavior)
    daily_rhythm: DailyRhythm = Field(default_factory=DailyRhythm)

    anniversary_dates: List[AnniversaryDate] = Field(default_factory=list)
    festival_lines: Dict[str, str] = Field(default_factory=dict)
    moment_style: List[str] = Field(default_factory=list)
    moment_topics: List[str] = Field(default_factory=list)


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: str = Field(default_factory=now_iso)
    meta_type: str = "chat"
    proactive_type: str = ""
    proactive_reason: str = ""


class MemoryFact(BaseModel):
    type: str
    value: str

class RelationshipMemory(BaseModel):
    recent_topics: List[str] = Field(default_factory=list)
    unresolved_topics: List[str] = Field(default_factory=list)
    recent_emotions: List[str] = Field(default_factory=list)
    interaction_trends: List[str] = Field(default_factory=list)


class UserImpressionMemory(BaseModel):
    likes: List[str] = Field(default_factory=list)
    dislikes: List[str] = Field(default_factory=list)
    facts: List[str] = Field(default_factory=list)
    habits: List[str] = Field(default_factory=list)
    sensitivities: List[str] = Field(default_factory=list)


class ConversationState(BaseModel):
    user_id: str
    character_id: str
    is_friend: bool = False
    is_pinned: bool = False
    affection: int = 50
    trust: int = 50
    mood: str = "平静"
    story_stage: str = "opening"
    relationship_phase: Literal["stranger", "familiar", "close"] = "stranger"
    emotional_state: Literal["neutral", "concerned", "warm", "playful", "guarded", "flustered"] = "neutral"
    emotional_intensity: int = 0
    last_emotion_reason: str = ""
    relationship_momentum: int = 0
    recent_sentiment_trend: List[str] = Field(default_factory=list)
    unread_count: int = 0
    unlocked_events: List[str] = Field(default_factory=list)
    event_reviews: List[EventReviewItem] = Field(default_factory=list)
    profile: Dict[str, List[str]] = Field(default_factory=lambda: {"likes": [], "dislikes": [], "facts": []})
    memories: List[MemoryFact] = Field(default_factory=list)
    recent_topics: List[str] = Field(default_factory=list)
    followup_hooks: List[TopicHook] = Field(default_factory=list)
    relationship_memory: RelationshipMemory = Field(default_factory=RelationshipMemory)
    user_impression: UserImpressionMemory = Field(default_factory=UserImpressionMemory)
    memory_summary: List[str] = Field(default_factory=list)
    messages: List[ChatMessage] = Field(default_factory=list)
    last_active_at: str = Field(default_factory=now_iso)
    last_user_message_at: str | None = None
    last_proactive_at: str | None = None
    last_read_at: str | None = None
    care_cooldown_until: str | None = None
    added_at: str | None = None
    special_event_history: List[str] = Field(default_factory=list)
    last_moment_at: str | None = None
    last_competition_event_id: str | None = None
    rival_attention_score: int = 0
    last_rival_feeling: str = ""
    last_rival_trigger_at: str | None = None


class CharacterSummary(BaseModel):
    id: str
    name: str
    sort_letter: str = "#"
    avatar: str
    title: str
    archetype: str
    source: str = ""
    is_friend: bool = False
    is_pinned: bool = False
    affection: int = 50
    trust: int = 50
    mood: str = "平静"
    story_stage: str = "opening"
    unread_count: int = 0
    last_message_preview: str = ""
    last_message_time: str = ""
    friend_request_status: str = "none"
    can_chat: bool = False
    presence_status: str = "idle"
    presence_text: str = ""
    last_seen_text: str = ""


class ChatRequest(BaseModel):
    character_id: str
    message: str
    user_id: str | None = None


class ChatResponse(BaseModel):
    character_id: str
    reply: str
    additional_messages: List[str] = Field(default_factory=list)
    triggered_events: List[str] = Field(default_factory=list)
    story_stage: str
    affection: int
    trust: int
    mood: str
    mode: str
    queued: bool = False
    reply_job_status: str = "sent"


class AddContactResponse(BaseModel):
    character_id: str
    success: bool
    status: str = "pending"
    message: str = ""
    first_messages: List[str] = Field(default_factory=list)


class RuntimeStatusResponse(BaseModel):
    llm_mode: str
    ollama_model: str
    ollama_connected: bool
    available_models: List[str] = Field(default_factory=list)
    send_shortcut: str = "enter"
    detail_panel_default_open: bool = False
    auto_check_interval_seconds: int = 20
    user_id: str
    user_avatar: str = ""


class RuntimeUpdateRequest(BaseModel):
    llm_mode: str | None = None
    ollama_model: str | None = None
    send_shortcut: str | None = None
    auto_check_interval_seconds: int | None = None

class PendingFriendRequest(BaseModel):
    user_id: str
    character_id: str
    status: Literal["pending", "accepted", "ignored", "rejected"] = "pending"
    requested_at: str = Field(default_factory=now_iso)
    review_after: str
    resolved_at: str | None = None

class FriendRequestListItem(BaseModel):
    character_id: str
    character_name: str
    avatar: str
    source: str = ""
    requested_at: str
    review_after: str
    resolved_at: str | None = None
    status: Literal["pending", "accepted", "ignored", "rejected"] = "pending"
    status_text: str
    is_friend: bool = False
    system_notice_text: str = ""
    result_text: str = ""
    reason_text: str = ""


class FriendRequestListResponse(BaseModel):
    items: List[FriendRequestListItem] = Field(default_factory=list)


class PendingReplyJob(BaseModel):
    id: str
    user_id: str
    character_id: str
    user_message: str
    status: Literal["queued", "typing", "sent", "ignored"] = "queued"
    created_at: str = Field(default_factory=now_iso)
    read_after: str
    typing_after: str | None = None
    send_after: str | None = None
    ignore: bool = False
    burst_count: int = 1
    resolved_at: str | None = None

class ProactiveDecision(BaseModel):
    proactive_type: Literal[
        "proactive_followup",
        "proactive_care",
        "proactive_share",
        "proactive_checkin",
        "proactive_emotion",
    ] = "proactive_share"
    reason_text: str = ""
    hook_text: str | None = None
    prompt_hint: str = ""

class RivalAttentionEvent(BaseModel):
    event_id: str
    initiator_character_id: str
    rival_character_ids: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)
    resolved_at: str | None = None
    user_replied_character_id: str | None = None
    is_active: bool = True

class MomentComment(BaseModel):
    id: str
    user_id: str
    user_name: str = "你"
    content: str
    created_at: str = Field(default_factory=now_iso)
    actor_type: Literal["user", "character"] = "user"
    character_id: str | None = None
    reply_to_comment_id: str | None = None


class StoredMoment(BaseModel):
    id: str
    character_id: str
    content: str
    created_at: str = Field(default_factory=now_iso)
    relationship_phase_hint: str = ""
    topic_refs: List[str] = Field(default_factory=list)
    like_user_ids: List[str] = Field(default_factory=list)
    comments: List[MomentComment] = Field(default_factory=list)
    moment_type: str = "daily"
    auto_generated: bool = False
    generated_from_topics: List[str] = Field(default_factory=list)

class AnniversaryDate(BaseModel):
    key: str
    name: str
    month_day: str
    prompt_hint: str = ""


class UserProfileSettings(BaseModel):
    birthday_month_day: str = ""


class SpecialCalendarEvent(BaseModel):
    event_key: str
    event_type: str
    display_name: str
    prompt_hint: str = ""
    message_reason: str = ""
    moment_reason: str = ""

class MomentFeedItem(BaseModel):
    id: str
    character_id: str
    character_name: str
    avatar: str
    source: str = ""
    content: str
    created_at: str
    relationship_phase_hint: str = ""
    topic_refs: List[str] = Field(default_factory=list)
    liked_by_me: bool = False
    like_count: int = 0
    comments: List[MomentComment] = Field(default_factory=list)


class MomentFeedResponse(BaseModel):
    items: List[MomentFeedItem] = Field(default_factory=list)


class MomentCommentRequest(BaseModel):
    content: str


class AvatarUploadResponse(BaseModel):
    character_id: str
    avatar_url: str


class PinRequest(BaseModel):
    value: bool


class UnreadIncrementRequest(BaseModel):
    count: int = 1
