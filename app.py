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

# Lista global com as 8 etapas para o fluxo
ETAPAS_GLOBAL = ["Pedido Criado", "Confirmar Pix", "Faturar Notas", "Faturar Entregar e Receber", "Cliente vem Buscar", "Entregas via Tecar", "Transportadora", "Pedido Finalizado"]

# Inicialização de controle de janelas na memória do navegador
if "pedido_selecionado" not in st.session_state:
    st.session_state.pedido_selecionado = None
if "aba_aberta" not in st.session_state:
    st.session_state.aba_aberta = None

# 2. Interface Estilizada Dinâmica
st.set_page_config(layout="wide", page_title="Gestão de Fluxo", page_icon="📋")

# Injeção de CSS Robusto para forçar Fundo Branco e manter elementos no Topo
st.markdown("""
    <style>
    /* Força todas as camadas do Streamlit a ficarem brancas */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMainBlockContainer"] {
        background-color: #ffffff !important;
    }
    
    /* Força os textos principais, títulos e labels para PRETO PURO */
    h1, h2, h3, h4, h5, h6, p, span, label, li, .stMarkdown, p font {
        color: #000000 !important;
    }
    
    /* Configuração e linha divisória das colunas (Estilo Agendor de cima a baixo) */
    div[data-testid="stHorizontalBlock"] {
        align-items: stretch !important;
        background-color: #ffffff !important;
    }
    
    div[data-testid="column"] {
        padding-right: 8px !important;
        padding-left: 8px !important;
        border-right: 1px solid #cccccc !important; /* Divisa cinza bem marcada */
    }
    
    div[data-testid="column"]:last-child {
        border-right: none !important;
    }
    
    /* Alinhamento perfeito das caixas de etapas superiores */
    .topo-coluna {
        background-color: #ffffff;
        border: 1px solid #000000;
        padding: 8px 4px;
        border-radius: 4px;
        text-align: center;
        margin-bottom: 20px;
        height: 55px;
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
    
    /* Caixinha Quadrada do Pedido - Fundo Branco, Bordas Cinzas e Texto PRETO */
    div.element-container button[data-testid="stBaseButton-secondary"] {
        background-color: #ffffff !important;
        border: 1px solid #a1a1aa !important;
        border-top: 4px solid #FFD700 !important; /* Detalhe em amarelo */
        border-radius: 4px !important;
        padding: 12px !important;
        width: 100% !important;
        height: auto !important;
        min-height: 80px !important;
        text-align: left !important;
        box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.08) !important;
        display: block !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease !important;
        transition-delay: 0.8s !important; /* Zoom com delay de 0.8s */
    }
    
    /* Garante que o texto de dentro do botão do pedido seja PRETO PURO */
    div.element-container button[data-testid="stBaseButton-secondary"] div p {
        color: #000000 !important;
        font-weight: bold !important;
    }
    
    div.element-container button[data-testid="stBaseButton-secondary"]:hover {
        transform: scale(1.06) !important;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.15) !important;
        background-color: #ffffff !important;
    }
    
    /* Customização dos botões amarelos superiores do topo */
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
    </style>
""", unsafe_allow_html=True)

# Layout do Cabeçalho principal (Título e os dois botões amarelos)
col_titulo, col_btn1, col_btn2 = st.columns([6, 2, 2])

with col_titulo:
    st.markdown("<h1 style='margin:0; font-size:2rem;'>📋 Painel de Controle</h1>", unsafe_allow_html=True)

with col_btn1:
    if st.button("👤 CRIAR CADASTRO", type="primary"):
        st.session_state.aba_aberta = "cadastro"
        st.session_state.pedido_selecionado = None

with col_btn2:
    if st.button("📦 CRIAR PEDIDO", type="primary"):
        st.session_state.aba_aberta = "pedido"
        st.session_state.pedido_selecionado = None

# ---- JANELA DINÂMICA: CRIAR CADASTRO ----
if st.session_state.aba_aberta == "cadastro":
    with st.container(border=True):
        st.subheader("👤 Cadastro de Novo Cliente")
        tipo_pess = st.radio("Tipo de Pessoa", ["PESSOA FÍSICA", "PESSOA JURÍDICA"], horizontal=True)
        
        with st.form("form_cliente", clear_on_submit=True):
            if tipo_pess == "PESSOA FÍSICA":
                nome = st.text_input("Nome:")
                cpf = st.text_input("CPF:")
                rg = st.text_input("RG:")
                dt_nasc = st.text_input("Data de Nascimento (DD/MM/AAAA):")
                orgao = st.text_input("Órgão Emissor:")
                if st.form_submit_button("Salvar e Fechar"):
                    if nome and cpf:
                        salvar_cliente(cpf, "PF", nome, rg, dt_nasc, orgao)
                        st.session_state.aba_aberta = None
                        st.rerun()
            else:
                nome_emp = st.text_input("Nome da Empresa:")
                cnpj = st.text_input("CNPJ:")
                dt_fund = st.text_input("Data de Fundação (DD/MM/AAAA):")
                if st.form_submit_button("Salvar e Fechar"):
                    if nome_emp and cnpj:
                        salvar_cliente(cnpj, "PJ", nome_emp, dt_fund=dt_fund)
                        st.session_state.aba_aberta = None
                        st.rerun()
        if st.button("❌ Cancelar e Sair", key="btn_cancelar_cad"):
            st.session_state.aba_aberta = None
            st.rerun()

# ---- JANELA DINÂMICA: CRIAR PEDIDO ----
if st.session_state.aba_aberta == "pedido":
    with st.container(border=True):
        st.subheader("📦 Abertura de Novo Pedido")
        doc_busca = st.text_input("Digite o CPF ou CNPJ do Cliente cadastrado:")
        if doc_busca:
            cliente_encontrado = buscar_cliente(doc_busca)
            if cliente_encontrado:
                st.success(f"Cliente Encontrado: {cliente_encontrado[0]}")
                if st.button("Confirmar Pedido e Fechar", type="primary", key="btn_conf_ped"):
                    criar_novo_pedido(doc_busca)
                    st.session_state.aba_aberta = None
                    st.rerun()
            else:
                st.error("Cliente não localizado. Realize o cadastro primeiro.")
        if st.button("❌ Cancelar e Sair", key="btn_cancelar_ped"):
            st.session_state.aba_aberta = None
            st.rerun()

# ---- JANELA DINÂMICA: DETALHES DO PEDIDO SELECIONADO ----
if st.session_state.pedido_selecionado is not None:
    row = st.session_state.pedido_selecionado
    with st.container(border=True):
        st.subheader(f"⚙️ Detalhes e Movimentação: Pedido P-{row['id']}")
        st.write(f"**Cliente:** {row['nome']} | **Documento:** {row['documento_cliente']} ({row['tipo']})")
        st.markdown("---")
        
        st.info(row['observacoes'] if row['observacoes'] else "Nenhuma informação adicionada.")
