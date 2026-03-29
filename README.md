# 🚀 AI Research Assistant (RAG-Based)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-red)
![Qdrant](https://img.shields.io/badge/Qdrant-VectorDB-orange)

An end-to-end system that allows users to ask questions on pre-indexed documents or upload their own PDFs to build a custom knowledge base.

Instead of relying only on an LLM, this project retrieves relevant information from a vector database and uses it to generate more reliable, source-backed answers.

This project implements a practical **retrieval-augmented generation (RAG)** pipeline designed to handle real-world constraints such as latency, ingestion time, and deployment limitations.

---

## 🌐 Live Demo

- **Frontend (Streamlit):** https://ai-research-assistant-rag-fhhschaxt7xy2r2sqvphbs.streamlit.app
- **Backend API:** https://ai-research-assistant-rag-2z6f.onrender.com

---

## 🧠 What This Project Solves

LLMs alone:
- Can hallucinate  
- Don’t know your private data  
- Can’t verify answers  

This system solves that using:

> **Retrieve → Re-rank → Generate**

- Retrieve relevant chunks  
- Improve quality using reranking  
- Generate answers with context  

---

## ⚙️ How It Works

### 1. Ingestion
- PDFs are parsed using **PyMuPDF**  
- Text is split into chunks  
- Each chunk is converted into embeddings  
- Stored in **Qdrant (vector database)**  

### 2. Retrieval
- Relevant chunks are fetched using **semantic search**  
- Results are **re-ranked using a cross-encoder**  
- Optional **domain filtering** improves precision  

### 3. Generation
- Top context is passed to **LLaMA 3 (Groq)**  
- Response includes:
  - Answer  
  - Sources  
  - Confidence  

---

## 🏗️ Architecture

```mermaid
flowchart LR
    A[User] --> B[Streamlit UI]
    B --> C[FastAPI Backend]

    C --> D[PDF Upload]
    D --> E[Text Chunking]
    E --> F[Embedding Model]
    F --> G[Qdrant Vector DB]

    A --> H[Query]
    H --> C
    C --> I[Retriever]
    I --> G
    I --> J[Top Context]

    J --> K[LLM]
    K --> L[Answer + Sources] 
   ```

---

## ✨ Key Features

- 📂 Document → searchable knowledge base  
- 🔍 Semantic retrieval using embeddings  
- 🧠 Cross-encoder reranking for better relevance  
- 🏷️ Domain-based filtering  
- 📊 Source attribution in responses  
- ⚡ Background ingestion (non-blocking API)  

---

## 🧰 Tech Stack

### Backend
- **FastAPI**
- **Uvicorn**

### Frontend
- **Streamlit**

### AI / ML
- **Sentence Transformers (MiniLM)**
- **Cross-Encoder (reranking)**
- **LLaMA 3 (Groq API)**

### Database
- **Qdrant (Vector DB)**

### Deployment
- **Render (Backend)**
- **Streamlit Cloud (Frontend)**

---

## 📂 Project Structure

```bash
ai-research-assistant-RAG/
│
├── api/              # FastAPI endpoints
├── services/         # ingestion & retrieval logic
├── app/              # Streamlit UI
├── config/           # settings & env handling
├── uploads/          # stored documents
│
├── requirements.txt
└── README.md
```

## 🚀 Running Locally

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/ai-research-assistant-RAG.git
cd ai-research-assistant-RAG
```
### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
### 3. Start backend
```bash
uvicorn api.main:app --reload
```
### 4. Start frontend
```bash
streamlit run app/app.py
```

## 🔐 Environment variables

### Create a .env file:
```env
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_key
QDRANT_COLLECTION=docs

EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2

STREAMLIT_BACKEND_URL=https://your-backend.onrender.com
GROQ_API_KEY=your_key
```
## ⚡ Performance Considerations

- Background ingestion prevents request timeouts  
- Chunk limits keep processing stable  
- Embedding model is cached to avoid reload overhead  
- Vector inserts are batched for efficiency  

---

## 🧠 What This Project Demonstrates

- Building a complete **RAG pipeline (ingest → retrieve → generate)**  
- Working with **vector databases and embeddings**  
- Improving retrieval quality using **reranking**  
- Handling real-world deployment constraints (timeouts, performance)  

---

## 👨‍💻 Author

**Yugandhar Narravula**