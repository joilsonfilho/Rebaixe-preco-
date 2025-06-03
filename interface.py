# SISTEMA COMPLETO DE REBAIXA DE PREÇOS - VISUAL MODERNO E FUNCIONAL
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
    "2003": {"senha": "@abc789", "loja": "todos", "nivel": "admin"},
}

# ========== LOGIN ==========
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.timeout = datetime.now()

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
st.title("📦 Sistema de Rebaixa de Preços")

if 'db' not in st.session_state:
    if os.path.exists("produtos.csv"):
        try:
            st.session_state.db = pd.read_csv("produtos.csv").to_dict(orient="records")
        except:
            st.session_state.db = []
    else:
        st.session_state.db = []

menu_opcoes = ["Cadastrar Produto", "Relatórios"]
if st.session_state.nivel == "admin":
    menu_opcoes.insert(1, "Retaguarda")
menu = st.sidebar.selectbox("Menu", menu_opcoes)

# ========== CADASTRO ==========
if menu == "Cadastrar Produto":
    st.header("📝 Cadastrar Produto")
    with st.form("form_produto"):
        ean = st.text_input("Código EAN")
        nome = st.text_input("Nome do Produto")
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
    st.header("📋 Retaguarda")
    df = pd.DataFrame(st.session_state.db)
    if df.empty:
        st.info("Nenhum produto cadastrado.")
    else:
        df["Validade"] = pd.to_datetime(df["Validade"], errors='coerce')
        df["Dias para Vencer"] = (df["Validade"] - pd.to_datetime(date.today())).dt.days

        loja_selecionada = st.selectbox("Loja", sorted(df["Loja"].unique()))
        df = df[df["Loja"] == loja_selecionada]

        status = st.selectbox("Status", ["Todos", "Aguardando", "Precificado"])
        if status != "Todos":
            df = df[df["Status"] == status]

        st.subheader("📊 Tabela Geral de Produtos")
        st.dataframe(df, use_container_width=True)

        st.subheader("✏️ Ações por Produto")
        for i, row in df.iterrows():
            st.markdown(f"**🛒 {row['Nome']}**")
            st.write(f"**EAN:** {row['EAN']} | **Validade:** {row['Validade'].date()} | **Dias para vencer:** {row['Dias para Vencer']}")
            preco_novo = st.text_input("Novo Preço de Oferta", value=row.get("Preço Sugestão", ""), key=f"preco_{i}")
            col1, col2 = st.columns(2)
            if col1.button("✅ Confirmar", key=f"confirmar_{i}"):
                for j, item in enumerate(st.session_state.db):
                    if item["EAN"] == row["EAN"] and item["Loja"] == row["Loja"]:
                        st.session_state.db[j]["Preço Sugestão"] = preco_novo
                        st.session_state.db[j]["Status"] = "Precificado"
                        break
                pd.DataFrame(st.session_state.db).to_csv("produtos.csv", index=False)
                st.success("Produto atualizado!")
                st.rerun()
            if col2.button("🗑️ Excluir", key=f"excluir_{i}"):
                st.session_state.db = [x for x in st.session_state.db if not (x["EAN"] == row["EAN"] and x["Loja"] == row["Loja"])]
                pd.DataFrame(st.session_state.db).to_csv("produtos.csv", index=False)
                st.warning("Produto excluído.")
                st.rerun()
            st.divider()

# ========== RELATÓRIOS ==========
if menu == "Relatórios":
    st.header("📈 Relatórios")
    df = pd.DataFrame(st.session_state.db)
    if not df.empty:
        df["Validade"] = pd.to_datetime(df["Validade"], errors='coerce')
        df["Dias para Vencer"] = (df["Validade"] - pd.to_datetime(date.today())).dt.days

        col1, col2 = st.columns(2)
        loja = col1.selectbox("Loja", ["Todos"] + sorted(df["Loja"].unique()))
        status = col2.selectbox("Status", ["Todos", "Aguardando", "Precificado"])

        if loja != "Todos": df = df[df["Loja"] == loja]
        if status != "Todos": df = df[df["Status"] == status]

        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Baixar CSV", data=csv, file_name="relatorio.csv")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for i, row in df.iterrows():
            pdf.cell(200, 10, txt=f"{row['Loja']} - {row['EAN']} - {row['Nome']} - {row['Validade'].date()} - R$ {row['Preço Sugestão']}", ln=True)
        pdf_output = "relatorio.pdf"
        pdf.output(pdf_output)
        with open(pdf_output, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            href = f'<a href="data:application/pdf;base64,{b64}" download="relatorio.pdf">📄 Baixar PDF</a>'
            st.markdown(href, unsafe_allow_html=True)
