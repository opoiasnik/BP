import requests


API_TOKEN = "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"
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"


headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def query_flan_t5(prompt):
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_length": 250,
            "do_sample": True,
            "temperature": 0.9,
            "top_p": 0.95,
            "top_k": 50
        }
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()


prompt = "Ako sa máš? Daj odpoved v slovencine"
result = query_flan_t5(prompt)

if isinstance(result, list) and len(result) > 0:
    print("Ответ от Flan-T5:", result[0]['generated_text'])
else:
    print("Ошибка при получении ответа:", result)