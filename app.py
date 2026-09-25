import streamlit as st
import sqlite3
import pandas as pd

# 1. Configuração e Conexão com Banco de Dados SQLite
DB_FILE = "sistema_agendor_custom.db"

def criar_banco():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Tabela de Clientes (PF e PJ)
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
    # Tabela de Pedidos
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

# Estilização CSS para botões amarelos no topo direito e cards minimalistas
st.markdown("""
    <style>
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; }
    .stButton>button { border-radius: 4px; }
    /* Botões amarelos do topo */
    div[data-testid="column"] button[p-id="botao-amarelo"] {
        background-color: #FFD700 !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: none !important;
        width: 100%;
    }
    /* Estilo dos mini-cards */
    .card-pedido {
        background-color: #f8f9fa;
        border-left: 4px solid #FFD700;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Layout do Cabeçalho
col_titulo, col_btn1, col_btn2 = st.columns([6, 2, 2])

with col_titulo:
    st.title("📋 Painel de Controle")

# Botões superiores amarelos usando janelas abertas por expanders discretos
with col_btn1:
    criar_cad = st.expander("👤 Criar Cadastro")
with col_btn2:
    criar_ped = st.expander("📦 Criar Pedido")

# Fluxo do botão Criar Cadastro
with criar_cad:
    st.subheader("Cadastro de Cliente")
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
    st.subheader("Abertura de Pedido")
    doc_busca = st.text_input("Digite o CPF ou CNPJ do Cliente:")
    if doc_busca:
        cliente_encontrado = buscar_cliente(doc_busca)
        if cliente_encontrado:
            st.info(f"Cliente identificado: {cliente_encontrado[0]} ({cliente_encontrado[1]})")
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
        # Título compacto para caber as 8 colunas na tela
        st.markdown(f"<p style='font-size:13px; font-weight:bold; margin-bottom:2px;'>{etapa.upper()}</p>", unsafe_allow_html=True)
        st.markdown("<hr style='margin-top:2px; margin-bottom:8px;'>", unsafe_allow_html=True)
        
        pedidos_fase = df_pedidos[df_pedidos["etapa"] == etapa] if not df_pedidos.empty else pd.DataFrame()
        
        for _, row in pedidos_fase.iterrows():
            # Card compacto customizado
            st.markdown(f"""
                <div class='card-pedido'>
                    <b style='font-size:14px;'>P-{row['id']}</b><br>
                    <small style='color:#555;'>{row['nome']}</small>
                </div>
            """, unsafe_allow_html=True)
            
            # Botão de Ação/Detalhes do pedido
            with st.popover("⚙️ Detalhes / Mover", use_container_width=True):
                st.write(f"**Pedido:** P-{row['id']}")
                st.write(f"**Cliente:** {row['nome']} ({row['documento_cliente']})")
                
                # Exibe observações atuais
                st.info(row['observacoes'] if row['observacoes'] else "Sem informações adicionadas.")
                
                # Inputs de atualização
                novas_obs = st.text_area("Adicionar Informações / Histórico:", value=row['observacoes'], key=f"obs_{row['id']}")
                
                # Upload de arquivos (armazenamento temporário em memória nesta versão simples)
                arquivo = st.file_uploader("Adicionar arquivos:", key=f"file_{row['id']}")
                if arquivo:
                    st.caption(f"📎 Arquivo carregado: {arquivo.name}")
                
                # Seleção manual da próxima aba
                nova_fase = st.selectbox("Mover manualmente para:", etapas, index=etapas.index(etapa), key=f"fase_{row['id']}")
                
                if st.button("Salvar Alterações", key=f"save_{row['id']}", type="primary"):
                    atualizar_pedido(row['id'], nova_fase, novas_obs)
                    st.success("Atualizado!")
                    st.rerun()

