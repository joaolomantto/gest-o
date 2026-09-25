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

# 2. Interface Estilizada e Minimalista
st.set_page_config(layout="wide", page_title="Gestão de Fluxo", page_icon="📋")

# Injeção de CSS para botões superiores amarelos e caixinhas quadradas
st.markdown("""
    <style>
    /* Estilo para transformar os expanders nos botões amarelos solicitados */
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
    
    /* Configuração e linha divisória das colunas de cima até embaixo */
    div[data-testid="stHorizontalBlock"] {
        align-items: stretch !important;
    }
    
    div[data-testid="column"] {
        padding-right: 15px !important;
        padding-left: 15px !important;
        border-right: 1px solid #e2e8f0 !important;
        min-height: 80vh !important;
    }
    
    div[data-testid="column"]:last-child {
        border-right: none !important;
    }
    
    /* Cabeçalho cinza minimalista para as etapas */
    .topo-coluna {
        background-color: #f8fafc;
        padding: 8px;
        border-radius: 4px;
        text-align: center;
        margin-bottom: 15px;
        border: 1px solid #edf2f7;
    }
    
    /* Caixinha quadrada do pedido (Estilo Agendor) */
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

# Layout do Cabeçalho - Ajustado com proporções (6 partes para o título, 2 para cada botão)
col_titulo, col_btn1, col_btn2 = st.columns([6, 2, 2])

with col_titulo:
    st.title("📋 Painel de Controle")

# Botões superiores amarelos empurrados para o canto direito
with col_btn1:
    criar_cad = st.expander("👤 CRIAR CADASTRO")
with col_btn2:
    criar_ped = st.expander("📦 CRIAR PEDIDO")

# Fluxo do botão Criar Cadastro
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
            nome_emp = st.text_input("Nome da Empresa:")
            cnpj = st.text_input("CNPJ:")
            dt_fund = st.text_input("Data de Fundação (DD/MM/AAAA):")
            if st.form_submit_button("Salvar Empresa"):
                if nome_emp and cnpj:
                    salvar_cliente(cnpj, "PJ", nome_emp, dt_fund=dt_fund)
                    st.success("Cliente PJ Cadastrado!")
                    st.rerun()

# Fluxo do botão Criar Pedido
with criar_ped:
    st.markdown("<p style='color:black; font-weight:bold;'>Novo Pedido</p>", unsafe_allow_html=True)
    doc_busca = st.text_input("Digite o CPF ou CNPJ do Cliente:")
    if doc_busca:
        cliente_encontrado = buscar_cliente(doc_busca)
        if cliente_encontrado:
            st.info(f"Cliente identificado: {cliente_encontrado[0]}")
            if st.button("Confirmar e Criar Pedido", type="primary"):
                criar_novo_pedido(doc_busca)
                st.success("Pedido enviado para 'Pedido Criado'!")
                st.rerun()
        else:
            st.error("Cliente não localizado. Realize o cadastro primeiro.")

st.markdown("---")

# 3. Definição das 8 Colunas Solicitadas
etapas = [
    "Pedido Criado", "Confirmar Pix", "Faturar Notas", 
    "Faturar Entregar e Receber", "Cliente vem Buscar", 
    "Entregas via Tecar", "Transportadora", "Pedido Finalizado"
]

colunas_quadro = st.columns(len(etapas))
df_pedidos = carregar_fluxo()

for idx_etapa, etapa in enumerate(etapas):
    with colunas_quadro[idx_etapa]:
        st.markdown(f"""
            <div class='topo-coluna'>
                <b style='font-size:11px; color:#2d3748;'>{etapa.upper()}</b>
            </div>
        """, unsafe_allow_html=True)
        
        pedidos_fase = df_pedidos[df_pedidos["etapa"] == etapa] if not df_pedidos.empty else pd.DataFrame()
        
        for _, row in pedidos_fase.iterrows():
            st.markdown(f"""
                <div class='caixa-pedido'>
                    <div class='id-pedido'>P-{row['id']}</div>
                    <div class='nome-cliente'>{row['nome']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            with st.popover("⚙️ Detalhes / Mover", use_container_width=True):
                st.write(f"**Pedido:** P-{row['id']}")
                st.write(f"**Cliente:** {row['nome']} ({row['documento_cliente']})")
                
                st.info(row['observacoes'] if row['observacoes'] else "Sem informações adicionadas.")
                
                novas_obs = st.text_area("Adicionar Informações / Histórico:", value=row['observacoes'], key=f"obs_{row['id']}")
                
                arquivo = st.file_uploader("Adicionar arquivos:", key=f"file_{row['id']}")
                if arquivo:
                    st.caption(f"📎 Arquivo anexado: {arquivo.name}")
                
                nova_fase = st.selectbox("Mover manualmente para:", etapas, index=etapas.index(etapa), key=f"fase_{row['id']}")
                
                if st.button("Salvar Alterações", key=f"save_{row['id']}", type="primary"):
                    atualizar_pedido(row['id'], nova_fase, novas_obs)
                    st.success("Pedido Atualizado!")
                    st.rerun()
