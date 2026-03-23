"""
这是一个 LoRA 微调模板，不是你第一步必须运行的内容。

建议你先把聊天软件本体跑起来，再做训练。

运行前你需要：
1. 有 NVIDIA GPU 环境
2. 安装 unsloth、transformers、datasets、trl、peft、accelerate
3. 修改下面的模型名、数据路径、输出路径
"""

from datasets import load_dataset

BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DATASET_PATH = "sample_roleplay_dataset.jsonl"
OUTPUT_DIR = "outputs/lora-roleplay"
MAX_SEQ_LENGTH = 2048


def format_messages(example):
    messages = example["messages"]
    text = ""
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        text += f"<|{role}|>\n{content}\n"
    return {"text": text}


def main():
    try:
        from unsloth import FastLanguageModel
        from trl import SFTTrainer, SFTConfig
    except ImportError:
        raise SystemExit(
            "你还没有安装训练依赖。请先在 GPU 环境安装 unsloth / trl / transformers / datasets / peft / accelerate。"
        )

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
        load_in_4bit=True,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )

    dataset = load_dataset("json", data_files=DATASET_PATH, split="train")
    dataset = dataset.map(format_messages)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        args=SFTConfig(
            output_dir=OUTPUT_DIR,
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            warmup_steps=10,
            num_train_epochs=2,
            learning_rate=2e-4,
            logging_steps=1,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=3407,
            report_to="none",
        ),
    )

    trainer.train()
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"训练完成，LoRA 已保存到：{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
