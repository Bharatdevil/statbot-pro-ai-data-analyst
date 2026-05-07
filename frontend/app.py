import os
from typing import Any

import requests
import streamlit as st


API_BASE_URL = os.getenv("STATBOT_API_URL", "http://127.0.0.1:8000")


def api_url(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def show_api_error(response: requests.Response) -> None:
    try:
        detail: Any = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text
    st.error(detail or "Request failed.")


st.set_page_config(page_title="StatBot Pro", layout="centered")
st.title("StatBot Pro")
st.caption("AI CSV Data Analyst Agent")

if "filename" not in st.session_state:
    st.session_state.filename = None
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Dataset")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file and st.button("Upload", use_container_width=True):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
        try:
            response = requests.post(api_url("/upload-csv"), files=files, timeout=60)
            if response.ok:
                result = response.json()
                st.session_state.filename = result["filename"]
                st.session_state.messages = []
                st.success(result.get("message", "Upload successful"))
            else:
                show_api_error(response)
        except requests.RequestException as exc:
            st.error(f"Backend unavailable: {exc}")

    if st.session_state.filename:
        st.info(st.session_state.filename)
        try:
            info_response = requests.get(api_url(f"/dataset-info/{st.session_state.filename}"), timeout=30)
            if info_response.ok:
                info = info_response.json()
                st.write(f"Rows: {info['rows']}")
                st.write(f"Columns: {info['columns_count']}")
                st.dataframe(info["preview"], use_container_width=True)
        except requests.RequestException:
            st.warning("Could not load dataset preview.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("chart_url"):
            st.image(api_url(message["chart_url"]), use_container_width=True)

prompt = st.chat_input("Ask about your CSV...")
if prompt:
    if not st.session_state.filename:
        st.warning("Upload a CSV first.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    payload = {"filename": st.session_state.filename, "query": prompt}
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                response = requests.post(api_url("/analyze"), json=payload, timeout=120)
                if response.ok:
                    result = response.json()
                    answer = result.get("answer", "")
                    chart_url = result.get("chart_url")
                    st.markdown(answer)
                    if chart_url:
                        st.image(api_url(chart_url), use_container_width=True)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer, "chart_url": chart_url}
                    )
                else:
                    show_api_error(response)
            except requests.RequestException as exc:
                st.error(f"Backend unavailable: {exc}")
