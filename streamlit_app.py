"""Streamlit chat interface for medAgenda agent"""
import streamlit as st
import requests
import uuid
from datetime import datetime

# API Configuration
API_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="medAgenda - Agendamento de Consultas",
    page_icon="🏥",
    layout="centered"
)

# Custom CSS with high contrast colors
st.markdown("""
<style>
    /* Main container */
    .main {
        background-color: #ffffff;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        color: #1a1a1a;
        padding: 1rem 0;
        font-weight: bold;
    }
    
    /* Chat messages */
    .chat-message {
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        display: flex;
        flex-direction: column;
        box-shadow: 0 3px 6px rgba(0,0,0,0.15);
        font-size: 1.1rem;
        line-height: 1.7;
    }
    
    /* User message - Blue border, white background */
    .user-message {
        background-color: #ffffff;
        color: #000000;
        margin-left: 3rem;
        border: 3px solid #0066cc;
        border-left: 8px solid #0066cc;
    }
    
    /* Bot message - Green border, white background */
    .bot-message {
        background-color: #ffffff;
        color: #000000;
        margin-right: 3rem;
        border: 3px solid #00a86b;
        border-left: 8px solid #00a86b;
    }
    
    /* Message labels */
    .message-label {
        font-weight: bold;
        margin-bottom: 1rem;
        font-size: 1.2rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    .user-label {
        color: #0066cc;
    }
    
    .bot-label {
        color: #00a86b;
    }
    
    /* Warning box */
    .warning-box {
        background-color: #fff3cd;
        border: 3px solid #ff9800;
        border-left: 8px solid #ff6f00;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-radius: 8px;
        color: #000000;
        font-size: 1.05rem;
    }
    
    .warning-box strong {
        color: #d84315;
        font-size: 1.15rem;
    }
    
    /* Info box */
    .info-box {
        background-color: #e3f2fd;
        border: 3px solid #2196f3;
        border-left: 8px solid #1976d2;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-radius: 8px;
        color: #000000;
        font-size: 1.05rem;
    }
    
    .info-box strong {
        color: #0d47a1;
        font-size: 1.15rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #182331;
        color: #f8fafc;
    }

    [data-testid="stSidebar"] :is(h1, h2, h3, h4, p, li, label, small) {
        color: #f8fafc;
    }
    
    /* Button styling */
    .stButton button {
        background-color: #1976d2;
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.75rem 1.5rem;
        font-size: 1.05rem;
    }
    
    .stButton button:hover {
        background-color: #1565c0;
    }
    
    /* Chat input */
    .stChatInput {
        border: 2px solid #1976d2;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'api_available' not in st.session_state:
    # Check if API is available
    try:
        response = requests.get(f"{API_URL}/", timeout=2)
        st.session_state.api_available = response.status_code == 200
    except:
        st.session_state.api_available = False

# Header
st.markdown('<h1 class="main-header">🏥 medAgenda</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: inherit; font-size: 1.1rem; font-weight: 500;">Assistente Virtual para Agendamento de Consultas</p>', unsafe_allow_html=True)

# API Status Check
if not st.session_state.api_available:
    st.error("⚠️ **API não está disponível!**\n\nCertifique-se de que o servidor está rodando:\n```bash\nuv run --locked uvicorn app.main:app --port 8000\n```")
    st.stop()

# Safety Warning
with st.expander("⚠️ Importante - Sobre o Agente"):
    st.markdown("""
    <div class="warning-box">
        <strong>🔒 Restrições de Segurança:</strong>
        <ul>
            <li>Este agente <strong>NÃO</strong> fornece diagnósticos médicos</li>
            <li>Este agente <strong>NÃO</strong> recomenda tratamentos</li>
            <li>Este agente <strong>NÃO</strong> faz avaliações clínicas</li>
            <li>Função: <strong>APENAS</strong> coletar dados para agendamento</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Sidebar - Session Info
with st.sidebar:
    st.markdown("### 📊 Informações da Sessão")
    st.markdown(f"**ID:** `{st.session_state.session_id[:8]}...`")
    st.markdown(f"**Mensagens:** `{len(st.session_state.messages)}`")
    
    st.markdown("")
    if st.button("🔄 Nova Conversa", use_container_width=True, type="primary"):
        # Reset session on backend
        try:
            requests.post(f"{API_URL}/sessions/{st.session_state.session_id}/reset")
        except:
            pass
        
        # Reset frontend
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 📋 Agendamentos")
    if st.button("📅 Ver Agendamentos", use_container_width=True, type="secondary"):
        try:
            response = requests.get(f"{API_URL}/appointments?limit=10")
            if response.status_code == 200:
                data = response.json()
                st.markdown(f"**Total de agendamentos:** `{data['total']}`")
                for apt in data['appointments']:
                    with st.expander(f"**#{apt['id']}** - {apt['name']}", expanded=False):
                        st.markdown(f"📱 **Telefone:** `{apt['phone']}`")
                        st.markdown(f"🏥 **Especialidade:** `{apt['specialty']}`")
                        st.markdown(f"📅 **Data/Hora:** `{apt['preferred_datetime']}`")
                        st.markdown(f"📍 **Modo:** `{apt['mode']}`")
                        st.markdown(f"✅ **Status:** `{apt['status']}`")
        except Exception as e:
            st.error(f"❌ Erro ao buscar agendamentos: {e}")
    
    st.markdown("---")
    
    st.markdown("### ℹ️ Como Usar")
    st.markdown("""
    **Exemplos de mensagens:**
    
    - 🟢 "Oi, quero marcar consulta"
    - 🟢 "Me chamo João Silva, telefone 11 98765-4321"
    - 🟢 "Preciso de dermatologista"
    - 🟢 "Presencial, amanhã às 14h"
    - 🟢 "sim" (para confirmar)
    
    **Campos necessários:**
    - ✅ Nome completo
    - ✅ Telefone/WhatsApp
    - ✅ Especialidade
    - ✅ Data/horário preferido
    - ✅ Modo (presencial/online)
    """)

# Chat Display
st.markdown("---")

# Display chat messages
for msg in st.session_state.messages:
    if msg['role'] == 'user':
        st.markdown(f"""
        <div class="chat-message user-message">
            <div class="message-label user-label">👤 VOCÊ</div>
            <div style="font-size: 1.1rem; line-height: 1.7; color: #000000;">{msg['content']}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message bot-message">
            <div class="message-label bot-label">🤖 MEDAGENDA</div>
            <div style="font-size: 1.1rem; line-height: 1.7; color: #000000; white-space: pre-wrap;">{msg['content']}</div>
        </div>
        """, unsafe_allow_html=True)

# Chat Input
user_input = st.chat_input("Digite sua mensagem...")

if user_input:
    # Add user message to chat
    st.session_state.messages.append({
        'role': 'user',
        'content': user_input,
        'timestamp': datetime.now().isoformat()
    })
    
    # Send to API
    try:
        with st.spinner("🤔 Processando..."):
            response = requests.post(
                f"{API_URL}/chat",
                json={
                    "session_id": st.session_state.session_id,
                    "message": user_input,
                    "channel": "streamlit"
                },
                timeout=60
            )
        
        if response.status_code == 200:
            data = response.json()
            bot_reply = data['reply']
            
            # Add bot message to chat
            st.session_state.messages.append({
                'role': 'assistant',
                'content': bot_reply,
                'timestamp': datetime.now().isoformat()
            })
            
            st.rerun()
        else:
            # Try to extract error message from API response
            try:
                error_data = response.json()
                error_message = error_data.get('detail', f"Erro {response.status_code}")
            except:
                error_message = f"Erro na API: {response.status_code}"
            
            # Show appropriate icon based on status code
            if response.status_code == 429:
                st.warning(f"⏳ {error_message}")
            elif response.status_code in [503, 504]:
                st.warning(f"⚠️ {error_message}")
            else:
                st.error(f"❌ {error_message}")
            
    except requests.exceptions.Timeout:
        st.error("⏱️ Timeout - A API demorou muito para responder. Tente novamente em alguns segundos.")
    except requests.exceptions.ConnectionError:
        st.error("🔌 Erro de conexão - Verifique se a API está rodando")
    except Exception as e:
        st.error(f"❌ Erro inesperado: {str(e)}")

# Initial greeting if no messages
if len(st.session_state.messages) == 0:
    st.markdown("""
    <div class="info-box">
        <strong>👋 Bem-vindo ao medAgenda!</strong><br><br>
        Sou seu assistente virtual para agendamento de consultas médicas.<br><br>
        <strong>Digite "Oi" ou "Quero marcar consulta" para começar!</strong>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<p style="text-align: center; color: inherit; opacity: 0.8; font-size: 0.9rem; font-weight: 500;">
    ⚡ medAgenda POC - Powered by LangGraph & FastAPI
</p>
""", unsafe_allow_html=True)
