import base64, json, os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("bizcard"))

_SCHEMA = {
    "name": "extract_contact",
    "description": "Extract contact info from a business card photo",
    "parameters": {
        "type": "object",
        "properties": {
            "name":        {"type": "string"},
            "job_title":   {"type": "string"},
            "organization":{"type": "string"},
            "email":       {"type": "string"},
            "phone":       {"type": "string"}
        },
        "required": ["name", "email"]
    }
}

def _b64(bytestr):
    return "data:image/jpeg;base64," + base64.b64encode(bytestr).decode()

def extract_contact(image_bytes: bytes) -> dict:
    messages = [{
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": (
                    # 👇 NEW, longer instruction
                    "Extract the fields listed in the function schema. "
                    "For **organization**, always pick the top‑level company name. "
                    "If the email domain (text after the @‑sign) points to a company "
                    "different from a department name printed on the card, "
                    "use the domain’s company name instead. "
                    "Return JSON only—no extra keys."
                )
            },
            {
                "type": "image_url",
                "image_url": {"url": _b64(image_bytes)}
            }
    ]}]

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=[{"type": "function", "function": _SCHEMA}],
        tool_choice={"type": "function",
                     "function": {"name": "extract_contact"}}
    )
    return json.loads(resp.choices[0].message.tool_calls[0].function.arguments)

