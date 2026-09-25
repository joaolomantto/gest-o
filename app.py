import streamlit as st
import sqlite3
import pandas as pd

# 1. BANCO DE DADOS (Nome alterado para iniciar 100% zerado e limpo)
DB_FILE = "sistema_agendor_oficial.db"

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
        SELECT p.id, p.documento_cliente, p.etapa, p.observacoes, IFNULL(c.nome, 'Cliente Sem Cadastro') as nome, IFNULL(c.tipo, 'PF') as tipo
        FROM pedidos p
        LEFT JOIN clientes c ON p.documento_cliente = c.documento
    ''', conn)
    conn.close()
    return df

criar_banco()

# As 8 etapas na ordem exata solicitada
ETAPAS_GLOBAL = [
    "Pedido Criado", "Confirmar Pix", "Faturar Notas", 
    "Faturar Entregar e Receber", "Cliente vem Buscar", 
    "Entregas via Tecar", "Transportadora", "Pedido Finalizado"
]

# 2. CONFIGURAÇÃO DA INTERFACE (Tema Claro e Expansão)
st.set_page_config(layout="wide", page_title="Gestão de Fluxo", page_icon="📋")

# Injeção de CSS de Alta Performance (Fundo Branco, Linhas e Caixas Quadradas)
st.markdown("""
    <style>
    /* Força todas as camadas do Streamlit a ficarem BRANCAS */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMainBlockContainer"] {
        background-color: #ffffff !important;
    }
    
    /* Força os textos e títulos para PRETO PURO */
    h1, h2, h3, h4, h5, h6, p, span, label, li, div, .stMarkdown, p font {
        color: #000000 !important;
    }

    /* Customização dos botões amarelos superiores do topo direito */
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
    
    /* Configuração e linhas verticais contínuas entre as colunas do funil */
    div[data-testid="stHorizontalBlock"] {
        align-items: stretch !important;
        background-color: #ffffff !important;
    }
    
    div[data-testid="column"] {
        padding-right: 10px !important;
        padding-left: 10px !important;
        border-right: 1px solid #cccccc !important; /* Linha de divisa cinza nítida */
    }
    
    div[data-testid="column"]:last-child {
        border-right: none !important;
    }
    
    /* CAIXA DE TÍTULO SUPERIOR: Altura fixa para manter o alinhamento horizontal perfeito */
    .topo-coluna {
        background-color: #ffffff;
        border: 1px solid #000000;
        padding: 6px 4px;
        border-radius: 4px;
        text-align: center;
        margin-bottom: 20px;
        height: 58px; /* Altura ideal para alinhar textos longos de duas linhas */
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
    
    /* CONFIGURAÇÃO DA CAIXINHA QUADRADA DO PEDIDO (CSS aplicado diretamente sobre o botão nativo) */
    div.element-container button[data-testid="stBaseButton-secondary"] {
        background-color: #ffffff !important;
        border: 1px solid #babcbf !important;
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
        transition-delay: 0.8s !important; /* Zoom só activa após 0,8s parado */
    }
    
    /* Força os textos internos da caixinha a ficarem pretos */
    div.element-container button[data-testid="stBaseButton-secondary"] p {
        color: #000000 !important;
        font-weight: bold !important;
        white-space: pre-wrap !important;
    }
    
    div.element-container button[data-testid="stBaseButton-secondary"]:hover {
        transform: scale(1.06) !important; /* Pequeno Zoom de destaque */
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.15) !important;
        background-color: #ffffff !important;
    }

    /* Garante que os campos de digitação funcionem em modo claro */
    input, textarea, select {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. JANELAS MODAIS FLUTUANTES (Abrem no centro e voltam limpas para a tela inicial)
@st.dialog("⚙️ Detalhes e Ações do Pedido")
def modal_detalhes_pedido(row):
    st.write(f"**Código:** P-{row['id']}")
    st.write(f"**Cliente:** {row['nome']} | **Documento:** {row['documento_cliente']} ({row['tipo']})")
    st.markdown("---")
    
    st.info(row['observacoes'] if row['observacoes'] else "Nenhuma informação ou histórico adicionado.")
    novas_obs = st.text_area("Adicionar Informações / Histórico Manual:", value=row['observacoes'])
    
    arquivo = st.file_uploader("Anexar Arquivos / Notas / Imagens:")
    if arquivo:
        st.caption(f"📎 Arquivo anexado: {arquivo.name}")
        
    nova_fase = st.selectbox("Mover Pedido para a Etapa:", ETAPAS_GLOBAL, index=ETAPAS_GLOBAL.index(row['etapa']))
    
    col_save, col_close = st.columns(2)
    with col_save:
        if st.button("💾 Salvar Alterações", type="primary"):
            atualizar_pedido(row['id'], nova_fase, novas_obs)
            st.rerun()
    with col_close:
        if st.button("❌ Sair sem Salvar"):
            st.rerun()

# 4. CABEÇALHO PRINCIPAL (Título e Botões Amarelos Alinhados à Direita)
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
            if st.button("Confirmar e Criar Pedido", type="primary"):
                criar_novo_pedido(doc_busca)
                st.success("Pedido enviado para 'Pedido Criado'!")
                st.rerun()
        else:
            st.warning("Cliente não localizado no banco, gerando pedido direto.")
            if st.button("Criar Pedido Direto", type="primary"):
