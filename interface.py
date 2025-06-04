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
        <style>
        .login-container {
            max-width: 400px;
            margin: auto;
            background-color: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        }
        .login-input input {
            font-size: 16px;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
        }
        .login-button button {
            background-color: #4CAF50;
            color: white;
            padding: 10px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.title("🔐 Login - Sistema de Rebaixa")
    usuario = st.text_input("👤 Usuário", key="login_user")
    senha = st.text_input("🔑 Senha", type="password", key="login_pass")
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("✅ Entrar"):
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
        if st.button("🔄 Esqueci Senha"):
            st.info("Entre em contato com o administrador para redefinir sua senha.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ========== BASE DE DADOS ==========
if 'db' not in st.session_state:
    if os.path.exists("produtos.csv"):
        try:
            st.session_state.db = pd.read_csv("produtos.csv").to_dict(orient="records")
        except:
            st.session_state.db = []
    else:
        st.session_state.db = []

# ========== MENU ==========
st.sidebar.write(f"👤 Usuário: {st.session_state.usuario} | Loja: {st.session_state.loja}")
menu_opcoes = ["Cadastrar Produto"]
if st.session_state.nivel == "admin":
    menu_opcoes.append("Retaguarda")
menu_opcoes += ["Relatórios", "Gráficos"]
menu = st.sidebar.selectbox("Menu", menu_opcoes)

# ========== CADASTRO DE PRODUTO ==========
if menu == "Cadastrar Produto":
    st.subheader("📋 Cadastro de Produto")
    with st.form("cadastro_form"):
        ean = st.text_input("Código EAN")
        nome = st.text_input("Nome do Produto")
        qtd = st.number_input("Quantidade a vencer", min_value=1)
        validade = st.date_input("Data de Validade", value=date.today())
        preco = st.text_input("Preço Atual")
        responsavel = st.text_input("Responsável")
        loja = st.session_state.loja if st.session_state.nivel != "admin" else st.selectbox("Loja", sorted(set([v['loja'] for v in usuarios.values() if v['nivel'] == 'loja'])))
        enviar = st.form_submit_button("💾 Salvar")

    if enviar:
        if not all([ean, nome, preco, responsavel]):
            st.warning("⚠️ Todos os campos obrigatórios devem ser preenchidos!")
        else:
            novo = {
                "EAN": ean,
                "Nome": nome,
                "Quantidade": qtd,
                "Validade": validade.strftime("%Y-%m-%d"),
                "Preço Atual": preco,
                "Preço Sugestão": "",
                "Responsável": responsavel,
                "Loja": loja,
                "Data Cadastro": date.today().strftime("%Y-%m-%d"),
                "Status": "Aguardando"
            }
            st.session_state.db.append(novo)
            pd.DataFrame(st.session_state.db).to_csv("produtos.csv", index=False)
            st.success("✅ Produto cadastrado com sucesso!")
            st.experimental_rerun()

# Continuação: Retaguarda, Relatórios, Gráficos e melhorias visuais seguem no próximo bloco.
