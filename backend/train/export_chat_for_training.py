from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONVERSATION_DIR = ROOT / "app" / "data" / "conversations"
CHARACTER_DIR = ROOT / "app" / "data" / "characters"
OUTPUT_FILE = Path(__file__).resolve().parent / "exported_roleplay_training_data.jsonl"


def load_characters() -> dict:
    result = {}
    for file in CHARACTER_DIR.glob("*.json"):
        data = json.loads(file.read_text(encoding="utf-8"))
        result[data["id"]] = data
    return result


def build_system_prompt(character: dict, conversation: dict) -> str:
    return (
        f"你要扮演{character['name']}。"
        f"角色身份：{character['title']}。"
        f"角色来源：{character.get('source', '')}。"
        f"性格：{'、'.join(character.get('personality', []))}。"
        f"说话风格：{'、'.join(character.get('speech_style', []))}。"
        f"剧情知识：{'；'.join(character.get('world_knowledge', [])[:6])}。"
        f"当前剧情阶段：{conversation.get('story_stage', 'opening')}。"
        f"请保持角色一致，不要跳出人设。"
    )


def convert_one_file(path: Path, characters: dict) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not data.get("is_friend"):
        return []
    character_id = data.get("character_id")
    character = characters.get(character_id)
    if not character:
        return []

    messages = [m for m in data.get("messages", []) if m.get("role") in {"user", "assistant"}]
    samples = []
    for i in range(len(messages) - 1):
        current_msg = messages[i]
        next_msg = messages[i + 1]
        if current_msg.get("role") == "user" and next_msg.get("role") == "assistant":
            assistant_text = next_msg.get("content", "")
            if assistant_text.startswith("【事件解锁："):
                continue
            samples.append(
                {
                    "messages": [
                        {"role": "system", "content": build_system_prompt(character, data)},
                        {"role": "user", "content": current_msg.get("content", "")},
                        {"role": "assistant", "content": assistant_text},
                    ],
                    "metadata": {
                        "character_id": character_id,
                        "character_name": character.get("name"),
                        "story_stage": data.get("story_stage", "opening"),
                    },
                }
            )
    return samples


def main() -> None:
    characters = load_characters()
    all_samples = []
    for file in CONVERSATION_DIR.glob("*.json"):
        all_samples.extend(convert_one_file(file, characters))
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for sample in all_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    print(f"导出完成：{OUTPUT_FILE}")
    print(f"样本数量：{len(all_samples)}")


if __name__ == "__main__":
    main()