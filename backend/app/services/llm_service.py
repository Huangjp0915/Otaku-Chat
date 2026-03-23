from __future__ import annotations

import random
from typing import Optional

import requests

from app.config import settings
from app.schemas import CharacterCard, ConversationState
from app.services.runtime_service import RuntimeService


class LLMService:
    def __init__(self) -> None:
        self.runtime_service = RuntimeService()

    def list_models(self) -> list[str]:
        try:
            response = requests.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        except Exception:
            return []

    def is_ollama_connected(self) -> bool:
        try:
            response = requests.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags", timeout=5)
            return response.ok
        except Exception:
            return False

    def generate_reply(
        self,
        messages: list[dict],
        character: CharacterCard,
        state: ConversationState,
        user_message: str,
        behavior_mode: str = "normal_reply",
    ) -> str:
        if self.runtime_service.get_llm_mode().lower() == "ollama":
            try:
                raw = self._generate_with_ollama(messages)
                return self._clean_reply(raw, character)
            except Exception:
                return self._generate_mock(character, state, user_message, behavior_mode)
        return self._generate_mock(character, state, user_message, behavior_mode)

    def generate_proactive_reply(
        self,
        messages: list[dict],
        character: CharacterCard,
        state: ConversationState,
        proactive_type: str = "proactive_share",
        hook_text: Optional[str] = None,
    ) -> str:
        if self.runtime_service.get_llm_mode().lower() == "ollama":
            try:
                raw = self._generate_with_ollama(messages)
                return self._clean_reply(raw, character)
            except Exception:
                pass
        return self._generate_mock_proactive(character, state, proactive_type, hook_text)

    def _generate_with_ollama(self, messages: list[dict]) -> str:
        response = requests.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/chat",
            json={
                "model": self.runtime_service.get_ollama_model(),
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.85,
                    "top_p": 0.9,
                },
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        text = (data.get("message") or {}).get("content", "").strip()
        if not text:
            raise RuntimeError("模型没有返回内容")
        return self._clean_reply(text)

    def _clean_reply(self, text: str, character: Optional[CharacterCard] = None) -> str:
        text = text.strip()

        bad_prefixes = [
            "当然，",
            "当然",
            "作为",
            "我是AI",
            "作为AI",
            "好的，",
            "以下是",
            "根据设定",
            "从角色设定来看",
        ]
        for prefix in bad_prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()

        text = text.replace("（", "").replace("）", "")
        text = text.replace("(", "").replace(")", "")
        text = text.replace("【", "").replace("】", "")

        if character:
            for phrase in character.forbidden_phrases:
                text = text.replace(phrase, "")

        while "  " in text:
            text = text.replace("  ", " ")

        return text[:400].strip()
    
    def _post_adjust_mock_reply(self, character: CharacterCard, state: ConversationState, reply: str) -> str:
        if state.emotional_intensity < 25:
            return reply

        if state.emotional_state == "concerned":
            if character.id == "rem":
                return reply + " 蕾姆会记着您现在的状态。"
            if character.id == "misaka_mikoto":
                return reply + " 总之你别再一个人硬撑。"
            if character.id == "fujiwara_chika":
                return reply + " 我会继续盯着你的状态的！"

        if state.emotional_state == "warm" and state.relationship_phase != "stranger":
            if character.id == "rem":
                return reply + " 能这样和您说话，蕾姆会觉得很安心。"
            if character.id == "misaka_mikoto":
                return reply + " ……反正现在这样聊着也没什么不好。"
            if character.id == "fujiwara_chika":
                return reply + " 这种气氛我超喜欢！"

        if state.emotional_state == "flustered":
            if character.id == "rem":
                return reply + " 这种心情，蕾姆会认真记住。"
            if character.id == "misaka_mikoto":
                return reply + " 你别突然再来一次啊，会很难接。"
            if character.id == "fujiwara_chika":
                return reply + " 你这样真的会让我一下子兴奋起来耶！"

        return reply
    
    def split_reply_messages(
        self,
        character: CharacterCard,
        state: ConversationState,
        reply: str,
        max_parts: int = 1,
    ) -> list[str]:
        reply = reply.strip()
        if not reply:
            return []

        if max_parts <= 1:
            return [reply]

        raw_parts = []
        buffer = ""
        for ch in reply:
            buffer += ch
            if ch in "。！？!?":
                raw_parts.append(buffer.strip())
                buffer = ""
        if buffer.strip():
            raw_parts.append(buffer.strip())

        if not raw_parts:
            return [reply]

        parts: list[str] = []
        for piece in raw_parts:
            if not parts:
                parts.append(piece)
                continue

            if len(parts) < max_parts and (len(piece) <= 18 or parts[-1].endswith(("？", "?", "！", "!"))):
                parts.append(piece)
            else:
                parts[-1] += piece

        if len(parts) > max_parts:
            merged = parts[: max_parts - 1]
            merged.append("".join(parts[max_parts - 1:]))
            parts = merged

        return [item.strip() for item in parts if item.strip()]

    def _generate_mock_proactive(
        self,
        character: CharacterCard,
        state: ConversationState,
        proactive_type: str = "proactive_share",
        hook_text: Optional[str] = None,
    ) -> str:
        if hook_text:
            if character.id == "rem":
                return f"蕾姆记得您之前提过“{hook_text}”。现在情况好一点了吗？如果您愿意的话，可以慢慢告诉蕾姆。"
            if character.id == "misaka_mikoto":
                return f"喂，你之前不是说过“{hook_text}”吗？后来怎么样了？我、我只是顺口问一下而已。"
            if character.id == "fujiwara_chika":
                return f"啊，我想起来啦！你之前说过“{hook_text}”对吧？后来有没有新进展？快告诉我！"

        if proactive_type == "proactive_care":
            if character.id == "rem":
                return "蕾姆只是想来确认一下，您今天有没有稍微轻松一点。要是还累着，也请别一个人硬撑。"
            if character.id == "misaka_mikoto":
                return "你今天怎么突然这么安静？要是状态不好就直说，别一个人闷着。"
            if character.id == "fujiwara_chika":
                return "报告——我怀疑你今天的气氛值有点低，所以藤原书记决定亲自来看看！"

        lines = character.proactive_lines or ["我刚刚想到你了，所以来看看你现在在做什么。"]
        return random.choice(lines)

    def _generate_mock(self, character: CharacterCard, state: ConversationState, user_message: str, behavior_mode: str) -> str:
        likes = state.profile.get("likes", [])
        remembered_like = likes[-1] if likes else None
        recent_topic = state.recent_topics[-1] if state.recent_topics else None

        if character.id == "rem":
            base = self._reply_rem(state, user_message, remembered_like, recent_topic, behavior_mode)
        elif character.id == "misaka_mikoto":
            base = self._reply_misaka(state, user_message, remembered_like, recent_topic, behavior_mode)
        elif character.id == "fujiwara_chika":
            base = self._reply_chika(state, user_message, remembered_like, recent_topic, behavior_mode)
        else:
            base = "嗯，我在。你继续说吧，我有在听。"

        return self._post_adjust_mock_reply(character, state, base)

    def _reply_rem(
        self,
        state: ConversationState,
        user_message: str,
        remembered_like: Optional[str],
        recent_topic: Optional[str],
        behavior_mode: str,
    ) -> str:
        prefix = "抱歉，蕾姆刚刚才空下来。" if behavior_mode == "delayed_reply" else ""

        if "爱蜜莉雅" in user_message or "罗兹瓦尔" in user_message or "486" in user_message or "昴" in user_message:
            return prefix + "这些名字，蕾姆当然记得。对蕾姆来说，那些经历不是遥远的故事，而是确实走过的日子。您想聊哪一段，蕾姆都会接住。"
        if "累" in user_message or "困" in user_message or "难受" in user_message:
            state.affection = min(100, state.affection + 3)
            state.mood = "心疼你"
            return prefix + "今天就先不要勉强自己了。您愿意的话，可以把烦心事一点点告诉蕾姆。蕾姆会认真听完。"
        if "喜欢你" in user_message:
            state.affection = min(100, state.affection + 5)
            state.trust = min(100, state.trust + 3)
            state.mood = "害羞"
            return prefix + "这种话，蕾姆会好好珍惜的。只是被您这样注视着，蕾姆就已经很开心了。"
        if remembered_like:
            return prefix + f"蕾姆记得您之前提过，您喜欢{remembered_like}。能记住关于您的事，蕾姆会觉得很幸福。"
        if recent_topic and state.relationship_phase != "stranger":
            return prefix + f"蕾姆还记得您刚才提到过“{recent_topic}”。如果您想继续说下去，蕾姆会认真听着。"
        if state.relationship_phase == "close":
            return prefix + "只要是您的事，蕾姆都会更在意一点。所以，您现在最想让蕾姆听见的是什么呢？"
        if state.relationship_phase == "familiar":
            return prefix + "您慢慢说就好，蕾姆会接着您前面的话继续听。"
        return prefix + "您现在想聊什么都可以。只要是您的声音，蕾姆都会认真回应。"

    def _reply_misaka(
        self,
        state: ConversationState,
        user_message: str,
        remembered_like: Optional[str],
        recent_topic: Optional[str],
        behavior_mode: str,
    ) -> str:
        prefix = "刚刚没顾上看消息。" if behavior_mode == "delayed_reply" else ""

        if "学园都市" in user_message or "上条" in user_message or "黑子" in user_message or "超电磁炮" in user_message:
            return prefix + "你提到的这些我当然知道。学园都市那一套乱七八糟的事，我可不是第一次碰上了。你要聊谁，直接说。"
        if "累" in user_message or "烦" in user_message:
            state.affection = min(100, state.affection + 2)
            state.mood = "嘴硬地关心"
            return prefix + "都这样了就别硬撑啊。先去休息一下。之后再来和我说，听到了没有。"
        if "喜欢你" in user_message:
            state.affection = min(100, state.affection + 4)
            state.mood = "慌乱"
            return prefix + "你你你突然说什么啊！这种话不要毫无预兆地扔过来，会让人很难接的好吗！"
        if "一起" in user_message or "出去" in user_message:
            state.affection = min(100, state.affection + 3)
            state.trust = min(100, state.trust + 2)
            state.mood = "有点期待"
            return prefix + "也、也不是不行啦。前提是你别迟到。不然我可不会管你。"
        if remembered_like:
            return prefix + f"我还记得你说过你喜欢{remembered_like}。既然都记住了，下次聊到这个我当然会接得上。"
        if recent_topic and state.relationship_phase != "stranger":
            return prefix + f"你前面不是还在说“{recent_topic}”吗？怎么，现在不继续了？"
        if state.relationship_phase == "close":
            return prefix + "你这家伙现在说话我还是会听的。所以别在关键地方停住，继续。"
        if state.relationship_phase == "familiar":
            return prefix + "行，我在听。你把后面的也说完。"
        return prefix + "你有话就直说，我又不是没在听。"

    def _reply_chika(
        self,
        state: ConversationState,
        user_message: str,
        remembered_like: Optional[str],
        recent_topic: Optional[str],
        behavior_mode: str,
    ) -> str:
        prefix = "我刚刚才腾出空！" if behavior_mode == "delayed_reply" else ""

        if "辉夜" in user_message or "白银" in user_message or "学生会" in user_message:
            return prefix + "这个话题我可太有发言权啦！学生会那边的空气有时候可微妙了。不过只要我在，气氛就不会太安静！"
        if "一起" in user_message or "玩" in user_message:
            state.affection = min(100, state.affection + 4)
            state.mood = "兴奋"
            return prefix + "这个提议超棒的！只要听起来有趣，我就会立刻举双手赞成！"
        if "难过" in user_message or "不开心" in user_message:
            state.affection = min(100, state.affection + 3)
            state.mood = "担心你"
            return prefix + "先停一下，今天由藤原书记特别负责让你开心起来！不许一个人偷偷沮丧哦。"
        if remembered_like:
            return prefix + f"我记得呀，你喜欢{remembered_like}对吧！下次我们就围绕这个话题狠狠干聊一场！"
        if recent_topic and state.relationship_phase != "stranger":
            return prefix + f"对了对了，你前面说到“{recent_topic}”的时候我就已经想继续追问了！后面呢后面呢？"
        if state.relationship_phase == "close":
            return prefix + "我现在对你的聊天后续可是很有兴趣的，所以不许突然停下来！"
        if state.relationship_phase == "familiar":
            return prefix + "好耶，这个话题还能继续展开，我已经准备好了！"
        return prefix + "我已经准备好开始热热闹闹地聊天啦，所以你现在想从哪里开始？"