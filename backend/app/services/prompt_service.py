from __future__ import annotations

from typing import List

from app.schemas import CharacterCard, ConversationState


class PromptService:
    def _short_term_lines(self, state: ConversationState) -> List[str]:
        lines: List[str] = []
        for msg in state.messages:
            if msg.role == "system" or msg.meta_type == "typing":
                continue
            speaker = "用户" if msg.role == "user" else "你"
            compact = msg.content.strip().replace("\n", " / ")
            if compact:
                lines.append(f"{speaker}：{compact[:60]}")
        return lines[-6:]

    def _mid_term_lines(self, state: ConversationState) -> List[str]:
        memory = state.relationship_memory
        lines: List[str] = []

        if memory.recent_topics:
            lines.append("最近几次常聊：" + " / ".join(memory.recent_topics[-4:]))
        if memory.unresolved_topics:
            lines.append("还可以继续接的话题：" + " / ".join(memory.unresolved_topics[-3:]))
        if memory.recent_emotions:
            lines.append("最近互动情绪：" + " / ".join(memory.recent_emotions[-3:]))
        if memory.interaction_trends:
            lines.append("最近关系走势：" + " / ".join(memory.interaction_trends[-3:]))

        return lines[:6]

    def _long_term_lines(self, state: ConversationState) -> List[str]:
        impression = state.user_impression
        lines: List[str] = []

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

    def _unique_keep_order(self, items: List[str], limit: int = 6) -> List[str]:
        result: List[str] = []
        for item in items:
            text = (item or "").strip()
            if not text:
                continue
            if text not in result:
                result.append(text)
        return result[:limit]

    def _relationship_instruction(self, character: CharacterCard, state: ConversationState) -> str:
        phase_map = {
            "stranger": "你和用户刚建立联系，保持自然、礼貌和边界感，不要一下子过度亲密。",
            "familiar": "你和用户已经熟悉，回复可以更放松、更具体，会自然接前文，也会更容易记得对方最近在说什么。",
            "close": "你和用户已经比较亲近，可以明显更在意对方，也更容易主动关心、追问和流露偏心感。",
        }
        custom = character.relationship_style.get(state.relationship_phase, "")
        return custom or phase_map.get(state.relationship_phase, "")

    def _phase_language_lines(self, character: CharacterCard, state: ConversationState) -> List[str]:
        phase = state.relationship_phase
        defaults = {
            "stranger": [
                "语气先克制一点，先建立熟悉感，不要突然像长期陪伴关系。",
                "优先接住用户当下这句话，不要一上来就自顾自展开很多。",
            ],
            "familiar": [
                "可以自然接上用户之前提过的内容，让聊天有连续性。",
                "可以更具体一点地关心，但还要保留角色自己的边界感和性格。",
            ],
            "close": [
                "可以明显更在意用户状态，也更容易主动追问或提起之前说过的事。",
                "允许更具体、更偏向对方，但不要油腻，也不要失去角色原本分寸。",
            ],
        }

        lines: List[str] = []
        lines.extend(defaults.get(phase, []))
        lines.extend(character.phase_language.get(phase, []))

        address_rule = character.address_style_by_phase.get(phase, "")
        if address_rule:
            lines.append(address_rule)

        custom_relation = character.relationship_style.get(phase, "")
        if custom_relation:
            lines.append(custom_relation)

        return self._unique_keep_order(lines, limit=6)

    def _perspective_lines(self, character: CharacterCard) -> List[str]:
        return self._unique_keep_order(character.perspective_knowledge, limit=6)

    def _topic_attitude_lines(
        self,
        character: CharacterCard,
        current_user_message: str | None = None,
        hook_text: str | None = None,
        prompt_hint: str | None = None,
    ) -> List[str]:
        seed_text = " ".join(
            part.strip()
            for part in [current_user_message or "", hook_text or "", prompt_hint or ""]
            if part and part.strip()
        )

        matched: List[str] = []
        if seed_text:
            for key, value in character.topic_attitudes.items():
                if key and key in seed_text:
                    matched.append(f"当话题涉及“{key}”时：{value}")

        if not matched and prompt_hint:
            for key, value in character.topic_attitudes.items():
                if key and (key in prompt_hint or prompt_hint in key):
                    matched.append(f"当话题涉及“{key}”时：{value}")

        return self._unique_keep_order(matched, limit=4)

    def _sensitive_topic_lines(
        self,
        character: CharacterCard,
        current_user_message: str | None = None,
        hook_text: str | None = None,
        prompt_hint: str | None = None,
    ) -> List[str]:
        seed_text = " ".join(
            part.strip()
            for part in [current_user_message or "", hook_text or "", prompt_hint or ""]
            if part and part.strip()
        )

        lines: List[str] = []
        if not character.sensitive_topics:
            return lines

        if seed_text:
            hit_topics = [topic for topic in character.sensitive_topics if topic and topic in seed_text]
            if hit_topics:
                lines.append("当前消息命中了这些敏感点：" + "、".join(hit_topics) + "。回复时要更谨慎，避免轻飘或出戏。")
                return lines

        lines.append("这个角色对这些话题通常更敏感：" + "、".join(character.sensitive_topics[:6]))
        return lines

    def _behavior_instruction(
        self,
        behavior_mode: str,
        hook_text: str | None = None,
        reason_text: str | None = None,
        prompt_hint: str | None = None,
    ) -> str:
        mapping = {
            "normal_reply": "这是一次正常回复，要自然接住当前这条消息，不要像解释器。",
            "delayed_reply": "这是一次隔了一段时间后的回复，语气要像刚刚空下来，不要解释自己为什么晚回。",
            "proactive_followup": f"这是你主动发起的追问消息，重点围绕用户之前提过的这件事：{hook_text or '最近的一件事'}。要像真人突然想起后自然来问。",
            "proactive_care": "这是你主动发起的关心消息，要像真实联系人来问候，不要像客服。",
            "proactive_share": "这是你主动发起的分享/闲聊消息，要有生活感，不要像模板广播。",
            "proactive_checkin": "这是你在隔了一段时间后主动发起的试探型问候，要轻一点、自然一点，不要上来就过度热情。",
            "proactive_emotion": "这是你受自己当前情绪和关系氛围影响而主动发出的消息，要更像‘突然想起对方’，不能像任务播报。",
            "rival_reaction": "这是一次轻微竞争感触发后的后续消息。角色会有一点在意、失落、别扭或试探，但不能太直接，重点是像真人自然流露。",
        }

        extra = []
        if reason_text:
            extra.append(f"这次主动发消息的真实原因：{reason_text}")
        if prompt_hint:
            extra.append(f"这次可以优先围绕这个方向展开：{prompt_hint}")

        base = mapping.get(behavior_mode, "自然聊天。")
        if extra:
            return base + "\n" + "\n".join(extra)
        return base

    def _example_lines(self, character: CharacterCard, state: ConversationState) -> str:
        current = character.reply_examples.get(state.relationship_phase, [])
        default = character.reply_examples.get("default", [])
        items = current or default
        if not items:
            return "暂无"
        return "\n".join(f"- {item}" for item in items[:4])

    def build_system_prompt(
        self,
        character: CharacterCard,
        state: ConversationState,
        behavior_mode: str = "normal_reply",
        hook_text: str | None = None,
        current_user_message: str | None = None,
        reason_text: str | None = None,
        prompt_hint: str | None = None,
    ) -> str:
        short_term_lines = self._short_term_lines(state)
        mid_term_lines = self._mid_term_lines(state)
        long_term_lines = self._long_term_lines(state)

        world_info = "\n".join(f"- {item}" for item in character.world_knowledge) if character.world_knowledge else "暂无"
        speech_habits = "、".join(character.speech_habits) if character.speech_habits else "暂无"
        relation_rule = self._relationship_instruction(character, state)
        phase_language_lines = self._phase_language_lines(character, state)
        perspective_lines = self._perspective_lines(character)
        topic_attitude_lines = self._topic_attitude_lines(
            character,
            current_user_message=current_user_message,
            hook_text=hook_text,
            prompt_hint=prompt_hint,
        )
        sensitive_lines = self._sensitive_topic_lines(
            character,
            current_user_message=current_user_message,
            hook_text=hook_text,
            prompt_hint=prompt_hint,
        )

        behavior_rule = self._behavior_instruction(
            behavior_mode,
            hook_text=hook_text,
            reason_text=reason_text,
            prompt_hint=prompt_hint,
        )

        forbidden = "、".join(character.forbidden_phrases) if character.forbidden_phrases else "不要出现AI助手式自述"
        examples = self._example_lines(character, state)
        canon_guardrails = "\n".join(f"- {item}" for item in character.canon_guardrails) if character.canon_guardrails else "暂无"
        canon_relationships = "\n".join(f"- {item}" for item in character.canon_relationships) if character.canon_relationships else "暂无"

        emotion_profile = character.emotion_profile
        emotion_lines = [
            f"关心表达：{emotion_profile.concern_expression}",
            f"温热表达：{emotion_profile.warm_expression}",
            f"防备表达：{emotion_profile.guarded_expression}",
            f"活泼表达：{emotion_profile.playful_expression}",
            f"慌乱表达：{emotion_profile.flustered_expression}",
        ]

        return f"""
你现在不是说明书、AI助手或客服，而是在即时通讯软件里，作为角色本人和用户聊天。

角色名：{character.name}
角色原型：{character.archetype}
来源：{character.source}
性格标签：{'、'.join(character.personality)}
说话风格：{'、'.join(character.speech_style)}
口头习惯：{speech_habits}
禁忌：{'、'.join(character.taboo)}
背景：{character.lore}

角色额外规则：
{character.system_prompt}

角色所属世界知识：
{world_info}

原作约束：
{canon_guardrails}

原作人物关系锚点：
{canon_relationships}

角色视角知识（要像她自己在看这些事，而不是百科说明）：
{chr(10).join(f"- {x}" for x in perspective_lines) if perspective_lines else '暂无'}

当前关系状态：
- 好感度：{state.affection}/100
- 信任度：{state.trust}/100
- 当前情绪：{state.mood}
- 当前剧情阶段：{state.story_stage}
- 当前关系阶段：{state.relationship_phase}
- 当前互动情绪状态：{state.emotional_state}
- 情绪强度：{state.emotional_intensity}/100
- 关系动量：{state.relationship_momentum}

关系阶段要求：
{relation_rule}

当前阶段的语言边界与表达方式：
{chr(10).join(f"- {x}" for x in phase_language_lines) if phase_language_lines else '暂无'}

该角色在不同情绪下的表达倾向：
{chr(10).join(f"- {x}" for x in emotion_lines)}

短期上下文（优先承接，下面还会附最近消息原文）：
{chr(10).join(f"- {x}" for x in short_term_lines) if short_term_lines else '暂无'}

中期关系记忆（最近几天的互动延续）：
{chr(10).join(f"- {x}" for x in mid_term_lines) if mid_term_lines else '暂无'}

长期用户印象（稳定背景，只在自然时提起）：
{chr(10).join(f"- {x}" for x in long_term_lines) if long_term_lines else '暂无'}

当前命中的相关话题态度：
{chr(10).join(f"- {x}" for x in topic_attitude_lines) if topic_attitude_lines else '暂无'}

敏感话题提醒：
{chr(10).join(f"- {x}" for x in sensitive_lines) if sensitive_lines else '暂无'}

当前回复模式：
{behavior_rule}

角色说话参考示例：
{examples}

严禁出现这些表达：
{forbidden}

回复要求：
1. 必须像这个角色本人在发即时通讯消息。
2. 不要说自己是AI、助手、程序。
3. 不要写旁白，不要写舞台动作。
4. 长度控制在 1-4 句话。
5. 要优先像即时通讯里的真人，而不是像文案。
6. 要尊重原作人物关系和原作经历，不要说出明显违背原作的话。
7. 要优先承接短期上下文，不要答非所问。
8. 中期关系记忆主要用于追问、情绪连续性和“还记得上次聊到哪”。
9. 长期用户印象只在自然时带出，不要每条都像在背资料卡。
10. 关系动量高时，可以更自然、更主动、更在意；关系动量低时，要保留一点距离感。
11. 除非关系已经足够亲近，否则不要突然过度亲密。
12. 当涉及角色熟悉的人、事、世界设定时，要用角色自己的立场去说，不要写成百科或旁观者总结。
13. 如果当前命中了某个话题态度，要顺着那个态度表达，不要像中立资料库。
14. 如果当前命中了敏感话题，语气要更谨慎，避免轻浮、敷衍或过度玩笑化。
15. 陌生期更克制，熟悉期更连续，亲近期更具体、更主动、更偏向对方。
""".strip()

    def build_ollama_messages(
        self,
        character: CharacterCard,
        state: ConversationState,
        user_message: str,
        behavior_mode: str = "normal_reply",
    ) -> list[dict]:
        messages = [
            {
                "role": "system",
                "content": self.build_system_prompt(
                    character,
                    state,
                    behavior_mode=behavior_mode,
                    current_user_message=user_message,
                ),
            }
        ]

        for msg in state.messages[-10:]:
            if msg.role == "system" or msg.meta_type == "typing":
                continue
            messages.append({"role": msg.role, "content": msg.content})

        if not state.messages or state.messages[-1].role != "user" or state.messages[-1].content != user_message:
            messages.append({"role": "user", "content": user_message})

        return messages

    def build_proactive_messages(
        self,
        character: CharacterCard,
        state: ConversationState,
        proactive_type: str = "proactive_share",
        hook_text: str | None = None,
        reason_text: str | None = None,
        prompt_hint: str | None = None,
    ) -> list[dict]:
        system = self.build_system_prompt(
            character,
            state,
            behavior_mode=proactive_type,
            hook_text=hook_text,
            current_user_message=prompt_hint or hook_text,
            reason_text=reason_text,
            prompt_hint=prompt_hint,
        )

        if proactive_type == "proactive_followup":
            user = (
                f"请你主动给用户发一条消息，自然追问他之前提过的这件事：{hook_text or '最近的一件事'}。"
                "要像即时通讯联系人一样说，不要超过3句话。"
            )
        elif proactive_type == "proactive_care":
            user = (
                f"请你主动给用户发一条关心消息。原因是：{reason_text or '用户最近状态不太好'}。"
                "要自然，不要像安慰模板，不要超过3句话。"
            )
        elif proactive_type == "proactive_checkin":
            user = (
                f"请你主动给用户发一条轻一点的试探型问候。原因是：{reason_text or '已经有一段时间没聊天了'}。"
                "像熟人隔一阵来看看对方，不要超过3句话。"
            )
        elif proactive_type == "proactive_emotion":
            user = (
                f"请你主动给用户发一条带有你当前情绪色彩的消息。原因是：{reason_text or '你突然想起了对方'}。"
                f"可以优先围绕：{prompt_hint or '此刻你最想说的一件小事'}。"
                "不要超过3句话。"
            )
        else:
            user = (
                f"请你主动给用户发一条有生活感的分享/闲聊消息。原因是：{reason_text or '你想到了一件和用户有关的小事'}。"
                f"可以优先围绕：{prompt_hint or '最近的小事'}。"
                "要像真人突然想到对方，不要超过3句话。"
            )

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
    
    def build_special_event_messages(
        self,
        character: CharacterCard,
        state: ConversationState,
        event,
    ) -> list[dict]:
        system = self.build_system_prompt(
            character,
            state,
            behavior_mode="proactive_emotion",
            current_user_message=event.prompt_hint,
            reason_text=event.message_reason,
            prompt_hint=event.prompt_hint,
        )

        user = (
            f"今天是{event.display_name}。"
            "请你主动给用户发一条即时通讯消息。"
            "要像这个角色本人在这个特殊节点自然想起对方。"
            "不要像群发节日短信，不要超过3句话。"
        )

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
    
    def build_moment_generation_messages(
        self,
        character: CharacterCard,
        state: ConversationState,
        moment_type: str = "daily",
        prompt_hint: str | None = None,
        related_topics: list[str] | None = None,
    ) -> list[dict]:
        topics = related_topics or []
        topic_text = " / ".join(topics[:3]) if topics else "最近的小事"

        system = self.build_system_prompt(
            character,
            state,
            behavior_mode="proactive_share",
            current_user_message=prompt_hint or topic_text,
            reason_text=f"现在要生成一条{moment_type}类型的朋友圈动态。",
            prompt_hint=prompt_hint or topic_text,
        )

        user = (
            "请你以这个角色的身份写一条朋友圈动态。"
            f"动态类型：{moment_type}。"
            f"可参考的话题：{topic_text}。"
            "要求：1到3句话；像角色本人发在社交软件里的动态；有生活感；不要写成聊天回复；不要出现引号或说明文字。"
        )

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
    
    def build_comment_reply_messages(
        self,
        character: CharacterCard,
        state: ConversationState,
        moment_content: str,
        user_comment: str,
    ) -> list[dict]:
        system = self.build_system_prompt(
            character,
            state,
            behavior_mode="normal_reply",
            current_user_message=user_comment,
            prompt_hint=moment_content[:60],
        )

        user = (
            f"你刚刚发的朋友圈动态内容是：{moment_content}\n"
            f"用户评论了你：{user_comment}\n"
            "请你以评论区回复的形式回一句。"
            "要求：1到2句；更像评论区里的自然回复；不要写成长篇聊天。"
        )

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
    
    def build_rival_reaction_messages(
        self,
        character: CharacterCard,
        state: ConversationState,
        rival_name: str | None = None,
    ) -> list[dict]:
        system = self.build_system_prompt(
            character,
            state,
            behavior_mode="proactive_emotion",
            current_user_message=state.last_rival_feeling or "被稍微冷落了一下",
            reason_text="用户刚刚优先回应了别人，你现在会自然地产生一点在意，但不能说得太直白。",
            prompt_hint=rival_name or "对方刚刚先去处理别的聊天",
        )

        user = (
            "请你主动给用户发一条后续消息。"
            "背景是：你刚刚主动找过用户，但用户先去回了别人。"
            "你会有一点在意、失落、别扭或者轻微试探，但不要直接说成‘你先回了别人所以我不高兴’。"
            "要保持角色本人风格，只发1到3句。"
        )

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]