import os
from openai import OpenAI

client = OpenAI()

APP_FILE = "app.py"

def generate_streamlit_code(x_col, y_col):

    return f'''
import streamlit as st
import pyarrow.parquet as pq
import plotly.express as px

FILE = "db2026.02.19.parquet"

st.title("AI Generated Chart")

pf = pq.ParquetFile(FILE)
batch = next(pf.iter_batches(batch_size=50000))
df = batch.to_pandas()

st.write("Showing relationship between {x_col} and {y_col}")

fig = px.scatter(df, x="{x_col}", y="{y_col}")

st.plotly_chart(fig, use_container_width=True)
'''

def update_streamlit_app(code):

    with open(APP_FILE, "w") as f:
        f.write(code)

def parse_request(user_input):

    prompt = f"""
Extract two column names from this request:

{user_input}

Return ONLY in format:
x_col,y_col
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return response.output_text.strip()

print("\nAI Streamlit Controller")
print("Example: plot c27.actVoltage vs L_ABS_mean")
print("Type exit to quit\n")

while True:

    user_input = input("> ")

    if user_input.lower() == "exit":
        break

    try:

        parsed = parse_request(user_input)

        x_col, y_col = parsed.split(",")

        code = generate_streamlit_code(x_col, y_col)

        update_streamlit_app(code)

        print(f"\nUpdated Streamlit with chart: {x_col} vs {y_col}")
        print("Refresh browser.\n")

    except Exception as e:

        print("Error:", e)
