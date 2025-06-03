
# SISTEMA COMPLETO DE REBAIXA DE PREÇOS - VISUAL APRIMORADO + EXPORTAÇÃO PDF
import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
from fpdf import FPDF

# ========== CONFIGURAÇÃO ==========
st.set_page_config(layout="wide", page_title="Sistema de Rebaixa de Preços", page_icon="🏷️")

# ========== USUÁRIOS ==========
usuarios = {
    "710": {"senha": "1234", "loja": "710", "nivel": "loja"},
    "728": {"senha": "1234", "loja": "728", "nivel": "loja"},
    "736": {"senha": "1234", "loja": "736", "nivel": "loja"},
    "655": {"senha": "1234", "loja": "655", "nivel": "loja"},
    "647": {"senha": "1234", "loja": "647", "nivel": "loja"},
    "450": {"senha": "1234", "loja": "450", "nivel": "loja"},
    "531": {"senha": "1234", "loja": "531", "nivel": "loja"},
    "2003": {"senha": "@abc789", "loja": "todos", "nivel": "admin"},
}

# ========== LOGIN ==========
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.timeout = datetime.now()

if datetime.now() > st.session_state.get("timeout", datetime.now()) + pd.Timedelta(hours=12):
    st.session_state.logado = False

if not st.session_state.logado:
    st.markdown("### 🔐 Login no Sistema")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if usuario in usuarios and usuarios[usuario]["senha"] == senha:
            st.session_state.logado = True
            st.session_state.usuario = usuario
            st.session_state.loja = usuarios[usuario]["loja"]
            st.session_state.nivel = usuarios[usuario]["nivel"]
            st.session_state.timeout = datetime.now()
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()

# ========== BASE ==========
st.sidebar.markdown(f"**👤 Usuário:** {st.session_state.usuario}")
st.sidebar.markdown(f"**🏬 Loja:** {st.session_state.loja}")

if 'db' not in st.session_state:
    if os.path.exists("produtos.csv"):
        try:
            st.session_state.db = pd.read_csv("produtos.csv").to_dict(orient="records")
        except:
            st.session_state.db = []
    else:
        st.session_state.db = []

menu_opcoes = ["📦 Cadastrar Produto"]
if st.session_state.nivel == "admin":
    menu_opcoes += ["📊 Retaguarda", "📁 Relatórios"]
menu = st.sidebar.selectbox("Menu", menu_opcoes)

# ========== CADASTRO ==========
if "Cadastrar" in menu:
    st.title("📦 Cadastro de Produtos")
    with st.form("form_produto"):
        col1, col2, col3 = st.columns(3)
        with col1:
            ean = st.text_input("Código EAN")
            nome = st.text_input("Nome do Produto")
            qtd = st.number_input("Quantidade a vencer", min_value=1)
        with col2:
            validade = st.date_input("Data de validade", min_value=date.today())
            preco = st.text_input("Preço Atual")
            responsavel = st.text_input("Responsável")
        with col3:
            loja = st.session_state.loja if st.session_state.nivel != "admin" else st.selectbox("Loja", ["710","728","736","655","647","450","531"])
        enviado = st.form_submit_button("Salvar")

    if enviado:
        if not all([ean, nome, qtd, validade, preco, responsavel]):
            st.warning("⚠️ Preencha todos os campos obrigatórios!")
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

# ========== RETAGUARDA ==========
if "Retaguarda" in menu:
    st.title("📊 Retaguarda de Produtos")
    df = pd.DataFrame(st.session_state.db)
    df["Validade"] = pd.to_datetime(df["Validade"], errors='coerce')
    df["Dias para Vencer"] = (df["Validade"] - pd.to_datetime(date.today())).dt.days

    loja = st.selectbox("Filtrar por Loja:", sorted(df["Loja"].unique()))
    status = st.selectbox("Status:", ["Todos", "Aguardando", "Precificado"])
    venc = st.radio("Vencimento:", ["Ambos", "Vencidos", "A vencer"], horizontal=True)

    if status != "Todos":
        df = df[df["Status"] == status]
    if venc == "Vencidos":
        df = df[df["Dias para Vencer"] < 0]
    elif venc == "A vencer":
        df = df[df["Dias para Vencer"] >= 0]
    df = df[df["Loja"] == loja]

    st.dataframe(df[["EAN", "Nome", "Loja", "Validade", "Preço Atual", "Preço Sugestão", "Status"]])

# ========== RELATÓRIOS ==========
if "Relatórios" in menu:
    st.title("📁 Relatórios")
    df = pd.DataFrame(st.session_state.db)
    df["Validade"] = pd.to_datetime(df["Validade"], errors='coerce')
    df["Dias para Vencer"] = (df["Validade"] - pd.to_datetime(date.today())).dt.days

    col1, col2 = st.columns(2)
    with col1:
        loja = st.selectbox("Filtrar Loja", ["Todos"] + sorted(df["Loja"].unique()))
        if loja != "Todos":
            df = df[df["Loja"] == loja]
    with col2:
        status = st.selectbox("Status", ["Todos", "Aguardando", "Precificado"])
        if status != "Todos":
            df = df[df["Status"] == status]

    st.subheader("📌 Tabela")
    st.dataframe(df[["Loja", "EAN", "Nome", "Validade", "Preço Sugestão"]])

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Relatório de Produtos", ln=True, align="C")
    for _, row in df.iterrows():
        texto = f"{row['Loja']} | {row['EAN']} | {row['Nome']} | {row['Validade'].date()} | R$ {row['Preço Sugestão']}"
        pdf.cell(200, 8, txt=texto, ln=True)

    with open("relatorio.pdf", "wb") as f:
        pdf.output(f)

    with open("relatorio.pdf", "rb") as f:
        st.download_button("📄 Baixar Relatório PDF", f, file_name="relatorio.pdf")
