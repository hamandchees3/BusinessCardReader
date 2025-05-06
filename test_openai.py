import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("openai_api"))

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Just say OK"}]
)
print(response.choices[0].message.content)

