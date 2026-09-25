import streamlit as st
import sqlite3
import pandas as pd
import os
import base64

# 1. Configuração e Conexão com Banco de Dados SQLite
DB_FILE = "sistema_agendor_custom.db"
UPLOAD_DIR = "arquivos_pedidos"

# Cria a pasta para salvar os arquivos anexados, se não existir
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
    
    # Adiciona a coluna de arquivos se ela não existir
    try:
        c.execute("ALTER TABLE pedidos ADD COLUMN arquivo_caminho TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    # Adiciona a coluna de autor se ela não existir de forma segura
    try:
        c.execute("ALTER TABLE pedidos ADD COLUMN autor TEXT DEFAULT 'Não informado'")
    except sqlite3.OperationalError:
        pass
        
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

# 2. Interface Estilizada e Minimalista
st.set_page_config(layout="wide", page_title="Gestão de Fluxo", page_icon="📋")

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
        margin-bottom: 4px;
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
            nome_emp = st.text_input("Nome da Empresa:")
            cnpj = st.text_input("CNPJ:")
            dt_fund = st.text_input("Data de Fundação (DD/MM/AAAA):")
            if st.form_submit_button("Salvar Empresa"):
                if nome_emp and cnpj:
                    salvar_cliente(cnpj, "PJ", nome_emp, dt_fund=dt_fund)
                    st.success("Cliente PJ Cadastrado!")
                    st.rerun()

with criar_ped:
    st.markdown("<p style='color:black; font-weight:bold;'>Novo Pedido</p>", unsafe_allow_html=True)
    doc_busca = st.text_input("Digite o CPF ou CNPJ do Cliente:")
    if doc_busca:
        cliente_encontrado = buscar_cliente(doc_busca)
        if cliente_encontrado:
            st.info(f"Cliente identificado: {cliente_encontrado}")
            autor_input = st.text_input("Seu Nome (Dono do Pedido):", key="novo_autor_pedido")
            if st.button("Confirmar e Criar Pedido", type="primary"):
                if autor_input.strip() != "":
                    criar_novo_pedido(doc_busca, autor_input.strip().lower())
                    st.success("Pedido enviado para 'Pedido Criado'!")
                    st.rerun()
                else:
                    st.error("Por favor, preencha o seu nome para sabermos quem é o autor do pedido.")
        else:
            st.error("Cliente não localizado. Realize o cadastro primeiro.")

st.markdown("---")

# 3. Definição das 8 Colunas do Kanban
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
            
            # Detalhes do pedido (Popover)
            with st.popover("⚙️ Detalhes / Opções", use_container_width=True):
                st.write(f"**Pedido:** P-{row['id']}")
                st.write(f"**Cliente:** {row['nome']} ({row['documento_cliente']})")
                st.write(f"👤 **Autor do Pedido:** {row['autor'].title()}")
                st.info(row['observacoes'] if row['observacoes'] else "Sem informações adicionadas.")
                
                # ATUALIZAÇÃO: Visualizador interno de arquivos na própria página
                if row['arquivo_caminho'] and os.path.exists(row['arquivo_caminho']):
                    nome_arquivo = os.path.basename(row['arquivo_caminho'])
                    extensao = nome_arquivo.split('.')[-1].lower()
                    
                    st.markdown(f"📎 **Arquivo Anexado:** `{nome_arquivo}`")
                    
                    with open(row['arquivo_caminho'], "rb") as f:
                        dados_arquivo = f.read()
                    
                    # Se for PDF, renderiza em um iframe interativo embutido
                    if extensao == "pdf":
                        base64_pdf = base64.b64encode(dados_arquivo).decode('utf-8')
                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="400" type="application/pdf"></iframe>'
