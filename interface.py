# SISTEMA COMPLETO DE REBAIXA DE PREÇOS - VISUAL REFINADO E REGRAS AVANÇADAS
import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
import matplotlib.pyplot as plt
import io
from fpdf import FPDF

# ========== USUÁRIOS ==========
usuarios = {
    "710": {"senha": "1234", "loja": "710", "nivel": "loja"},
    "728": {"senha": "1234", "loja": "728", "nivel": "loja"},
    "736": {"senha": "1234", "loja": "736", "nivel": "loja"},
    "655": {"senha": "1234", "loja": "655", "nivel": "loja"},
    "647": {"senha": "1234", "loja": "647", "nivel": "loja"},
    "450": {"senha": "1234", "loja": "450", "nivel": "loja"},
    "531": {"senha": "1234", "loja": "531", "nivel": "loja"},
    "2003": {"senha": "1234", "loja": "todos", "nivel": "admin"},
}

# ========== LOGIN ==========
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.timeout = datetime.now()

# Mantém login válido por 12 horas
if datetime.now() > st.session_state.get("timeout", datetime.now()) + pd.Timedelta(hours=12):
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login")
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
            st.error("❌ Usuário ou senha inválidos.")
    st.stop()

# ========== BASE ==========
st.sidebar.write(f"👤 Usuário: {st.session_state.usuario} | Loja: {st.session_state.loja}")
st.title(":label: Sistema de Rebaixa de Preços")

if 'db' not in st.session_state:
    if os.path.exists("produtos.csv"):
        try:
            st.session_state.db = pd.read_csv("produtos.csv").to_dict(orient="records")
        except:
            st.session_state.db = []
    else:
        st.session_state.db = []

menu_opcoes = ["Cadastrar Produto"]
if st.session_state.nivel == "admin":
    menu_opcoes += ["Retaguarda", "Relatórios"]
menu = st.sidebar.selectbox("Menu", menu_opcoes)

# ========== RELATÓRIOS ==========
if menu == "Relatórios":
    st.header(":bar_chart: Relatórios de Preçificação")
    df = pd.DataFrame(st.session_state.db)
    df["Validade"] = pd.to_datetime(df["Validade"], errors='coerce')
    df["Dias para Vencer"] = (df["Validade"] - pd.to_datetime(date.today())).dt.days
    df["Dias de Antecedência"] = (pd.to_datetime(df["Validade"]) - pd.to_datetime(df["Data Cadastro"])).dt.days
    df["Loja"] = df["Loja"].astype(str)

    col1, col2, col3 = st.columns(3)
    with col1:
        loja_filtro = st.selectbox("Filtrar por Loja", ["Todos"] + sorted(df["Loja"].unique()))
        if loja_filtro != "Todos":
            df = df[df["Loja"] == loja_filtro]
    with col2:
        status_rel = st.selectbox("Status", ["Todos", "Aguardando", "Precificado"])
        if status_rel != "Todos":
            df = df[df["Status"] == status_rel]
    with col3:
        venc_rel = st.selectbox("Vencimento", ["Todos", "A vencer", "Vencidos"])
        if venc_rel == "A vencer":
            df = df[df["Dias para Vencer"] >= 0]
        elif venc_rel == "Vencidos":
            df = df[df["Dias para Vencer"] < 0]

    col1, col2 = st.columns(2)
    with col1:
        inicio = st.date_input("Data Inicial", value=date.today().replace(day=1))
    with col2:
        fim = st.date_input("Data Final", value=date.today())

    df = df[(pd.to_datetime(df["Data Cadastro"]).dt.date >= inicio) & (pd.to_datetime(df["Data Cadastro"]).dt.date <= fim)]

    st.subheader(":page_facing_up: Dados Filtrados")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar CSV", data=csv, file_name="relatorio.csv", mime="text/csv")

    def gerar_pdf(df):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Relatório de Produtos Precificados", ln=True, align="C")
        pdf.ln(10)
        for index, row in df.iterrows():
            texto = f"Loja: {row['Loja']} | EAN: {row['EAN']} | Nome: {row['Nome']} | Validade: {row['Validade'].date()} | Preço Sugestão: R$ {row['Preço Sugestão']}"
            pdf.multi_cell(0, 10, txt=texto)
        return pdf.output(dest='S').encode('latin1')

    pdf_bytes = gerar_pdf(df)
    st.download_button("📄 Baixar PDF", data=pdf_bytes, file_name="relatorio.pdf", mime="application/pdf")
