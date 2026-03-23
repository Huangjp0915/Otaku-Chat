from datetime import date

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import RUNTIME_DIR, STATIC_DIR, settings
from app.schemas import (
    ChatRequest,
    FriendRequestListResponse,
    MomentCommentRequest,
    MomentFeedResponse,
    PinRequest,
    UserProfileSettings,
    RuntimeStatusResponse,
    RuntimeUpdateRequest,
    UnreadIncrementRequest,
)
from app.services.avatar_service import AvatarService
from app.services.chat_service import ChatService
from app.services.moment_service import MomentService
from app.services.special_date_service import SpecialDateService

app = FastAPI(title="Otaku Chat Desktop", version="4.1.0")
chat_service = ChatService()
avatar_service = AvatarService()
moment_service = MomentService()
special_date_service = SpecialDateService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/user-content", StaticFiles(directory=str(RUNTIME_DIR)), name="user-content")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/runtime/status", response_model=RuntimeStatusResponse)
def get_runtime_status() -> RuntimeStatusResponse:
    runtime = chat_service.runtime_service.load()
    return RuntimeStatusResponse(
        llm_mode=runtime["llm_mode"],
        ollama_model=runtime["ollama_model"],
        ollama_connected=chat_service.llm_service.is_ollama_connected(),
        available_models=chat_service.llm_service.list_models(),
        send_shortcut=runtime["send_shortcut"],
        detail_panel_default_open=bool(runtime.get("detail_panel_default_open", False)),
        auto_check_interval_seconds=runtime["auto_check_interval_seconds"],
        user_id=settings.user_id,
        user_avatar=avatar_service.resolve_user_avatar(),
    )


@app.post("/api/runtime/update")
def update_runtime(request: RuntimeUpdateRequest) -> dict:
    data = chat_service.runtime_service.update(
        llm_mode=request.llm_mode,
        ollama_model=request.ollama_model,
        send_shortcut=request.send_shortcut,
        auto_check_interval_seconds=request.auto_check_interval_seconds,
    )
    return {"success": True, "data": data}


@app.get("/api/characters")
def list_characters() -> dict:
    summaries = chat_service.list_character_summaries(settings.user_id)
    return {"items": [item.model_dump() for item in summaries]}

@app.get("/api/friends/requests", response_model=FriendRequestListResponse)
def list_friend_requests() -> FriendRequestListResponse:
    items = chat_service.list_friend_requests(settings.user_id)
    return FriendRequestListResponse(items=items)

@app.get("/api/characters/{character_id}")
def get_character(character_id: str) -> dict:
    try:
        character = chat_service.character_service.get(character_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return character.model_dump()

@app.get("/api/moments/feed", response_model=MomentFeedResponse)
def list_moment_feed() -> MomentFeedResponse:
    items = moment_service.list_feed(settings.user_id)
    return MomentFeedResponse(items=items)


@app.get("/api/moments/character/{character_id}", response_model=MomentFeedResponse)
def list_character_moments(character_id: str) -> MomentFeedResponse:
    try:
        chat_service.character_service.get(character_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    items = moment_service.list_feed(settings.user_id, character_id=character_id)
    return MomentFeedResponse(items=items)


@app.post("/api/moments/{moment_id}/like")
def toggle_moment_like(moment_id: str) -> dict:
    try:
        liked = moment_service.toggle_like(settings.user_id, moment_id)
        items = moment_service.list_feed(settings.user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    target = next((item for item in items if item.id == moment_id), None)
    return {
        "success": True,
        "liked": liked,
        "like_count": target.like_count if target else 0,
    }


@app.post("/api/moments/{moment_id}/comment")
def add_moment_comment(moment_id: str, request: MomentCommentRequest) -> dict:
    try:
        comment = moment_service.add_comment(settings.user_id, moment_id, request.content)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "comment": comment.model_dump(),
    }


@app.post("/api/contacts/{character_id}/add")
def add_contact(character_id: str) -> dict:
    try:
        result = chat_service.add_contact(settings.user_id, character_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.model_dump()


@app.post("/api/contacts/{character_id}/delete")
def delete_contact(character_id: str) -> dict:
    try:
        chat_service.delete_contact(settings.user_id, character_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"success": True}


@app.post("/api/contacts/{character_id}/pin")
def pin_contact(character_id: str, request: PinRequest) -> dict:
    try:
        chat_service.pin_contact(settings.user_id, character_id, request.value)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"success": True, "value": request.value}


@app.get("/api/conversations/{character_id}")
def get_conversation(character_id: str) -> dict:
    try:
        state = chat_service.get_conversation(settings.user_id, character_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return state.model_dump()


@app.post("/api/conversations/{character_id}/increment-unread")
def increment_conversation_unread(character_id: str, request: UnreadIncrementRequest) -> dict:
    try:
        state = chat_service.increment_unread(settings.user_id, character_id, request.count)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"success": True, "unread_count": state.unread_count}


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict:
    user_id = request.user_id or settings.user_id
    message = request.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="消息不能为空")

    try:
        chat_service.simulation_service.resolve_rival_event_on_user_reply(
            user_id,
            request.character_id,
        )
        result = chat_service.chat(user_id, request.character_id, message)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    return result.model_dump()


@app.post("/api/conversations/{character_id}/reset")
def reset_conversation(character_id: str) -> dict:
    try:
        state = chat_service.reset_conversation(settings.user_id, character_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return state.model_dump()


@app.get("/api/proactive/check-all")
def proactive_check_all(current_character_id: str | None = Query(default=None)) -> dict:
    items = chat_service.check_all_proactive(settings.user_id, current_character_id)
    return {"items": items}


@app.post("/api/avatar/upload/{character_id}")
async def upload_avatar(character_id: str, file: UploadFile = File(...)) -> dict:
    try:
        chat_service.character_service.get(character_id)
        result = await avatar_service.save_upload(character_id, file)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump()


@app.post("/api/avatar/reset/{character_id}")
def reset_avatar(character_id: str) -> dict:
    try:
        chat_service.character_service.get(character_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    avatar_service.reset_avatar(character_id)
    return {"success": True}


@app.post("/api/avatar/upload-user")
async def upload_user_avatar(file: UploadFile = File(...)) -> dict:
    try:
        result = await avatar_service.save_user_upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump()


@app.post("/api/avatar/reset-user")
def reset_user_avatar() -> dict:
    avatar_service.reset_user_avatar()
    return {"success": True}

@app.get("/api/user/profile", response_model=UserProfileSettings)
def get_user_profile() -> UserProfileSettings:
    return special_date_service.load_user_profile()


@app.post("/api/user/profile", response_model=UserProfileSettings)
def save_user_profile(request: UserProfileSettings) -> UserProfileSettings:
    return special_date_service.save_user_profile(request)

