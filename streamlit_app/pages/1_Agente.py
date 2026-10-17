import os
from pathlib import Path
from textwrap import shorten
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


def api_request(method: str, path: str, **kwargs) -> requests.Response:
    api_url = setting("API_URL", "http://localhost:8000").rstrip("/")
    api_key = setting("API_KEY")
    if not api_key:
        raise ValueError("Falta configurar API_KEY en .env para guardar el historial.")

    headers = kwargs.pop("headers", {})
    headers["X-API-Key"] = api_key
    response = requests.request(
        method,
        f"{api_url}/api/conversaciones{path}",
        headers=headers,
        timeout=20,
        **kwargs,
    )
    response.raise_for_status()
    return response


def load_conversations() -> list[dict]:
    response = api_request("GET", "/", params={"limit": 50})
    return response.json()


def load_conversation(conversation_id: str) -> list[dict]:
    response = api_request("GET", f"/{conversation_id}")
    return response.json()["mensajes"]


def save_message(conversation_id: str, role: str, content: str) -> None:
    api_request(
        "POST",
        f"/{conversation_id}/mensajes",
        json={"role": role, "content": content},
    )


def open_conversation(conversation_id: str) -> None:
    stored_messages = load_conversation(conversation_id)
    st.session_state.langflow_session_id = conversation_id
    st.session_state.agent_messages = [
        {"role": message["role"], "content": message["content"]}
        for message in stored_messages
    ]


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
    suggested_question = None
    if st.button("Nueva conversación", icon=":material/edit_square:", width="stretch"):
        st.session_state.langflow_session_id = uuid4().hex
        st.session_state.agent_messages = []
        st.rerun()

    st.divider()
    st.caption("Historial")
    try:
        saved_conversations = load_conversations()
    except (requests.RequestException, ValueError) as error:
        saved_conversations = []
        st.warning(f"No se pudo cargar el historial: {error}", icon=":material/cloud_off:")

    current_id = st.session_state.langflow_session_id
    for conversation in saved_conversations:
        conversation_id = conversation["id"]
        title = conversation["titulo"].strip() or "Conversación nueva"
        if st.button(
            shorten(title, width=38, placeholder="..."),
            key=f"conversation_{conversation_id}",
            type="primary" if conversation_id == current_id else "secondary",
            width="stretch",
            help=title,
        ) and conversation_id != current_id:
            try:
                open_conversation(conversation_id)
                st.rerun()
            except (requests.RequestException, ValueError) as error:
                st.error(f"No se pudo abrir la conversación: {error}")

    st.divider()
    with st.expander("Preguntas de ejemplo", expanded=not st.session_state.agent_messages):
        suggestions = {
            "Promedio y máximo de CO₂": "¿Cuál fue el promedio de CO₂ y cuál fue el máximo?",
            "Comparar periodos": "Compara los promedios del primer y segundo periodo.",
            "Tendencia de temperatura": "¿Qué tendencia tuvo la temperatura?",
            "Dispositivo con más lecturas": "¿Qué dispositivo registró más lecturas?",
        }
        for index, (label, prompt) in enumerate(suggestions.items()):
            if st.button(label, key=f"suggestion_{index}", width="stretch"):
                suggested_question = prompt

for message in st.session_state.agent_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Pregunta sobre las lecturas, comparaciones o tendencias...")
if suggested_question:
    question = suggested_question

if question:
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Analizando el histórico..."):
            try:
                save_message(st.session_state.langflow_session_id, "user", question)
                st.session_state.agent_messages.append({"role": "user", "content": question})
                answer = ask_agent(question)
                st.markdown(answer)
                save_message(st.session_state.langflow_session_id, "assistant", answer)
                st.session_state.agent_messages.append({"role": "assistant", "content": answer})
            except requests.RequestException as error:
                st.error(f"No se pudo completar o guardar el mensaje: {error}")
                st.caption("Revisa que la API, Langflow y la API_KEY estén configurados.")
            except ValueError as error:
                st.error(str(error))
                st.caption("Verifica la configuración de API_KEY y LANGFLOW_FLOW_ID.")