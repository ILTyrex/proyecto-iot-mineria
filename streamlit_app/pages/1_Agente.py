import os
from pathlib import Path
from uuid import uuid4

import requests
import streamlit as st
from dotenv import load_dotenv


DEFAULT_FLOW_ID = "e6d3ba85-cb78-4ef1-aa18-917413ca33a9"

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
st.set_page_config(page_title="Agente | Calidad de aire", page_icon="🌬️", layout="wide")


def setting(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value
    try:
        return str(st.secrets.get(name, default))
    except (FileNotFoundError, KeyError):
        return default


def _find_text(value: object) -> str | None:
    if isinstance(value, dict):
        text = value.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()
        for key in ("message", "messages", "result", "results", "response", "data", "outputs"):
            if key in value:
                found = _find_text(value[key])
                if found:
                    return found
    elif isinstance(value, list):
        for item in reversed(value):
            found = _find_text(item)
            if found:
                return found
    return None


def response_text(payload: dict) -> str:
    text = _find_text(payload.get("outputs", []))
    if not text:
        raise ValueError("Langflow no devolvio un mensaje de respuesta.")
    return text


def ask_agent(question: str) -> str:
    langflow_url = setting("LANGFLOW_URL", "http://localhost:7860").rstrip("/")
    flow_id = setting("LANGFLOW_FLOW_ID", DEFAULT_FLOW_ID)

    headers = {"Content-Type": "application/json", "accept": "application/json"}
    api_key = setting("LANGFLOW_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key

    response = requests.post(
        f"{langflow_url}/api/v1/run/{flow_id}",
        headers=headers,
        json={
            "input_value": question,
            "input_type": "chat",
            "output_type": "chat",
            "session_id": st.session_state.langflow_session_id,
        },
        timeout=90,
    )
    response.raise_for_status()
    return response_text(response.json())


st.title("Agente de calidad del aire")
st.caption("Consultas analíticas sobre el histórico de sensores")

if "langflow_session_id" not in st.session_state:
    st.session_state.langflow_session_id = uuid4().hex
if "agent_messages" not in st.session_state:
    st.session_state.agent_messages = []

with st.sidebar:
    st.subheader("Ejemplos")
    st.markdown(
        "- ¿Cuál fue el promedio de CO₂ y cuál fue el máximo?\n"
        "- Compara los promedios del primer y segundo periodo.\n"
        "- ¿Qué tendencia tuvo la temperatura?\n"
        "- ¿Qué dispositivo registró más lecturas?"
    )
    if st.button("Nueva conversación", icon="🔄"):
        st.session_state.langflow_session_id = uuid4().hex
        st.session_state.agent_messages = []
        st.rerun()

for message in st.session_state.agent_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Pregunta sobre las lecturas, comparaciones o tendencias...")
if question:
    st.session_state.agent_messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Analizando el histórico..."):
            try:
                answer = ask_agent(question)
                st.markdown(answer)
                st.session_state.agent_messages.append({"role": "assistant", "content": answer})
            except (requests.RequestException, ValueError) as error:
                st.error(str(error))
                st.caption("Verifica que Langflow esté activo y que el Flow ID esté configurado.")