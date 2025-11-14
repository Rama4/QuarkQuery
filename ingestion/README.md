# QuarkQuery - Data Ingestion Pipeline

This folder contains scripts to extract, chunk, embed, and upload physics papers to a vector database.

## 📋 Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
Create a `.env` file in this folder:
```bash
PINECONE_API_KEY=your_pinecone_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

Get free API keys:
- Pinecone: https://app.pinecone.io/ (Free: 100k vectors)
- Groq: https://console.groq.com/ (Free: 14,400 requests/day)

## 🚀 Usage

### Step 1: Extract text from PDFs
```bash
python extract_pdfs.py
```
Output: `extracted_data/` folder with JSON files

### Step 2: Chunk text and generate embeddings
```bash
python chunk_and_embed.py
```
Output: `extracted_data/chunks_with_embeddings.json`

### Step 3: Upload to Pinecone
```bash
python upload_to_pinecone.py
```
Output: Vectors uploaded to Pinecone index `physics-rag`

## 📊 What Gets Created

- **~2,500 chunks** from 11 physics papers
- **384-dimensional embeddings** using sentence-transformers
- **Metadata** including paper ID, title, page numbers
- **Pinecone index** ready for semantic search

## 🔧 Configuration

Edit parameters in the scripts:
- `chunk_size`: Default 500 words
- `chunk_overlap`: Default 100 words
- `embedding_model`: Default "all-MiniLM-L6-v2"
- `index_name`: Default "physics-rag"

## 📁 Output Structure

```
extracted_data/
├── all_papers.json              # All extracted papers
├── chunks_with_embeddings.json  # Chunked + embedded data
├── embedding_summary.json       # Statistics
└── extraction_report.txt        # PDF extraction report
```

