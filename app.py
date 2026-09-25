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
            observacoes TEXT DEFAULT ' '
        )
    ''')
    conn.commit()
    conn.close()

def buscar_cliente(doc):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT nome, tipo FROM clientes WHERE documento = ?", (doc.strip(),))
    res = c.fetchone()
    conn.close()
    return res

def salvar_cliente(doc, tipo, nome, rg=None, dt_nasc=None, orgao=None, dt_fund=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO clientes (documento, tipo, nome, rg, data_nascimento, orgao_emissor, data_fundacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (doc.strip(), tipo, nome, rg, dt_nasc, orgao, dt_fund))
    conn.commit()
    conn.close()

def criar_novo_pedido(doc):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO pedidos (documento_cliente, etapa) VALUES (?, 'Pedido Criado')", (doc.strip(),))
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
        SELECT p.id, p.documento_cliente, p.etapa, p.observacoes, 
               IFNULL(c.nome, p.documento_cliente) as nome, 
               IFNULL(c.tipo, 'PF') as tipo
        FROM pedidos p
        LEFT JOIN clientes c ON p.documento_cliente = c.documento
    ''', conn)
    conn.close()
    return df

criar_banco()

# Inicialização do controle estável de cliques
if "pedido_selecionado" not in st.session_state:
    st.session_state.pedido_selecionado = None

# 2. Interface Avançada e Configuração de Tela
st.set_page_config(layout="wide", page_title="Gestão de Fluxo", page_icon="📋")

