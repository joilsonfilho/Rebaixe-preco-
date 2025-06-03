# SISTEMA COMPLETO DE REBAIXA DE PREÇOS - VISUAL MODERNO COM CARTÕES, PDF E FILTROS
import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
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
st.title("📉 Sistema de Rebaixa de Preços")

if 'db' not in st.session_state:
    if os.path.exists("produtos.csv"):
        try:
            st.session_state.db = pd.read_csv("produtos.csv").to_dict(orient="records")
        except:
            st.session_state.db = []
    else:
        st.session_state.db = []

df = pd.DataFrame(st.session_state.db)

menu_opcoes = ["Cadastrar Produto", "Retaguarda"]
if st.session_state.nivel == "admin":
    menu_opcoes.append("Relatórios")
menu = st.sidebar.selectbox("Menu", menu_opcoes)

# ========== CADASTRO ==========
if menu == "Cadastrar Produto":
    st.header("📝 Cadastrar Novo Produto")
    with st.form("form_produto"):
        ean = st.text_input("Código EAN")
        nome = st.text_input("Nome do Produto")
        qtd = st.number_input("Quantidade a vencer", min_value=1)
        validade = st.date_input("Data de validade", min_value=date.today())
        preco = st.text_input("Preço Atual")
        responsavel = st.text_input("Responsável")
        loja = st.session_state.loja if st.session_state.nivel != "admin" else st.selectbox("Loja", ["710", "728", "736", "655", "647", "450", "531"])
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
if menu == "Retaguarda":
    st.header("📋 Retaguarda de Produtos")
    df = pd.DataFrame(st.session_state.db)
    df["Validade"] = pd.to_datetime(df["Validade"], errors='coerce')
    df["Dias para Vencer"] = (df["Validade"] - pd.to_datetime(date.today())).dt.days
    df["Loja"] = df["Loja"].astype(str)

    loja_filtro = st.selectbox("Filtrar por Loja", sorted(df["Loja"].unique()))
    df = df[df["Loja"] == loja_filtro]

    for i, row in df.iterrows():
        with st.container():
            st.markdown(f"#### 🛒 {row['Nome']} (EAN: {row['EAN']})")
            st.write(f"📍 Loja: {row['Loja']} | 🗓️ Validade: {row['Validade'].date()} | ⏳ Dias: {row['Dias para Vencer']}")
            st.write(f"💲 Atual: R$ {row['Preço Atual']} | 💡 Sugestão: R$ {row.get('Preço Sugestão', '-')}")
            preco_novo = st.text_input("Novo Preço de Oferta", value=row.get("Preço Sugestão", ""), key=f"preco_{i}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar", key=f"confirma_{i}"):
                    for idx, item in enumerate(st.session_state.db):
                        if item["EAN"] == row["EAN"] and item["Loja"] == row["Loja"]:
                            st.session_state.db[idx]["Preço Sugestão"] = preco_novo
                            st.session_state.db[idx]["Status"] = "Precificado"
                            pd.DataFrame(st.session_state.db).to_csv("produtos.csv", index=False)
                            st.success("Produto atualizado!")
                            st.rerun()
            with col2:
                if st.button("🗑️ Excluir", key=f"excluir_{i}"):
                    st.session_state.db = [item for item in st.session_state.db if not (item["EAN"] == row["EAN"] and item["Loja"] == row["Loja"])]
                    pd.DataFrame(st.session_state.db).to_csv("produtos.csv", index=False)
                    st.warning("Produto excluído.")
                    st.rerun()
