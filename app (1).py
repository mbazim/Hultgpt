import streamlit as st
from openai import OpenAI
import os
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv


load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


client = OpenAI(api_key="OPENAI_API_KEY")


st.set_page_config(page_title="GPT Chat", page_icon="💬")
st.title("💬 Hult GPT v1.3 — ChatGPT Clone")


@retry(
    stop=stop_after_attempt(5), 
    wait=wait_exponential(multiplier=1, min=4, max=60),  
    retry=retry_if_exception_type(Exception),  
    before_sleep=lambda retry_state: st.info(f"API error. Reintentando en {retry_state.next_action.sleep} segundos...")
)
def create_chat_completion(messages, model):
    """Genera una respuesta de ChatGPT con manejo de errores"""
    try:
        return client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
    except Exception as e:
        if "rate limit" in str(e).lower() or "quota" in str(e).lower():
            logger.error(f"Rate limit error: {e}")
            st.error("Has alcanzado el límite de la API. La app intentará de nuevo.")
        else:
            logger.error(f"API error: {e}")
            st.error(f"Error: {e}")
        raise

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

st.sidebar.title("⚙️ Configuración")
selected_model = st.sidebar.selectbox(
    "Modelo de IA",
    ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4-turbo"],
    index=0
)
st.session_state["openai_model"] = selected_model

with st.sidebar.expander("📡 Estado de la API"):
    if st.button("🔄 Verificar API"):
        try:
            client.models.list()
            st.sidebar.success("✅ Conexión exitosa con OpenAI")
        except Exception as e:
            st.sidebar.error(f"❌ Error en API: {str(e)}")

if prompt := st.chat_input("Escribe tu mensaje aquí..."):

    st.session_state.messages.append({"role": "user", "content": prompt})

    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        try:
            stream = create_chat_completion(
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                model=st.session_state["openai_model"],
            )
            
            response = st.write_stream(stream)

          
            st.session_state.messages.append({"role": "assistant", "content": response})

        except Exception as e:
            st.error(f"Error tras varios intentos: {str(e)}")
            st.info("Intenta más tarde o contacta soporte.")