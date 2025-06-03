# SISTEMA COMPLETO DE REBAIXA DE PREÇOS - VISUAL MODERNO E FUNCIONAL COM GRÁFICOS
import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
import base64

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
    st.title("🔐 Login - Sistema de Rebaixa")
    col1, col2 = st.columns(2)
    with col1:
        usuario = st.text_input("Usuário")
    with col2:
        senha = st.text_input("Senha", type="password")
    col1, col2 = st.columns([2, 1])
    if col1.button("Entrar"):
        if usuario in usuarios and usuarios[usuario]["senha"] == senha:
            st.session_state.logado = True
            st.session_state.usuario = usuario
            st.session_state.loja = usuarios[usuario]["loja"]
            st.session_state.nivel = usuarios[usuario]["nivel"]
            st.session_state.timeout = datetime.now()
            st.rerun()
        else:
            st.error("❌ Usuário ou senha inválidos.")
    if col2.button("Esqueci Senha"):
        st.info("Entre em contato com o administrador para redefinir sua senha.")
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

# ========== BASE EAN ==========
if os.path.exists("produtos_base.csv"):
    base_ean = pd.read_csv("produtos_base.csv")
else:
    base_ean = pd.DataFrame(columns=["EAN", "Nome"])

menu_opcoes = ["Cadastrar Produto", "Relatórios", "Gráficos"]
if st.session_state.nivel == "admin":
    menu_opcoes.insert(1, "Retaguarda")
menu = st.sidebar.selectbox("Menu", menu_opcoes)

# ========== CADASTRO ==========
if menu == "Cadastrar Produto":
    st.header("📝 Cadastrar Produto")
    with st.form("form_produto"):
        ean = st.text_input("Código EAN")
        nome_auto = base_ean[base_ean["EAN"] == ean]["Nome"].values
        nome = nome_auto[0] if len(nome_auto) > 0 else ""
        nome = st.text_input("Nome do Produto", value=nome)
        qtd = st.number_input("Quantidade a vencer", min_value=1)
        validade = st.date_input("Data de validade", min_value=date.today())
        preco = st.text_input("Preço Atual")
        responsavel = st.text_input("Responsável")
        loja = st.session_state.loja if st.session_state.nivel != "admin" else st.selectbox("Loja", sorted(set([str(u['loja']) for u in usuarios.values() if u['nivel'] == 'loja'])))
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
            st.experimental_rerun()

# ========== RETAGUARDA ==========
if menu == "Retaguarda" and st.session_state.nivel == "admin":
    st.header("📋 Retaguarda de Produtos")
    df = pd.DataFrame(st.session_state.db)
    if not df.empty:
        df["Validade"] = pd.to_datetime(df["Validade"], errors='coerce')
        df["Dias para Vencer"] = (df["Validade"] - pd.to_datetime(date.today())).dt.days

        loja_filtro = st.selectbox("Selecionar Loja", sorted(df["Loja"].unique()))
        status_filtro = st.selectbox("Status", ["Aguardando", "Precificado", "Todos"])
        df = df[df["Loja"] == loja_filtro]
        if status_filtro != "Todos":
            df = df[df["Status"] == status_filtro]

        st.dataframe(df[["EAN", "Nome", "Validade", "Preço Atual", "Preço Sugestão", "Status"]], use_container_width=True)

        for i, row in df.iterrows():
            st.markdown(f"### 🛒 {row['Nome']} (EAN: {row['EAN']})")
            st.write(f"Validade: {row['Validade'].date()} | Dias para vencer: {row['Dias para Vencer']}")
            preco_novo = st.text_input("Novo Preço de Oferta", value=row.get("Preço Sugestão", ""), key=f"novo_preco_{i}")
            col1, col2 = st.columns(2)
            if col1.button("✅ Confirmar", key=f"confirmar_{i}"):
                for j, item in enumerate(st.session_state.db):
                    if item["EAN"] == row["EAN"] and item["Loja"] == row["Loja"]:
                        st.session_state.db[j]["Preço Sugestão"] = preco_novo
                        st.session_state.db[j]["Status"] = "Precificado"
                        break
                pd.DataFrame(st.session_state.db).to_csv("produtos.csv", index=False)
                st.rerun()
            if col2.button("🗑️ Excluir", key=f"excluir_{i}"):
                st.session_state.db = [x for x in st.session_state.db if not (x["EAN"] == row["EAN"] and x["Loja"] == row["Loja"])]
                pd.DataFrame(st.session_state.db).to_csv("produtos.csv", index=False)
                st.rerun()

# ========== RELATÓRIOS ==========
if menu == "Relatórios":
    st.header("📑 Relatórios")
    df = pd.DataFrame(st.session_state.db)
    if not df.empty:
        df["Validade"] = pd.to_datetime(df["Validade"], errors='coerce')
        df["Dias para Vencer"] = (df["Validade"] - pd.to_datetime(date.today())).dt.days

        loja_filtro = st.selectbox("Filtrar Loja", ["Todos"] + sorted(df["Loja"].unique()))
        status_filtro = st.selectbox("Status", ["Todos", "Aguardando", "Precificado"])
        if loja_filtro != "Todos":
            df = df[df["Loja"] == loja_filtro]
        if status_filtro != "Todos":
            df = df[df["Status"] == status_filtro]

        st.dataframe(df[["Loja", "EAN", "Nome", "Validade", "Preço Atual", "Preço Sugestão", "Status"]], use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Baixar CSV", data=csv, file_name="relatorio.csv")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        for _, row in df.iterrows():
            pdf.cell(200, 8, txt=f"{row['Loja']} - {row['EAN']} - {row['Nome']} - {row['Validade'].date()} - R$ {row['Preço Sugestão']}", ln=True)
        pdf_output = "relatorio.pdf"
        pdf.output(pdf_output)
        with open(pdf_output, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="relatorio.pdf">📄 Baixar PDF</a>', unsafe_allow_html=True)

# ========== GRÁFICOS ==========
if menu == "Gráficos":
    st.header("📊 Gráficos")
    df = pd.DataFrame(st.session_state.db)
    if not df.empty:
        df["Validade"] = pd.to_datetime(df["Validade"], errors='coerce')
        df["Dias para Vencer"] = (df["Validade"] - pd.to_datetime(date.today())).dt.days

        col1, col2 = st.columns(2)
        with col1:
            inc = df.groupby("Data Cadastro")["EAN"].count()
            st.subheader("📆 Inclusões por Data")
            st.line_chart(inc)
        with col2:
            prec = df[df["Status"] == "Precificado"].groupby("Loja")["EAN"].count()
            st.subheader("🏪 Precificados por Loja")
            st.bar_chart(prec)
        col1, col2 = st.columns(2)
        with col1:
            venc = df[df["Dias para Vencer"] < 0].groupby("Loja")["EAN"].count()
            st.subheader("⛔ Vencidos por Loja")
            st.bar_chart(venc)
        with col2:
            status_df = df["Status"].value_counts()
            st.subheader("📌 Status Geral")
            st.bar_chart(status_df)
    else:
        st.info("Nenhum dado disponível para gráficos.")
