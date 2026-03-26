import requests
import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import settings

st.set_page_config(page_title="AI Research Assistant (RAG-Based)", layout="wide")
st.title("📚 AI Research Assistant (RAG-Based)")
st.write("Upload documents, choose a knowledge base, and ask grounded questions.")

if "session_id" not in st.session_state:
    st.session_state.session_id = None

backend = settings.STREAMLIT_BACKEND_URL

with st.sidebar:
    st.header("Knowledge Base")
    domain = st.selectbox(
        "Select Knowledge Base",
        ["general", "finance", "tech", "security", "all"],
        index=0,
    )

    st.header("Upload Document")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    upload_domain = st.selectbox(
        "Upload into domain",
        ["general", "finance", "tech", "security"],
        index=0,
        key="upload_domain",
    )

    if uploaded_file and st.button("Process File"):
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                "application/pdf",
            )
        }
        data = {"domain": upload_domain}

        try:
            # ✅ STEP 2: Wake up backend
            with st.spinner("Connecting to backend (first time may take ~40 sec)..."):
                try:
                    requests.get(f"{backend}/health", timeout=20)
                except:
                    pass

            # ✅ STEP 3: Upload with high timeout
            with st.spinner("Uploading..."):
                response = requests.post(
                    f"{backend}/upload",
                    files=files,
                    data=data,
                    timeout=120,
                )

            if response.ok:
                st.success("✅ Upload started. Processing in background.")
                st.info("⏳ Wait 30–60 sec before querying.")
            else:
                st.error(response.text)

        except requests.exceptions.ReadTimeout:
            st.warning("⚠️ Backend cold start. Click again in 20–30 seconds.")

query = st.text_input("Ask a question")

if st.button("Ask") and query:
    params = {
        "q": query,
        "domain": None if domain == "all" else domain,
        "session_id": st.session_state.session_id,
    }

    response = requests.get(f"{backend}/query", params=params, timeout=120)

    if response.ok:
        result = response.json()
        st.session_state.session_id = result["session_id"]

        st.subheader("🧠 Answer")
        st.markdown(result["answer"])

        st.subheader("Sources")
        for s in result["sources"]:
            st.write(f"- {s}")

        st.subheader("System Info")
        st.write(f"**Route:** {result['route']}")
        st.write(f"**Domain:** {result['domain']}")
        st.write(f"**Confidence:** {result['confidence']:.2f}")
        st.write(f"**Verified:** {result['verified']}")
        st.write(f"**Reason:** {result['verification_reason']}")

        with st.expander("Retrieved Context Preview"):
            st.text(result["context_preview"])
    else:
        st.error(response.text)
