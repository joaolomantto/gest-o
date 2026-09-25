import streamlit as st
import sqlite3
import pandas as pd

# 1. Banco de Dados SQLite
DB_FILE = "sistema_pedidos.db"

def criar_banco():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            pedido TEXT NOT NULL,
            etapa TEXT NOT NULL,
            valor REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

def carregar_dados():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM pedidos", conn)
    conn.close()
    return df

def inserir_pedido(cliente, pedido, valor):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO pedidos (cliente, pedido, etapa, valor) VALUES (?, ?, 'Contato', ?)", (cliente, pedido, valor))
    conn.commit()
    conn.close()

def atualizar_etapa(id_pedido, nova_etapa):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE pedidos SET etapa = ? WHERE id = ?", (nova_etapa, id_pedido))
    conn.commit()
    conn.close()

criar_banco()

# 2. Configuração da Página igual ao Agendor
st.set_page_config(layout="wide", page_title="Funil de Vendas", page_icon="💼")

# Cabeçalho Superior
st.title("💼 Funil de Vendas")

df_atual = carregar_dados()
total_negocios = len(df_atual)
valor_total = df_atual["valor"].sum() if not df_atual.empty else 0.0

st.markdown(f"### 📊 R\$ {valor_total:,.2f} | `{total_negocios} negócios`")
st.markdown("---")

# --- FORMULÁRIO DE CADASTRO (No topo) ---
with st.expander("➕ Adicionar Novo Negócio / Pedido", expanded=False):
    with st.form("cadastro_pedido", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            cliente = st.text_input("Nome do Cliente / Empresa:")
        with col2:
            pedido_detalhe = st.text_input("Descrição do Negócio (Ex: Pacote Master):")
        with col3:
            valor = st.number_input("Valor (R\$):", min_value=0.0, step=100.0)
        
        submetido = st.form_submit_button("Salvar Negócio", type="primary")
        
        if submetido and cliente and pedido_detalhe:
            inserir_pedido(cliente, pedido_detalhe, valor)
            st.success("Negócio adicionado ao funil!")
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# --- COLUNAS DO FUNIL (IGUAL À FOTO) ---
# Definição das etapas idênticas à imagem que você mandou
etapas = ["Contato", "Apresentação", "Proposta", "Negociação"]

# Cria as colunas lado a lado na tela
colunas_tela = st.columns(len(etapas))

for i, etapa in enumerate(etapas):
    with colunas_tela[i]:
        # Filtra dados da etapa atual
        pedidos_da_etapa = df_atual[df_atual["etapa"] == etapa] if not df_atual.empty else pd.DataFrame()
        total_etapa = len(pedidos_da_etapa)
        valor_etapa = pedidos_da_etapa["valor"].sum() if not pedidos_da_etapa.empty else 0.0
        
        # Título da Coluna com o totalizador em dinheiro embaixo
        st.markdown(f"#### **{etapa.upper()}**")
        st.markdown(f"<small style='color:gray;'>{total_etapa} • R\$ {valor_etapa:,.2f}</small>", unsafe_allow_html=True)
        st.markdown("---")
        
        if pedidos_da_etapa.empty:
            st.caption("Nenhum negócio aqui.")
        else:
            for idx, row in pedidos_da_etapa.iterrows():
                # Cria o "Card" (cartão do Trello/Agendor)
                with st.container(border=True):
                    st.markdown(f"**{row['id']} - {row['cliente']}**")
                    st.markdown(f"<small>{row['pedido']}</small>", unsafe_allow_html=True)
                    st.markdown(f"**R\$ {row['valor']:,.2f}**")
                    
                    # Botão para empurrar o card para o lado direito
                    if i < len(etapas) - 1:
                        proxima_etapa = etapas[i + 1]
                        if st.button(f"➡️ Mover", key=f"btn_{row['id']}"):
                            atualizar_etapa(row['id'], proxima_etapa)
                            st.rerun()
