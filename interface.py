# SISTEMA COMPLETO DE REBAIXA DE PREÇOS - VISUAL MODERNO E FUNCIONAL COM GRÁFICOS E ESTILO
import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
import base64

# ========== ESTILO PERSONALIZADO ==========
st.markdown("""
    <style>
    .main { background-color: #f5f7fa; }
    .block-container { padding-top: 2rem; }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        padding: 0.5em 1em;
    }
    .stTextInput > div > input, .stNumberInput input {
        border-radius: 5px;
        padding: 5px;
    }
    .stDataFrame, .stTable {
        border-radius: 10px;
        border: 1px solid #ddd;
        background-color: white;
    }
    .login-box {
        text-align:center;
        padding: 2em;
        background: #fff;
        border-radius: 10px;
        width: 350px;
        margin: auto;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .login-title {
        font-size: 24px;
        margin-bottom: 1em;
    }
    .login-button {
        margin-top: 1em;
    }
    </style>
""", unsafe_allow_html=True)

# ========== USUÁRIOS ==========
usuarios = {
    "710": {"senha": "1234", "loja": "710", "nivel": "loja"},
    "728": {"senha": "1234", "loja": "728", "nivel": "loja"},
    "736": {"senha": "1234", "loja": "736", "nivel": "loja"},
    "655": {"senha": "1234", "loja": "655", "nivel": "loja"},
    "647": {"senha": "1234", "loja": "647", "nivel": "loja"},
    "450": {"senha": "1234", "loja": "450", "nivel": "loja"},
    "531": {"senha": "1234", "loja": "531", "nivel": "loja"},
    "2003": {"senha": "admin", "loja": "todos", "nivel": "admin"},
}

# ========== LOGIN ==========
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.timeout = datetime.now()

if datetime.now() > st.session_state.get("timeout", datetime.now()) + pd.Timedelta(hours=12):
    st.session_state.logado = False

if not st.session_state.logado:
    st.markdown("""
        <div class="login-box">
            <div class="login-title">🔐 Login</div>
    """, unsafe_allow_html=True)
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Entrar", key="entrar"):
            if usuario in usuarios and usuarios[usuario]["senha"] == senha:
                st.session_state.logado = True
                st.session_state.usuario = usuario
                st.session_state.loja = usuarios[usuario]["loja"]
                st.session_state.nivel = usuarios[usuario]["nivel"]
                st.session_state.timeout = datetime.now()
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos.")
    with col2:
        st.button("Esqueci a senha", key="esqueci")
    st.markdown("""</div>""", unsafe_allow_html=True)
    st.stop()

# ========== BASE ==========
st.sidebar.write(f"👤 Usuário: {st.session_state.usuario} | Loja: {st.session_state.loja}")
st.title("📦 Sistema de Rebaixa de Preços")

if 'db' not in st.session_state:
    if os.path.exists("produtos.csv"):
        try:
            st.session_state.db = pd.read_csv("produtos.csv").to_dict(orient="records")
        except:
            st.session_state.db = []
    else:
        st.session_state.db = []

# ========== MENU ==========
menu_opcoes = ["Cadastrar Produto", "Relatórios", "Gráficos"]
if st.session_state.nivel == "admin":
    menu_opcoes.insert(1, "Retaguarda")
menu = st.sidebar.selectbox("Menu", menu_opcoes)

# ========== CADASTRO ==========
if menu == "Cadastrar Produto":
    st.header("📝 Cadastro de Produto")
    with st.form("formulario"):
        ean = st.text_input("Código EAN")
        nome = st.text_input("Descrição do Produto")
        validade = st.date_input("Data de Validade", min_value=date.today())
        preco = st.text_input("Preço Atual")
        preco_sugestao = st.text_input("Preço Sugestão")
        responsavel = st.text_input("Responsável")
        loja = st.session_state.loja
        status = "Aguardando"
        enviado = st.form_submit_button("Salvar")

    if enviado:
        if not all([ean, nome, validade, preco, preco_sugestao, responsavel]):
            st.warning("⚠️ Preencha todos os campos obrigatórios!")
        else:
            novo_produto = {
                "EAN": ean,
                "Nome": nome,
                "Validade": validade,
                "Preço Atual": preco,
                "Preço Sugestão": preco_sugestao,
                "Responsável": responsavel,
                "Loja": loja,
                "Data Cadastro": date.today(),
                "Status": status
            }
            st.session_state.db.append(novo_produto)
            pd.DataFrame(st.session_state.db).to_csv("produtos.csv", index=False)
            st.success("✅ Produto cadastrado com sucesso!")
            st.rerun()

# ========== GRÁFICOS ==========
if menu == "Gráficos":
    st.header("📊 Análises Visuais")
    df = pd.DataFrame(st.session_state.db)
    if not df.empty:
        df["Validade"] = pd.to_datetime(df["Validade"], errors='coerce')
        df["Dias para Vencer"] = (df["Validade"] - pd.to_datetime(date.today())).dt.days

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📆 Inclusões por Data")
            inc = df.groupby("Data Cadastro")["EAN"].count()
            st.line_chart(inc)
        with col2:
            st.subheader("🏪 Precificados por Loja")
            prec = df[df["Status"] == "Precificado"].groupby("Loja")["EAN"].count()
            st.bar_chart(prec)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("⛔ Vencidos por Loja")
            venc = df[df["Dias para Vencer"] < 0].groupby("Loja")["EAN"].count()
            st.bar_chart(venc)
        with col2:
            st.subheader("📌 Status Geral")
            status_df = df["Status"].value_counts()
            st.bar_chart(status_df)
    else:
        st.info("Nenhum dado disponível para gráficos.")
