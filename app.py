import streamlit as st
import sqlite3
import pandas as pd

# 1. Configuração e Conexão com Banco de Dados SQLite
DB_FILE = "sistema_agendor_custom.db"

def criar_banco():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            documento TEXT PRIMARY KEY,
            tipo TEXT NOT NULL,
            nome TEXT NOT NULL,
            rg TEXT,
            data_nascimento TEXT,
            orgao_emissor TEXT,
            data_fundacao TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            documento_cliente TEXT NOT NULL,
            etapa TEXT NOT NULL,
            observacoes TEXT DEFAULT '',
            FOREIGN KEY(documento_cliente) REFERENCES clientes(documento)
        )
    ''')
    conn.commit()
    conn.close()

def buscar_cliente(doc):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT nome, tipo FROM clientes WHERE documento = ?", (doc,))
    res = c.fetchone()
    conn.close()
    return res

def salvar_cliente(doc, tipo, nome, rg=None, dt_nasc=None, orgao=None, dt_fund=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO clientes (documento, tipo, nome, rg, data_nascimento, orgao_emissor, data_fundacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (doc, tipo, nome, rg, dt_nasc, orgao, dt_fund))
    conn.commit()
    conn.close()

def criar_novo_pedido(doc):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO pedidos (documento_cliente, etapa) VALUES (?, 'Pedido Criado')", (doc,))
    conn.commit()
    conn.close()

def atualizar_pedido(id_ped, nova_etapa, novas_obs):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE pedidos SET etapa = ?, observacoes = ? WHERE id = ?", (nova_etapa, novas_obs, id_ped))
    conn.commit()
    conn.close()

def carregar_fluxo():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query('''
        SELECT p.id, p.documento_cliente, p.etapa, p.observacoes, c.nome, c.tipo
        FROM pedidos p
        JOIN clientes c ON p.documento_cliente = c.documento
    ''', conn)
    conn.close()
    return df

criar_banco()

# Lista global estável com as 8 etapas solicitadas
ETAPAS_GLOBAL = [
    "Pedido Criado", "Confirmar Pix", "Faturar Notas", 
    "Faturar Entregar e Receber", "Cliente vem Buscar", 
    "Entregas via Tecar", "Transportadora", "Pedido Finalizado"
]

# Inicialização de variáveis de controle de janelas na memória do navegador
if "pedido_selecionado" not in st.session_state:
    st.session_state.pedido_selecionado = None
if "aba_aberta" not in st.session_state:
    st.session_state.aba_aberta = None

# 2. Interface Estilizada e Configuração de Cores (Design Minimalista Branco/Preto)
st.set_page_config(layout="wide", page_title="Gestão de Fluxo", page_icon="📋")

# Aplicação de CSS Inteligente - Sem quebrar cliques e forçando o Tema Claro Rígido
st.markdown("""
    <style>
    /* Força o fundo de toda a página para BRANCO Puro */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMainBlockContainer"] {
        background-color: #ffffff !important;
    }
    
    /* Força todas as fontes, títulos e labels para PRETO */
    h1, h2, h3, h4, h5, h6, p, span, label, li, div, .stMarkdown {
        color: #000000 !important;
    }
    
    /* Configuração e linhas divisórias verticais cinzas entre as abas */
    div[data-testid="stHorizontalBlock"] {
        align-items: stretch !important;
        background-color: #ffffff !important;
    }
    
    div[data-testid="column"] {
        padding-right: 8px !important;
        padding-left: 8px !important;
        border-right: 1px solid #cccccc !important; /* Divisa cinza nítida */
    }
    
    div[data-testid="column"]:last-child {
        border-right: none !important;
    }
    
    /* ALINHAMENTO DAS ETAPAS DO TOPO: Garante tamanho fixo idêntico para todas as caixas */
    .topo-coluna {
        background-color: #ffffff;
        border: 1px solid #000000; /* Contorno preto fino */
        padding: 6px 4px;
        border-radius: 4px;
        text-align: center;
        margin-bottom: 20px;
        height: 58px; /* Altura ideal para alinhar textos de duas linhas */
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0px 1px 2px rgba(0,0,0,0.05);
    }
    
    .texto-topo {
        font-size: 10px;
        font-weight: bold;
        color: #000000 !important;
        line-height: 1.2;
    }
    
    /* TRANSFORMANDO O BOTÃO DO PEDIDO NA CAIXINHA QUADRADA COM ZOOM DELAY DE 0,8s */
    div.element-container button[data-testid="stBaseButton-secondary"] {
        background-color: #ffffff !important;
        border: 1px solid #babcbf !important; /* Contorno cinza do card */
        border-top: 4px solid #FFD700 !important; /* Detalhe amarelo superior */
        border-radius: 4px !important;
        padding: 12px !important;
        width: 100% !important;
        height: auto !important;
        min-height: 85px !important;
        text-align: left !important;
        box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.08) !important;
        display: block !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease !important;
        transition-delay: 0.8s !important; /* Delay exato de 0,8 segundos */
    }
    
    /* Texto interno da caixinha em preto */
    div.element-container button[data-testid="stBaseButton-secondary"] p {
        color: #000000 !important;
        font-weight: bold !important;
        white-space: pre-wrap !important;
    }
    
    div.element-container button[data-testid="stBaseButton-secondary"]:hover {
        transform: scale(1.06) !important; /* Efeito de pequeno zoom */
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.15) !important;
        background-color: #ffffff !important;
    }
    
    /* Estilo dos botões amarelos fixos superiores do topo direito */
    div.element-container button[data-testid="stBaseButton-primary"] {
        background-color: #FFD700 !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: 1px solid #E6C200 !important;
        width: 100% !important;
    }
    div.element-container button[data-testid="stBaseButton-primary"]:hover {
        background-color: #E6C200 !important;
        color: #000000 !important;
    }
    
    /* Ajustes para inputs em modo claro */
    input {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# Layout do Cabeçalho principal organizando título e botões
col_titulo, col_btn1, col_btn2 = st.columns([6, 2, 2])

with col_titulo:
    st.title("📋 Painel de Controle")

with col_btn1:
    if st.button("👤 CRIAR CADASTRO", type="primary", key="main_btn_cad"):
        st.session_state.aba_aberta = "cadastro"
        st.session_state.pedido_selecionado = None
        st.rerun()

with col_btn2:
    if st.button("📦 CRIAR PEDIDO", type="primary", key="main_btn_ped"):
        st.session_state.aba_aberta = "pedido"
        st.session_state.pedido_selecionado = None
        st.rerun()

# ---- JANELA DINÂMICA: CRIAR CADASTRO ----
if st.session_state.aba_aberta == "cadastro":
    with st.container(border=True):
        st.markdown("### 👤 Cadastro de Novo Cliente")
        tipo_pess = st.radio("Tipo de Pessoa", ["PESSOA FÍSICA", "PESSOA JURÍDICA"], horizontal=True)
        
        with st.form("form_cliente", clear_on_submit=True):
            if tipo_pess == "PESSOA FÍSICA":
                nome = st.text_input("Nome:")
                cpf = st.text_input("CPF:")
                rg = st.text_input("RG:")
                dt_nasc = st.text_input("Data de Nascimento (DD/MM/AAAA):")
                orgao = st.text_input("Órgão Emissor:")
                if st.form_submit_button("Salvar e Voltar"):
                    if nome and cpf:
                        salvar_cliente(cpf, "PF", nome, rg, dt_nasc, orgao)
                        st.session_state.aba_aberta = None  # Reseta para voltar à tela inicial
                        st.rerun()
            else:
                nome_emp = st.text_input("Nome da Empresa:")
                cnpj = st.text_input("CNPJ:")
                dt_fund = st.text_input("Data de Fundação (DD/MM/AAAA):")
                if st.form_submit_button("Salvar e Voltar"):
                    if nome_emp and cnpj:
                        salvar_cliente(cnpj, "PJ", nome_emp, dt_fund=dt_fund)
                        st.session_state.aba_aberta = None  # Reseta para voltar à tela inicial
                        st.rerun()
        if st.button("❌ Cancelar e Sair", key="btn_cancelar_cad"):
            st.session_state.aba_aberta = None
            st.rerun()

# ---- JANELA DINÂMICA: CRIAR PEDIDO ----
if st.session_state.aba_aberta == "pedido":
    with st.container(border=True):
        st.markdown("### 📦 Abertura de Novo Pedido")
        doc_busca = st.text_input("Digite o CPF ou CNPJ do Cliente cadastrado:")
        if doc_busca:
            cliente_encontrado = buscar_cliente(doc_busca)
            if cliente_encontrado:
                st.success(f"Cliente Identificado: {cliente_encontrado[0]}")
                if st.button("Confirmar Pedido e Voltar", type="primary", key="btn_conf_ped"):
                    criar_novo_pedido(doc_busca)
                    st.session_state.aba_aberta = None  # Reseta para voltar à tela inicial
                    st.rerun()
            else:
                st.error("Cliente não localizado. Realize o cadastro primeiro.")
        if st.button("❌ Cancelar e Sair", key="btn_cancelar_ped"):
            st.session_state.aba_aberta = None
            st.rerun()

# ---- JANELA DINÂMICA: DETALHES DO PEDIDO SELECIONADO (DENTRO DA CAIXA) ----
