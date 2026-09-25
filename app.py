import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
import hashlib

# 1. Configuração e Conexão com Banco de Dados SQLite (v2 para evitar conflito)
DB_FILE = "sistema_agendor_v2.db"
UPLOAD_DIR = "arquivos_pedidos"

# Cria a pasta para salvar os arquivos anexados, se não existir
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def gerará_hash_senha(senha):
    """Criptografa a senha para salvar no banco de dados com segurança."""
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

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
            arquivo_caminho TEXT DEFAULT '',
            autor TEXT DEFAULT 'Não informado'
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            senha_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def cadastrar_usuario(username, nome, senha):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    senha_hash = gerará_hash_senha(senha)
    try:
        c.execute("INSERT OR REPLACE INTO usuarios (username, nome, senha_hash) VALUES (?, ?, ?)", 
                  (username.strip().lower(), nome, senha_hash))
        conn.commit()
        sucesso = True
    except sqlite3.IntegrityError:
        sucesso = False
    conn.close()
    return sucesso

def verificar_login(username, senha):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    senha_hash = gerará_hash_senha(senha)
    c.execute("SELECT nome FROM usuarios WHERE username = ? AND senha_hash = ?", 
              (username.strip().lower(), senha_hash))
    res = c.fetchone()
    conn.close()
    return res

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

def criar_novo_pedido(doc, autor):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO pedidos (documento_cliente, etapa, autor) VALUES (?, 'Pedido Criado', ?)", (doc, autor))
    conn.commit()
    conn.close()

def atualizar_pedido(id_ped, nova_etapa, novas_obs, arquivo_path=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if arquivo_path:
        c.execute("UPDATE pedidos SET etapa = ?, observacoes = ?, arquivo_caminho = ? WHERE id = ?", (nova_etapa, novas_obs, arquivo_path, id_ped))
    else:
        c.execute("UPDATE pedidos SET etapa = ?, observacoes = ? WHERE id = ?", (nova_etapa, novas_obs, id_ped))
    conn.commit()
    conn.close()

def excluir_pedido(id_ped):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM pedidos WHERE id = ?", (id_ped,))
    conn.commit()
    conn.close()

def carregar_fluxo():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query('''
        SELECT p.id, p.documento_cliente, p.etapa, p.observacoes, p.arquivo_caminho, p.autor, c.nome, c.tipo
        FROM pedidos p
        JOIN clientes c ON p.documento_cliente = c.documento
    ''', conn)
    conn.close()
    return df

def exibir_pdf(caminho_pdf):
    try:
        with open(caminho_pdf, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo PDF: {e}")

# Inicializa o banco de dados limpo
criar_banco()

# 2. Interface Estilizada e Configuração Inicial
st.set_page_config(layout="wide", page_title="Gestão de Fluxo", page_icon="📋")

# Controle de Sessão de Usuário
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "usuario_nome" not in st.session_state:
    st.session_state.usuario_nome = None

# Sidebar Dinâmica para Autenticação
with st.sidebar:
    st.header("👤 Autenticação")
    if not st.session_state.usuario:
        ja_tem_conta = st.checkbox("Já tenho uma conta cadastrada", value=True)
        
        if ja_tem_conta:
            st.subheader("Fazer Login")
            user_login = st.text_input("Usuário (Username):", key="login_user")
            senha_login = st.text_input("Senha:", type="password", key="login_senha")
            
            if st.button("Acessar Painel", type="primary", use_container_width=True):
                dados_user = verificar_login(user_login, senha_login)
                if dados_user:
                    st.session_state.usuario = user_login.strip().lower()
                    st.session_state.usuario_nome = dados_user[0]
                    st.success(f"Bem-vindo, {dados_user[0]}!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
        else:
            st.subheader("Criar Novo Cadastro")
            new_user = st.text_input("Escolha um Username:", key="cad_user")
            new_nome = st.text_input("Seu Nome Completo:", key="cad_nome")
            new_senha = st.text_input("Defina uma Senha:", type="password", key="cad_senha")
            
            if st.button("Registrar Conta", use_container_width=True):
                if new_user and new_nome and new_senha:
                    if cadastrar_usuario(new_user, new_nome, new_senha):
                        st.success("Cadastro realizado! Marque a caixa acima para fazer login.")
                    else:
                        st.error("Este Username já está em uso.")
                else:
                    st.error("Por favor, preencha todos os campos do cadastro.")
    else:
        st.write(f"Conectado como: **{st.session_state.usuario_nome}** (`{st.session_state.usuario}`)")
        if st.button("Sair / Desconectar", use_container_width=True):
            st.session_state.usuario = None
            st.session_state.usuario_nome = None
            st.rerun()

# Se não houver sessão ativa, interrompe a execução do Kanban
if not st.session_state.usuario:
    st.warning("⚠️ Faça login na barra lateral para carregar as informações do sistema.")
    st.stop()

# Estilos CSS Customizados
st.markdown("""
    <style>
    div[data-testid="stExpander"] {
        background-color: #FFD700 !important;
        border: 1px solid #E6C200 !important;
        border-radius: 4px !important;
        box-shadow: none !important;
    }
    div[data-testid="stExpander"] p {
        color: #000000 !important;
        font-weight: bold !important;
    }
    div[data-testid="stHorizontalBlock"] {
        align-items: stretch !important;
    }
    div[data-testid="column"] {
        padding-right: 10px !important;
        padding-left: 10px !important;
        border-right: 1px solid #e2e8f0 !important;
        min-height: 80vh !important;
    }
    div[data-testid="column"]:last-child {
        border-right: none !important;
    }
    .topo-coluna {
        background-color: #f8fafc;
        padding: 6px;
        border-radius: 4px;
        text-align: center;
        margin-bottom: 15px;
        border: 1px solid #edf2f7;
        min-height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .caixa-pedido {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-top: 3px solid #FFD700;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 8px;
        box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.05);
    }
    .id-pedido {
        font-size: 13px;
        font-weight: bold;
        color: #1a202c;
        margin-bottom: 2px;
    }
    .nome-cliente {
        font-size: 13px;
        color: #4a5568;
        word-wrap: break-word;
    }
    </style>
""", unsafe_allow_html=True)

col_titulo, col_btn1, col_btn2 = st.columns([6, 2, 2])

with col_titulo:
    st.title("📋 Painel de Controle")

with col_btn1:
    criar_cad = st.expander("👤 CRIAR CADASTRO")
with col_btn2:
    criar_ped = st.expander("📦 CRIAR PEDIDO")

with criar_cad:
    st.markdown("<p style='color:black; font-weight:bold;'>Novo Cliente</p>", unsafe_allow_html=True)
    tipo_pess = st.radio("Tipo de Pessoa", ["PESSOA FÍSICA", "PESSOA JURÍDICA"], horizontal=True)
    
    with st.form("form_cliente", clear_on_submit=True):
        if tipo_pess == "PESSOA FÍSICA":
            nome = st.text_input("Nome:")
            cpf = st.text_input("CPF:")
            rg = st.text_input("RG:")
            dt_nasc = st.text_input("Data de Nascimento (DD/MM/AAAA):")
            orgao = st.text_input("Órgão Emissor:")
            
            if st.form_submit_button("Salvar Cliente"):
                if nome and cpf:
                    salvar_cliente(cpf, "PF", nome, rg, dt_nasc, orgao)
                    st.success("Cliente PF Cadastrado!")
                    st.rerun()
                else:
