# import requests
#
# API_TOKEN = "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"
# API_URL = "https://api-inference.huggingface.co/models/google/mt5-base"
#
# headers = {
#     "Authorization": f"Bearer {API_TOKEN}",
#     "Content-Type": "application/json"
# }
#
# def query_mT5(prompt):
#     payload = {
#         "inputs": prompt,
#         "parameters": {
#             "max_length": 100,
#             "do_sample": True,
#             "temperature": 0.7
#         }
#     }
#     response = requests.post(API_URL, headers=headers, json=payload)
#     return response.json()
#
# # Пример использования
# result = query_mT5("Aké sú účinné lieky na horúčku?")
# print("Ответ от mT5:", result)

from transformers import AutoTokenizer, MT5ForConditionalGeneration

tokenizer = AutoTokenizer.from_pretrained("google/mt5-small")
model = MT5ForConditionalGeneration.from_pretrained("google/mt5-small")

# training
input_ids = tokenizer("The <extra_id_0> walks in <extra_id_1> park", return_tensors="pt").input_ids
labels = tokenizer("<extra_id_0> cute dog <extra_id_1> the <extra_id_2>", return_tensors="pt").input_ids
outputs = model(input_ids=input_ids, labels=labels)
loss = outputs.loss
logits = outputs.logits

# inference

input_ids = tokenizer(
    "summarize: studies have shown that owning a dog is good for you", return_tensors="pt"
).input_ids  # Batch size 1
outputs = model.generate(input_ids, max_new_tokens=50)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))

# studies have shown that owning a dog is good for you.
