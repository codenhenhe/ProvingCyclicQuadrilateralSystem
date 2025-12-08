from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base + LoRA
base_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-3B-Instruct",
    torch_dtype="auto",
    device_map="auto"
)
model = PeftModel.from_pretrained(base_model, "yourusername/vn-geometry-qwen2.5-3b")

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")

# Prompt theo format của bạn (dài, chi tiết cho parsing)
system_msg = """Bạn là một API Backend vô cảm. Nhiệm vụ duy nhất: Phân tích văn bản đề bài hình học tiếng Việt và chuyển sang mảng JSON thuần theo schema. [DÁN TOÀN BỘ PROMPT TỐI ƯU CỦA BẠN VÀO ĐÂY]"""

user_msg = "DỮ LIỆU ĐẦU VÀO: Cho tam giác ABC đều. Đường cao AD và BE cắt nhau tại H. Chứng minh tứ giác CDHE nội tiếp."

messages = [
    {"role": "system", "content": system_msg},
    {"role": "user", "content": user_msg}
]

# Dùng apply_chat_template chuẩn HF
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
generated_ids = model.generate(
    **model_inputs,
    max_new_tokens=512,
    temperature=0.0,
    do_sample=False  # Để deterministic cho JSON
)

# Decode chỉ phần mới generate
generated_ids = [
    output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
]
response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

print(response)  # Sẽ ra JSON array sạch