# Estilização do Design Original (Botões Amarelos e Divisórias verticais)
st.markdown("""
    <style>
    div[data-testid="stExpander"] {
        background-color: #FFD700 !important;
        border: 1px solid #E6C200 !important;
        border-radius: 4px !important;
    }
    div[data-testid="stExpander"] p {
        color: #000000 !important;
        font-weight: bold !important;
    }
    
    /* Força as divisões de colunas irem de cima até embaixo */
    div[data-testid="stHorizontalBlock"] {
        align-items: stretch !important;
    }
    
    div[data-testid="column"] {
        padding-right: 10px !important;
        padding-left: 10px !important;
        border-right: 1px solid #d1d5db !important;
    }
    
    div[data-testid="column"]:last-child {
        border-right: none !important;
    }
    
    /* Caixa de Etapas Superior */
    .topo-coluna {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
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
        color: #1a202c;
        line-height: 1.2;
    }
    
    /* Efeito de Zoom com 0.8s nos botões-cards nativos */
    div.element-container button[data-testid="stBaseButton-secondary"] {
        background-color: #ffffff !important;
        border: 1px solid #babcbf !important;
        border-top: 4px solid #FFD700 !important;
        border-radius: 4px !important;
        padding: 12px !important;
        width: 100% !important;
        height: auto !important;
        min-height: 80px !important;
        text-align: left !important;
        box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.05) !important;
        display: block !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease !important;
        transition-delay: 0.8s !important;
    }
    
    div.element-container button[data-testid="stBaseButton-secondary"] p {
        color: #1a202c !important;
        font-weight: bold !important;
        white-space: pre-wrap !important;
    }
    
    div.element-container button[data-testid="stBaseButton-secondary"]:hover {
        transform: scale(1.06) !important;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.12) !important;
        background-color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# Layout do Cabeçalho
col_titulo, col_btn1, col_btn2 = st.columns()

with col_titulo:
    st.title("📋 Painel de Controle")

with col_btn1:
    criar_cad = st.expander("👤 CRIAR CADASTRO")
with col_btn2:
    criar_ped = st.expander("📦 CRIAR PEDIDO")

# Fluxo Criar Cadastro
with criar_cad:
    st.markdown("<p style='color:black; font-weight:bold;'>Novo Cliente</p>", unsafe_allow_html=True)
    tipo_pess = st.radio("Tipo de Pessoa", ["PESSOA FÍSICA", "PESSOA JURÍDICA"], horizontal=True)
    
    with st.form("form_cliente", clear_on_submit=True):
        if tipo_pess == "PESSOA FÍSICA":
            nome = st.text_input("Nome:")
            cpf = st.text_input("CPF:")
            rg = st.text_input("RG:")
            dt_nasc = st.text_input("Data de Nascimento:")
            orgao = st.text_input("Órgão Emissor:")
            if st.form_submit_button("Salvar Cliente"):
                if nome and cpf:
                    salvar_cliente(cpf, "PF", nome, rg, dt_nasc, orgao)
                    st.success("Cliente PF Cadastrado!")
                    st.rerun()
        else:
            nome_emp = st.text_input("Nome da Empresa:")
            cnpj = st.text_input("CNPJ:")
            dt_fund = st.text_input("Data de Fundação:")
            if st.form_submit_button("Salvar Empresa"):
                if nome_emp and cnpj:
                    salvar_cliente(cnpj, "PJ", nome_emp, dt_fund=dt_fund)
                    st.success("Cliente PJ Cadastrado!")
                    st.rerun()

# Fluxo Criar Pedido
with criar_ped:
    st.markdown("<p style='color:black; font-weight:bold;'>Novo Pedido</p>", unsafe_allow_html=True)
    doc_busca = st.text_input("Digite o CPF ou CNPJ do Cliente:")
    if doc_busca:
        cliente_encontrado = buscar_cliente(doc_busca)
        if cliente_encontrado:
            st.info(f"Cliente identificado: {cliente_encontrado}")
            if st.button("Confirmar e Criar Pedido", type="primary", key="btn_confirmar_pedido_final"):
                criar_novo_pedido(doc_busca)
                st.session_state.pedido_selecionado = None
                st.rerun()
        else:
            st.warning("Cliente não localizado. Criar mesmo assim?")
            if st.button("Confirmar e Criar Pedido (Sem Cadastro)", type="primary", key="btn_criar_ped_sem_cadastro"):
                criar_novo_pedido(doc_busca)
                st.session_state.pedido_selecionado = None
                st.rerun()

# ---- JANELA DINÂMICA DE DETALHES ----
if st.session_state.pedido_selecionado is not None:
    row = st.session_state.pedido_selecionado
    with st.container(border=True):
        st.markdown(f"### ⚙️ Detalhes do Pedido P-{row['id']}")
        st.write(f"**Cliente:** {row['nome']} | **Documento:** {row['documento_cliente']} ({row['tipo']})")
        st.markdown("---")
        
        st.info(row['observacoes'] if row['observacoes'] else "Nenhuma informação adicionada.")
        novas_obs = st.text_area("Adicionar Informações / Histórico Manual:", value=row['observacoes'], key=f"obs_edit_{row['id']}")
        
        arquivo = st.file_uploader("Adicionar arquivos:", key=f"file_edit_{row['id']}")
        if arquivo:
            st.caption(f"📎 Arquivo anexado: {arquivo.name}")
            
        etapas_lista = ["Pedido Criado", "Confirmar Pix", "Faturar Notas", "Faturar Entregar e Receber", "Cliente vem Buscar", "Entregas via Tecar", "Transportadora", "Pedido Finalizado"]
        nova_fase = st.selectbox("Mover manualmente para:", etapas_lista, index=etapas_lista.index(row['etapa']), key=f"fase_edit_{row['id']}")
        
        col_salvar, col_cancelar = st.columns(2)
        with col_salvar:
            if st.button("💾 Salvar Alterações e Fechar", type="primary", key=f"save_btn_{row['id']}"):
                atualizar_pedido(row['id'], nova_fase, novas_obs)
                st.session_state.pedido_selecionado = None
                st.rerun()
        with col_cancelar:
            if st.button("❌ Cancelar e Sair", key=f"cancel_btn_{row['id']}"):
                st.session_state.pedido_selecionado = None
                st.rerun()

st.markdown("---")

# 3. GERAÇÃO COMPLETA DAS 8 COLUNAS
etapas = [
    "Pedido Criado", "Confirmar Pix", "Faturar Notas", 
    "Faturar Entregar e Receber", "Cliente vem Buscar", 
    "Entregas via Tecar", "Transportadora", "Pedido Finalizado"
]

colunas_quadro = st.columns(len(etapas))
df_pedidos = carregar_fluxo()

for idx_etapa, etapa_nome in enumerate(etapas):
    with colunas_quadro[idx_etapa]:
        # Caixa de título montada de forma estável
        texto_html_topo = f"<div class='topo-coluna'><span class='texto-topo'>{etapa_nome.upper()}</span></div>"
        st.markdown(texto_html_topo, unsafe_allow_html=True)
        
