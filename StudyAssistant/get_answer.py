def get_answer(self, question_text):
    prompt = f"""
You are a smart study assistant.

Answer this question.
If MCQ, return only correct option.

Format:
ANSWER: A/B/C/D
OPTION: exact option text
WHY: short explanation

Question:
{question_text}
"""

    response = requests.post(
        self.url,
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    data = response.json()
    print("DEBUG:", data)  # 👈 helps debugging

    if "response" not in data:
        raise Exception(f"Ollama error: {data}")

    return self.parse(data["response"])