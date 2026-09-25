import streamlit as st
import sqlite3
import pandas as pd

# Configuração e Conexão com Banco de Dados SQLite
DB_FILE = "sistema_pedidos.db"

def criar_banco():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            pedido TEXT NOT NULL,
            etapa TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def carregar_dados():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM pedidos", conn)
    conn.close()
    return df

def inserir_pedido(cliente, pedido):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO pedidos (cliente, pedido, etapa) VALUES (?, ?, 'Aguardando')", (cliente, pedido))
    conn.commit()
    conn.close()

def atualizar_etapa(id_pedido, nova_etapa):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE pedidos SET etapa = ? WHERE id = ?", (nova_etapa, id_pedido))
    conn.commit()
    conn.close()

criar_banco()

# Interface do Sistema
st.set_page_config(layout="wide", page_title="Sistema de Pedidos", page_icon="📌")
st.title("📌 Sistema de Pedidos & Funil")

st.header("✨ Novo Pedido")
with st.form("cadastro_pedido", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        cliente = st.text_input("Nome do Cliente:")
    with col2:
        pedido_detalhe = st.text_input("Descrição do Pedido:")
    
    submetido = st.form_submit_button("Cadastrar Pedido")
    
    if submetido and cliente and pedido_detalhe:
        inserir_pedido(cliente, pedido_detalhe)
        st.success("Pedido cadastrado com sucesso!")
        st.rerun()

st.markdown("---")

st.header("📋 Fluxo de Trabalho (Estilo Trello)")
etapas = ["Aguardando", "Em Produção", "Enviado", "Concluído"]
abas = st.tabs(etapas)

df_atual = carregar_dados()

for i, etapa in enumerate(etapas):
    with abas[i]:
        pedidos_da_etapa = df_atual[df_atual["etapa"] == etapa]
        
        if pedidos_da_etapa.empty:
            st.info("Nenhum pedido nesta etapa.")
        
        for idx, row in pedidos_da_etapa.iterrows():
            with st.container(border=True):
                st.subheader(f"📦 {row['pedido']}")
                st.write(f"**Cliente:** {row['cliente']} | **ID:** {row['id']}")
                
                if i < len(etapas) - 1:
                    proxima_etapa = etapas[i + 1]
                    if st.button(f"➡️ Avançar para {proxima_etapa}", key=f"btn_{row['id']}"):
                        atualizar_etapa(row['id'], proxima_etapa)
                        st.rerun()
