import streamlit as st
import sqlite3
import pandas as pd
import os
import base64

# 1. Configuração e Conexão com Banco de Dados SQLite
DB_FILE = "sistema_agendor_custom.db"
UPLOAD_DIR = "arquivos_pedidos"

USER_MASTER = "admintecar.renault"
SENHA_MASTER = "admin123"

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
    
    c.execute("DROP TABLE IF EXISTS usuarios")
        
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario TEXT PRIMARY KEY,
            senha TEXT NOT NULL,
            nome TEXT NOT NULL,
            cpf TEXT NOT NULL,
            data_nascimento TEXT NOT NULL,
            telefone TEXT NOT NULL,
            autorizado TEXT DEFAULT 'PENDENTE'
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

def cadastrar_usuario(usuario, senha, nome, cpf, dt_nasc, telefone):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        usuario_limpo = usuario.strip().lower()
        c.execute("DELETE FROM usuarios WHERE usuario = ?", (usuario_limpo,))
        # CORREÇÃO: Alinhado o nome do campo do INSERT para 'telefone' idêntico ao banco de dados
        c.execute('''
            INSERT INTO usuarios (usuario, senha, nome, cpf, data_nascimento, telefone, autorizado)
            VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE')
        ''', (usuario_limpo, senha, nome, cpf, dt_nasc, telefone))
        conn.commit()
        sucesso = True
    except Exception:
        sucesso = False
    conn.close()
    return sucesso

def checar_status_usuario(usuario):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT autorizado FROM usuarios WHERE usuario = ?", (usuario.strip().lower(),))
    res = c.fetchone()
    conn.close()
    if res:
        return res[0]
    return "PENDENTE"

# CORREÇÃO CRÍTICA: Adicionado o campo 'autorizado' na busca para que a validação de sessão funcione
def realizar_login(usuario, senha):
    usuario_limpo = usuario.strip().lower()
    
    if usuario_limpo == USER_MASTER and senha == SENHA_MASTER:
        return {"usuario": USER_MASTER, "nome": "Administrador Tecar", "status": "APROVADO"}
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT nome, autorizado FROM usuarios WHERE usuario = ? AND senha = ?", (usuario_limpo, senha))
    res = c.fetchone()
    conn.close()
    
    if res:
        return {"usuario": usuario_limpo, "nome": res[0], "status": res[1]}
    return None

def listar_usuarios_pendentes():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT usuario, nome, cpf, telefone FROM usuarios WHERE autorizado = 'PENDENTE'", conn)
    conn.close()
    return df

def julgar_usuario(usuario, decisao):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    novo_status = "APROVADO" if decisao == "ACEITAR" else "RECUSADO"
    c.execute("UPDATE usuarios SET autorizado = ? WHERE usuario = ?", (novo_status, usuario.strip().lower()))
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

# 2. Configurações de Sessão do Streamlit
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "session_user" not in st.session_state:
    st.session_state["session_user"] = ""
if "session_nome" not in st.session_state:
    st.session_state["session_nome"] = ""
if "session_status" not in st.session_state:
    st.session_state["session_status"] = ""

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

# ----------------------------------------------------
# SISTEMA DE PORTAL DE ENTRADA
# ----------------------------------------------------
if not st.session_state["logado"]:
    st.title("📋 Portal de Acesso — Gestão de Fluxo")
    tab_login, tab_cadastro = st.tabs(["🔒 Acessar Minha Conta", "👤 Criar Nova Conta"])
    
    with tab_login:
        with st.form("form_login_sistema"):
            input_user = st.text_input("Usuário:")
            input_pass = st.text_input("Senha:", type="password")
            if st.form_submit_button("Entrar no Painel", use_container_width=True):
                conta = realizar_login(input_user, input_pass)
                if conta:
                    st.session_state["logado"] = True
                    st.session_state["session_user"] = conta["usuario"]
                    st.session_state["session_nome"] = conta["nome"]
                    st.session_state["session_status"] = conta["status"]
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
                    
    with tab_cadastro:
        with st.form("form_cadastro_estavel", clear_on_submit=False):
            new_nome = st.text_input("Nome Completo:")
            new_cpf = st.text_input("CPF (Apenas números):")
            new_nasc = st.text_input("Data de Nascimento (DD/MM/AAAA):")
            new_fone = st.text_input("Telefone de Contato:")
            st.markdown("---")
            new_user = st.text_input("Escolha um Nome de Usuário (Para o login):")
            new_pass = st.text_input("Defina sua Senha de Acesso:", type="password")
            
            enviar_dados = st.form_submit_button("🚀 Cadastrar e Solicitar Permissão", use_container_width=True)
            
            if enviar_dados:
                campos_preenchidos = bool(new_nome and new_cpf and new_nasc and new_fone and new_user and new_pass)
                usuario_valido = bool(new_user.strip().lower() != USER_MASTER)
                
                if not campos_preenchidos:
                    st.error("Preencha todos os campos do formulário para concluir.")
                elif not usuario_valido:
                    st.error("Este nome de usuário é reservado ao administrador.")
                else:
                    cadastrar_usuario(new_user, new_pass, new_nome, new_cpf, new_nasc, new_fone)
