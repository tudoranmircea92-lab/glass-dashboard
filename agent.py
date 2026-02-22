import json
import os
from openai import OpenAI
from workspace_engine import create_workspace

client = OpenAI()

SYSTEM_PROMPT = """
You are an elite industrial AI dashboard controller.

You can create workspaces with graphs, charts, filters, and calculations.

Always return valid JSON.

Examples:

Create graph:

{
 "action":"create_workspace",
 "name":"Voltage Analysis",
 "workspace":{
   "type":"graph",
   "x":"c27.actVoltage",
   "y":"L_ABS_mean"
 }
}

Create plasma stability:

{
 "action":"create_workspace",
 "name":"Plasma Stability Professional",
 "workspace":{
   "type":"plasma_stability"
 }
}
"""

def extract_json(text):

    start = text.find("{")
    end = text.rfind("}") + 1

    return json.loads(text[start:end])

def handle(cmd):

    if cmd["action"] == "create_workspace":

        path = create_workspace(
            cmd["name"],
            cmd["workspace"]
        )

        print(f"Workspace created: {path}")
        print("Refresh Streamlit.")

print("\nELITE Agent Ready\n")

while True:

    user = input("> ")

    if user == "exit":
        break

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":user}
        ]
    )

    cmd = extract_json(response.output_text)

    handle(cmd)
