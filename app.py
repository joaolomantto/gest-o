import streamlit as st
import sqlite3
import pandas as pd
import os
import base64

# 1. Configuração e Conexão com Banco de Dados SQLite
DB_FILE = "sistema_agendor_custom.db"
UPLOAD_DIR = "arquivos_pedidos"
CHAVE_MESTRE_CHEFE = "admin123"  # <--- SUA SENHA MASTER DO CHEFE

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

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
            observacoes TEXT DEFAULT ''
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            cpf TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            data_nascimento TEXT NOT NULL,
            telefone TEXT NOT NULL,
            autorizado INTEGER DEFAULT 0
        )
    ''')
    
    try:
        c.execute("ALTER TABLE pedidos ADD COLUMN arquivo_caminho TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE pedidos ADD COLUMN autor TEXT DEFAULT 'Não informado'")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

def cadastrar_usuario(nome, cpf, email, dt_nasc, telephone):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO usuarios (cpf, nome, email, data_nascimento, telefone, autorizado)
            VALUES (?, ?, ?, ?, ?, 0)
        ''', (cpf, nome, email, dt_nasc, telephone))
        conn.commit()
        sucesso = True
    except sqlite3.IntegrityError:
        sucesso = False
    conn.close()
    return sucesso

def checar_status_usuario(cpf):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT nome, autorizado FROM usuarios WHERE cpf = ?", (cpf,))
    res = c.fetchone()
    conn.close()
    return res

def listar_usuarios_pendentes():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT cpf, nome, email, telephone FROM usuarios WHERE autorizado = 0", conn)
    conn.close()
    return df

def autorizar_usuario(cpf):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET autorizado = 1 WHERE cpf = ?", (cpf,))
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

criar_banco()

# 2. Interface Estilizada e Configurações de Sessão
st.set_page_config(layout="wide", page_title="Gestão de Fluxo", page_icon="📋")

if "usuario_cpf" not in st.session_state:
    st.session_state["usuario_cpf"] = ""
if "usuario_nome" not in st.session_state:
    st.session_state["usuario_nome"] = ""
if "modo_chefe_emergencia" not in st.session_state:
    st.session_state["modo_chefe_emergencia"] = False

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
    div[data-testid="stHorizontalBlock"] { align-items: stretch !important; }
    div[data-testid="column"] {
        padding-right: 10px !important;
        padding-left: 10px !important;
        border-right: 1px solid #e2e8f0 !important;
        min-height: 80vh !important;
    }
    div[data-testid="column"]:last-child { border-right: none !important; }
    .topo-coluna {
        background-color: #f8fafc; padding: 6px; border-radius: 4px; text-align: center;
        margin-bottom: 15px; border: 1px solid #edf2f7; min-height: 48px;
        display: flex; align-items: center; justify-content: center;
    }
    .caixa-pedido {
        background-color: #ffffff; border: 1px solid #e2e8f0; border-top: 3px solid #FFD700;
        padding: 12px; border-radius: 4px; margin-bottom: 4px; box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.05);
    }
    .id-pedido { font-size: 13px; font-weight: bold; color: #1a202c; margin-bottom: 2px; }
    .nome-cliente { font-size: 13px; color: #4a5568; word-wrap: break-word; }
    </style>
""", unsafe_allow_html=True)

# CORREÇÃO: Função rápida de Login do Chefe para pular os bloqueios na hora
def forcar_login_chefe():
    st.session_state["modo_chefe_emergencia"] = True
    st.session_state["usuario_nome"] = "Administrador"
    st.session_state["usuario_cpf"] = "MASTER"

# ----------------------------------------------------
# FLUXO DE ENTRADA: CADASTRO OU ESPERA DE PERMISSÃO
# ----------------------------------------------------
if not st.session_state["modo_chefe_emergencia"] and st.session_state["usuario_cpf"] == "":
    st.title("📋 Bem-vindo ao Sistema de Gestão")
    st.subheader("Primeiro acesso detectado. Por favor, identifique-se ou faça o seu cadastro.")
    
    aba_login, aba_cadastro = st.tabs(["Já tenho Cadastro", "Criar Novo Cadastro"])
    
    with aba_login:
        with st.form("form_entrar"):
            login_cpf = st.text_input("Digite seu CPF cadastrado:")
            btn_entrar = st.form_submit_button("Entrar no Painel")
            if btn_entrar:
                if login_cpf.strip():
                    status = checar_status_usuario(login_cpf.strip())
                    if status:
                        st.session_state["usuario_cpf"] = login_cpf.strip()
                        st.session_state["usuario_nome"] = status[0]
                        st.rerun()
                    else:
                        st.error("CPF não localizado no sistema. Vá na aba ao lado e realize o cadastro.")
                else:
                    st.warning("Preencha o campo de CPF.")
                    
    with aba_cadastro:
        with st.form("form_registro_inicial", clear_on_submit=True):
            reg_nome = st.text_input("Nome Completo:")
            reg_cpf = st.text_input("CPF (Apenas números):")
            reg_email = st.text_input("E-mail Corporativo:")
            reg_nasc = st.text_input("Data de Nascimento (DD/MM/AAAA):")
            reg_fone = st.text_input("Número de Telefone (com DDD):")
            
            if st.form_submit_button("Solicitar Acesso ao Sistema"):
                if reg_nome and reg_cpf and reg_email and reg_nasc and reg_fone:
                    if cadastrar_usuario(reg_nome, reg_cpf, reg_email, reg_nasc, reg_fone):
                        st.session_state["usuario_cpf"] = reg_cpf
                        st.session_state["usuario_nome"] = reg_nome
                        st.success("Cadastro realizado! Aguardando aprovação.")
                        st.rerun()
                    else:
                        st.error("Este CPF já possui uma solicitação registrada.")
                else:
                    st.error("Todos os campos do formulário são obrigatórios.")
    
    st.markdown("---")
    with st.expander("🔑 Acesso Direto do Administrador (Chefe)"):
        senha_direta = st.text_input("Digite a senha master para pular o cadastro:", type="password", key="senha_inicial")
        if st.button("Ignorar e Entrar como Chefe"):
            if senha_direta == CHAVE_MESTRE_CHEFE:
                forcar_login_chefe()
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

# Se não for o chefe emergencial, checa o status de aprovação comum no banco
if not st.session_state["modo_chefe_emergencia"]:
    dados_usuario = checar_status_usuario(st.session_state["usuario_cpf"])
    if dados_usuario and dados_usuario[1] == 0:
        st.title("📋 Aguardando Liberação")
        st.warning(f"Olá, {st.session_state['usuario_nome'].title()}! Seu cadastro foi recebido com sucesso.")
