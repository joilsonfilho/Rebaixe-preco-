# SISTEMA COMPLETO DE REBAIXA DE PREÇOS - COMPATÍVEL COM STREAMLIT CLOUD
import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
import matplotlib.pyplot as plt

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

# ========== CADASTRO ==========
if menu == "Cadastrar Produto":
    st.header(":memo: Cadastrar Produto")
    with st.form("form_produto"):
        ean = st.text_input("Código EAN")
        nome = st.text_input("Nome do Produto")
        qtd = st.number_input("Quantidade a vencer", min_value=1)
        validade = st.date_input("Data de validade", min_value=date.today())
        preco = st.text_input("Preço Atual")
        responsavel = st.text_input("Responsável")
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
if menu == "Retaguarda":
    st.header(":clipboard: Retaguarda de Produtos")
    df = pd.DataFrame(st.session_state.db)
    df["Validade"] = pd.to_datetime(df["Validade"], errors='coerce')
    df["Dias para Vencer"] = (df["Validade"] - pd.to_datetime(date.today())).dt.days
    df["Dias de Antecedência"] = (pd.to_datetime(df["Validade"]) - pd.to_datetime(df["Data Cadastro"])).dt.days
    df["Loja"] = df["Loja"].astype(str)

    loja_selecionada = st.selectbox("Filtrar por Loja:", sorted(df["Loja"].unique()))
    df = df[df["Loja"] == loja_selecionada]

    col1, col2 = st.columns(2)
    with col1:
        status_filtro = st.selectbox("Filtrar por status:", ["Todos", "Aguardando", "Precificado"])
        if status_filtro != "Todos":
            df = df[df["Status"] == status_filtro]
    with col2:
        venc_filtro = st.radio("Vencimento:", ["Ambos", "Vencidos", "A vencer"], horizontal=True)
        if venc_filtro == "Vencidos":
            df = df[df["Dias para Vencer"] < 0]
        elif venc_filtro == "A vencer":
            df = df[df["Dias para Vencer"] >= 0]

    for i, row in df.iterrows():
        st.markdown(f"### 🛒 {row['Nome']} (EAN: {row['EAN']})")
        st.write(f"**Loja:** {row['Loja']}  |  **Validade:** {row['Validade'].date()}  |  **Dias para vencer:** {row['Dias para Vencer']}")
        st.write(f"**Preço Atual:** R$ {row['Preço Atual']}  |  **Preço Sugestão:** R$ {row.get('Preço Sugestão', '') or '-'}  |  **Status:** {row['Status']}")

        preco_novo = st.text_input("Novo Preço de Oferta", value=row.get("Preço Sugestão", ""), key=f"novo_preco_{i}")
        colc1, colc2 = st.columns(2)
        with colc1:
            if st.button("✅ Confirmar", key=f"confirmar_{i}"):
                st.session_state.db[i]["Preço Sugestão"] = preco_novo
                st.session_state.db[i]["Status"] = "Precificado"
                pd.DataFrame(st.session_state.db).to_csv("produtos.csv", index=False)
                st.success("Produto precificado!")
                st.rerun()
        with colc2:
            if st.button("🗑️ Excluir", key=f"excluir_{i}"):
                st.session_state.db.pop(i)
                pd.DataFrame(st.session_state.db).to_csv("produtos.csv", index=False)
                st.warning("Produto excluído.")
                st.rerun()
        st.divider()

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

    st.subheader(":chart_with_upwards_trend: Gráficos")
    col1, col2 = st.columns(2)
    with col1:
        venc = df[df["Dias para Vencer"] < 0].groupby("Loja")["EAN"].count()
        st.bar_chart(venc)
    with col2:
        inc = df.groupby("Data Cadastro")["EAN"].count()
        st.line_chart(inc)

    st.subheader(":factory: Precificados por Loja")
    prec = df[df["Status"] == "Precificado"].groupby("Loja")["EAN"].count()
    st.bar_chart(prec)

    st.subheader(":page_facing_up: Dados Filtrados")
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar CSV", data=csv, file_name="relatorio.csv", mime="text/csv")
