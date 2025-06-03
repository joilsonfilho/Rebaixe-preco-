# from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import streamlit as st
import pandas as pd
import cv2

# =============================
# CLASSE SCANNER DE QR CODE
# =============================
class QRScanner(VideoTransformerBase):
    def _init_(self):
        self.last_code = ""

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(img)

        if data:
            self.last_code = data
            if bbox is not None:
                bbox = bbox.astype(int)
                for i in range(len(bbox[0])):
                    pt1 = tuple(bbox[0][i])
                    pt2 = tuple(bbox[0][(i + 1) % len(bbox[0])])
                    cv2.line(img, pt1, pt2, (0, 255, 0), 2)
                cv2.putText(img, data, (bbox[0][0][0], bbox[0][0][1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        return img

# =============================
# INTERFACE PRINCIPAL
# =============================

# Lista de usuários e senhas
usuarios = {
    "loja01": "senha123",
    "loja02": "senha456",
    "gerente": "admin",
    "loja710": "loja710"
}

# Verifica se está logado
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if usuario in usuarios and usuarios[usuario] == senha:
            st.session_state.logado = True
            st.session_state.usuario = usuario
            st.success("✅ Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("❌ Usuário ou senha inválidos.")
    st.stop()

# Após login
if 'usuario' in st.session_state: st.sidebar.write(f"👤 Usuário: {st.session_state.usuario}")
st.title("📉 Sistema de Rebaixa de Preços")

# Banco de dados em memória
if "db" not in st.session_state:
    st.session_state.db = []

# MENU PRINCIPAL
menu = st.sidebar.selectbox("Menu", ["Cadastrar Produto", "Retaguarda"])

# =============================
# CADASTRO DE PRODUTO
# =============================
if menu == "Cadastrar Produto":
    st.header("📦 Cadastro de Produto")

    st.subheader("📷 Escaneie o QR Code do produto")
    ctx = webrtc_streamer(key="scanner", video_transformer_factory=QRScanner)
    ean = st.text_input("Código EAN", value="", key="ean_input")

    if ctx.video_transformer and ctx.video_transformer.last_code:
        ean = ctx.video_transformer.last_code
        st.session_state.ean_input = ean
        st.success(f"📦 Código detectado: {ean}")

    nome = st.text_input("Nome do Produto")
    quantidade = st.number_input("Quantidade a vencer", min_value=1, step=1)
    validade = st.date_input("Data de validade")
    loja = st.text_input("Número da Loja")
    preco_atual = st.number_input("Preço Atual", min_value=0.01, format="%.2f")
    preco_sugerido = st.number_input("Preço Sugerido", min_value=0.01, format="%.2f")
    responsavel = st.text_input("Responsável")

    if st.button("Cadastrar"):
        novo_produto = {
            "EAN": ean,
            "Nome": nome,
            "Quantidade": quantidade,
            "Validade": validade,
            "Loja": loja,
            "Preço Atual": preco_atual,
            "Preço Sugerido": preco_sugerido,
            "Responsável": responsavel,
            "Status": "Aguardando"
        }
        st.session_state.db.append(novo_produto)
        st.success("✅ Produto cadastrado com sucesso!")

# =============================
# RETAGUARDA
# =============================
elif menu == "Retaguarda":
    st.header("📋 Produtos na Retaguarda")

    if len(st.session_state.db) == 0:
        st.info("Nenhum produto cadastrado ainda.")
    else:
        df = pd.DataFrame(st.session_state.db)
        st.dataframe(df, use_container_width=True)

        for i, row in df.iterrows():
            st.subheader(f"Produto: {row['Nome']} - EAN: {row['EAN']}")

            # Campo para editar o preço
            novo_preco = st.number_input(
                f"Novo Preço sugerido para {row['Nome']}",
                value=row["Preço Sugerido"],
                min_value=0.01,
                step=0.01,
                format="%.2f",
                key=f"preco_{i}"
            )

            # Botão para atualizar o preço
            if st.button(f"💰 Atualizar Preço de {row['Nome']}", key=f"att_{i}"):
                st.session_state.db[i]["Preço Sugerido"] = novo_preco
                st.success(f"💰 Preço de {row['Nome']} atualizado com sucesso!")

            # Botão para marcar como precificado
            if st.button(f"✅ Confirmar Precificação {row['EAN']}", key=i):
                st.session_state.db[i]["Status"] = "Precificado"
                st.success(f"✅ Produto {row['Nome']} foi marcado como Precificado!")