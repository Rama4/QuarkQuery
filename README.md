# 🔬 QuarkQuery - AI Physics Research Assistant

An AI-powered RAG (Retrieval Augmented Generation) application that lets you ask questions about physics and get intelligent answers from a curated database of foundational physics research papers.

## ✨ Features

- 🔍 **Semantic Search** across 100 foundational physics papers
- 🤖 **AI-Powered Answers** using Groq's Llama 3.3 70B
- 📚 **Source Citations** with relevance scores
- 🎨 **Beautiful UI** built with Next.js and Tailwind CSS
- 📊 **API Status Dashboard** - Monitor service health and rate limits
- 🆓 **100% Free** hosting on Vercel with free tier APIs
- ⚡ **Fast** - 2-4 second query response times
- 🚀 **GPU-Accelerated** embeddings (10-50x faster with CUDA)
- ⚙️ **Parallel Processing** for fast data ingestion

## 🎯 Try It Live

[https://quark-query.vercel.app/](https://quark-query.vercel.app/)

### Example Questions

- "What is the AdS/CFT correspondence?"
- "Explain the KKLT construction for de Sitter vacua"
- "What are extra dimensions at a millimeter scale?"
- "Describe the Randall-Sundrum model"
- "What is the swampland program in string theory?"

### Features in Action

- 🔍 **Search** - Semantic search finds relevant passages across all 100 papers
- 🤖 **Answer** - AI generates comprehensive explanations
- 📚 **Citations** - See exact sources with relevance scores
- 📊 **Status** - Click "API Status" button to monitor service health

## 📚 Included Papers

**100 foundational physics papers** covering:

- **String Theory & M-theory** - Polchinski's D-branes, Witten's M-theory unification
- **AdS/CFT & Holography** - Maldacena's original correspondence, holographic entanglement
- **Extra Dimensions** - Randall-Sundrum models, large extra dimensions
- **Swampland Program** - Distance conjecture, de Sitter swampland
- **Black Holes** - Information paradox, microstate counting, Page curve
- **Quantum Information** - Holographic error correction, entanglement wedge reconstruction

Key papers include:

- **Maldacena (1997)** - The Large N Limit and AdS/CFT
- **Witten (1998)** - Anti de Sitter Space and Holography
- **KKLT (2003)** - de Sitter Vacua in String Theory
- **Randall-Sundrum** - Large Mass Hierarchy from Extra Dimensions
- **Strominger-Vafa (1996)** - Black hole microstate counting
- And 95 more foundational papers

## 🛠️ Tech Stack

| Component      | Technology              | Why                                 |
| -------------- | ----------------------- | ----------------------------------- |
| **Frontend**   | Next.js 14 + TypeScript | Modern, fast, SEO-friendly          |
| **Styling**    | Tailwind CSS 4          | Beautiful, responsive UI            |
| **Vector DB**  | Pinecone                | 100k vectors free, managed          |
| **LLM**        | Groq (Llama 3.3 70B)    | Fastest inference, 14k req/day free |
| **Embeddings** | Hugging Face            | Free API, sentence-transformers     |
| **Hosting**    | Vercel                  | Free, auto-deploy from GitHub       |

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and pnpm
- Python 3.8+
- API keys (all free):
  - [Pinecone](https://app.pinecone.io/)
  - [Groq](https://console.groq.com/)
  - [Hugging Face](https://huggingface.co/settings/tokens)

### 1. Clone & Install

```bash
git clone <your-repo>
cd "QuarkQuery"

# Install frontend dependencies
cd frontend
pnpm install

# Install Python dependencies (for ingestion)
cd ../ingestion
pip install -r requirements.txt
```

### 2. Download Papers (if not already downloaded)

```bash
cd ingestion

# Download 100 papers from arXiv (parallel processing)
python download_papers.py --yes
```

### 3. Extract & Process Papers

```bash
cd ingestion

# Step 1: Extract text from PDFs (parallel processing)
python extract_pdfs.py

# Step 2: Chunk text and generate embeddings (GPU-accelerated if available)
python chunk_and_embed.py

# Step 3: Upload to Pinecone (requires API key)
# Create .env file first with your keys
python upload_to_pinecone.py
```

**Note:** The scripts automatically detect and use GPU if available. For GPU support, install PyTorch with CUDA:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 4. Run Frontend

```bash
cd ../frontend

# Create .env.local with your API keys
cp env.example .env.local
# Edit .env.local and add your keys

# Run development server
pnpm dev
```

Visit http://localhost:3000 🎉

## 📁 Project Structure

```
.
├── ingestion/                # Data processing pipeline
│   ├── download_papers.py   # Download PDFs from arXiv (parallel)
│   ├── extract_pdfs.py      # PDF → JSON extraction (parallel)
│   ├── chunk_and_embed.py   # Text → Embeddings (GPU-accelerated)
│   ├── upload_to_pinecone.py # Upload to vector DB
│   ├── pending_papers.json  # List of 100 papers to download
│   ├── data/                # Downloaded PDFs
│   └── extracted_data/      # Generated JSON files
├── frontend/                 # Next.js application
│   ├── app/
│   │   ├── api/
│   │   │   ├── query/       # Main RAG endpoint (Groq)
│   │   │   ├── status/      # Service status dashboard
│   │   │   └── health/      # Health check
│   │   ├── components/
│   │   │   ├── icons.tsx    # Icon components
│   │   │   └── StatusPanel.tsx # API status UI
│   │   ├── page.tsx         # Main UI
│   │   └── layout.tsx       # Layout & metadata
│   ├── lib/                 # Utilities
│   │   ├── pinecone.ts     # Vector DB client
│   │   ├── embeddings.ts   # HuggingFace embeddings
│   │   └── groq.ts         # Groq LLM client
│   └── package.json
└── README.md               # You are here
```

## 🔑 Environment Variables

### Frontend (`frontend/.env.local`)

```bash
PINECONE_API_KEY=your_pinecone_api_key
GROQ_API_KEY=your_groq_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key

# Optional: specify custom index name (default: quarkquery)
# PINECONE_INDEX=quarkquery
```

### Ingestion (`ingestion/.env`)

```bash
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=physics-rag  # Optional: defaults to "physics-rag" if not set
```

**Where to get API keys (all FREE):**

- **Pinecone**: https://app.pinecone.io/ → API Keys
- **Groq**: https://console.groq.com/ → API Keys
- **HuggingFace**: https://huggingface.co/settings/tokens → New Token (Read access)

## 📊 Architecture

```
User Question
    ↓
[Frontend] Next.js UI
    ↓
[API Route] /api/query
    ↓
[1] Generate embedding (HuggingFace)
    ↓
[2] Search vectors (Pinecone)
    ↓
[3] Retrieve top 5 chunks
    ↓
[4] Enrich prompt with context
    ↓
[5] Generate answer (Groq/Llama)
    ↓
Answer + Citations
```

## 🧪 API Endpoints

### Main Query Endpoint

```bash
POST /api/query
Content-Type: application/json

{
  "question": "What is string theory?"
}
```

### Status Dashboard

```bash
GET /api/status
```

Returns health status and rate limits for all services (Pinecone, Groq, HuggingFace).

### Health Check

```bash
GET /api/health
```

## 📝 License

MIT

## 🙏 Acknowledgments

- Physics papers from arXiv.org
- Embeddings via sentence-transformers
- LLM inference via Groq
- Built with Next.js, Tailwind CSS, and Pinecone

---
