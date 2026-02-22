import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

with open("app.py", "r") as f:
    code = f.read()

prompt = f"""
You are an autonomous AI developer.
Analyze the following Streamlit dashboard code.
Improve structure, performance, and clarity.
Return FULL updated file content.

{code}
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
)

new_code = response.choices[0].message.content

with open("app.py", "w") as f:
    f.write(new_code)

print("Agent updated app.py")
