# QuarkQuery - Data Ingestion Pipeline

This folder contains scripts to download, extract, chunk, embed, and upload physics papers to a vector database.

## 📋 Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
Create a `.env` file in this folder:
```bash
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX=physics-rag  # Optional: defaults to "physics-rag"
```

Get free API keys:
- Pinecone: https://app.pinecone.io/ (Free: 100k vectors)

3. **GPU Support (Optional but Recommended):**
For faster embedding generation, install PyTorch with CUDA:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## 🚀 Usage

### Step 0: Download Papers
```bash
python download_papers.py --yes
```
- Downloads 100 papers from arXiv using parallel processing
- Reads from `pending_papers.json`
- Saves PDFs to `data/` directory
- Skips already downloaded files

### Step 1: Extract text from PDFs
```bash
python extract_pdfs.py
```
- **Parallel processing** - Uses multiple threads (CPU count × 2)
- Output: `extracted_data/` folder with JSON files
- Processes all PDFs in `data/` directory

### Step 2: Chunk text and generate embeddings
```bash
python chunk_and_embed.py
```
- **GPU-accelerated** if CUDA is available (10-50x faster)
- **Parallel chunking** - Processes papers in parallel
- **Optimized batch sizes** - Auto-adjusts for CPU/GPU
- Output: `extracted_data/chunks_with_embeddings.json`

### Step 3: Upload to Pinecone
```bash
python upload_to_pinecone.py
```
- Uploads vectors to Pinecone index (default: `physics-rag`)
- Batch uploads for efficiency
- Output: Vectors ready for semantic search

## 📊 What Gets Created

- **~4,000 chunks** from 100 physics papers
- **384-dimensional embeddings** using sentence-transformers/all-MiniLM-L6-v2
- **Metadata** including paper ID, title, page numbers, chunk index
- **Pinecone index** ready for semantic search

## 🔧 Configuration

### Download Script (`download_papers.py`)
- `DEFAULT_PAPERS_DIR`: "data" - Where PDFs are saved
- `DEFAULT_LIST_FILE`: "pending_papers.json" - Paper list file
- Parallel workers: CPU count × 2 (auto-detected)

### Extraction Script (`extract_pdfs.py`)
- `INPUT_DIR`: "data" - PDF source directory
- `OUTPUT_DIR`: "extracted_data" - JSON output directory
- Parallel workers: CPU count × 2 (auto-detected)

### Chunking & Embedding (`chunk_and_embed.py`)
- `DEFAULT_CHUNK_SIZE`: 500 words
- `DEFAULT_CHUNK_OVERLAP`: 100 words
- `DEFAULT_BATCH_SIZE`: 128 (CPU) / 256 (GPU)
- `EMBEDDING_MODEL_NAME`: "sentence-transformers/all-MiniLM-L6-v2"
- GPU auto-detection: Automatically uses CUDA if available

### Upload Script (`upload_to_pinecone.py`)
- `DEFAULT_INDEX_NAME`: "physics-rag"
- `DEFAULT_BATCH_SIZE`: 100 vectors per batch
- Can be overridden with `PINECONE_INDEX` env variable

## 📁 Output Structure

```
ingestion/
├── data/                        # Downloaded PDFs (100 papers)
│   ├── 9711200v3.pdf
│   ├── 9802109v2.pdf
│   └── ...
├── pending_papers.json          # List of papers with metadata
├── extracted_data/              # Generated JSON files
│   ├── all_papers.json          # All extracted papers
│   ├── chunks_with_embeddings.json  # Chunked + embedded data
│   ├── embedding_summary.json  # Statistics
│   ├── extraction_report.txt   # PDF extraction report
│   └── {arxiv_id}.json         # Individual paper JSON files
└── .env                         # Environment variables (create this)
```

## ⚡ Performance

- **Download**: ~2-5 minutes for 100 papers (parallel downloads)
- **Extraction**: ~1-2 minutes for 100 papers (parallel processing)
- **Chunking**: ~1 second for 100 papers (parallel processing)
- **Embedding (CPU)**: ~2-3 minutes for ~4,000 chunks
- **Embedding (GPU)**: ~30 seconds-1 minute for ~4,000 chunks
- **Upload**: ~1-2 minutes for ~4,000 vectors

