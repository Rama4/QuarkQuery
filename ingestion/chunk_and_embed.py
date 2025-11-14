"""
Chunking and Embedding Script for Physics Papers
Chunks extracted text and generates embeddings for vector database
"""

import json
import os
import threading
from pathlib import Path
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import numpy as np

# Directory and file paths
OUTPUT_DIR = 'extracted_data'
ALL_PAPERS_FILE = "all_papers.json"
CHUNKS_WITH_EMBEDDINGS_FILE = "chunks_with_embeddings.json"
EMBEDDING_SUMMARY_FILE = "embedding_summary.json"

# Embedding model configuration
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Chunking configuration
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 100
MIN_CHUNK_LENGTH = 50

# Embedding generation configuration
DEFAULT_BATCH_SIZE = 128  # Increased for faster processing (adjust based on available memory)
MAX_BATCH_SIZE = 512  # Maximum batch size for very large memory systems

# Parallelization configuration
DEFAULT_CPU_COUNT = 4
WORKER_MULTIPLIER = 2

class TextChunker:
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        extracted_data_dir: str = "",
        max_workers: int = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.extracted_data_dir = Path(extracted_data_dir)
        # Thread-safe lock for progress updates
        self.print_lock = threading.Lock()
        # Determine number of workers
        if max_workers is None:
            self.max_workers = min((os.cpu_count() or DEFAULT_CPU_COUNT) * WORKER_MULTIPLIER, 32)
        else:
            self.max_workers = max_workers
        
    def chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Split text into overlapping chunks with metadata
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            
            if len(chunk_text.strip()) > MIN_CHUNK_LENGTH:  # Skip very small chunks
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        **metadata,
                        "chunk_index": len(chunks),
                        "start_word": i,
                        "end_word": i + len(chunk_words)
                    }
                })
        
        return chunks
    
    def process_paper(self, paper_data: Dict) -> List[Dict]:
        """
        Process a single paper and create chunks with metadata
        """
        arxiv_id = paper_data["arxiv_id"]
        full_text = paper_data["full_text"]
        
        base_metadata = {
            "arxiv_id": arxiv_id,
            "filename": paper_data["filename"],
            "num_pages": paper_data["num_pages"],
            "title": paper_data.get("metadata", {}).get("title", "Unknown")
        }
        
        # Create chunks for the full paper
        chunks = self.chunk_text(full_text, base_metadata)
        
        return chunks
    
    def process_all_papers(self) -> List[Dict]:
        """
        Process all papers and return all chunks using parallel processing
        """
        all_papers_file = self.extracted_data_dir / ALL_PAPERS_FILE
        
        with open(all_papers_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        
        print(f"Processing {len(papers)} papers...")
        print(f"Using {self.max_workers} parallel workers")
        print()
        
        all_chunks = []
        completed_count = 0
        total_count = len(papers)
        
        # Process papers in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all chunking tasks
            future_to_paper = {
                executor.submit(self.process_paper, paper): paper
                for paper in papers
            }
            
            # Process completed chunking as they finish
            with tqdm(total=total_count, desc="Chunking papers") as pbar:
                for future in as_completed(future_to_paper):
                    paper = future_to_paper[future]
                    try:
                        chunks = future.result()
                        all_chunks.extend(chunks)
                        
                        with self.print_lock:
                            completed_count += 1
                            pbar.set_postfix_str(f"{completed_count}/{total_count} papers, {len(all_chunks)} chunks")
                        
                        pbar.update(1)
                        
                    except Exception as e:
                        with self.print_lock:
                            print(f"  ✗ Error processing paper {paper.get('arxiv_id', 'unknown')}: {str(e)}")
                        pbar.update(1)
        
        print(f"\nCreated {len(all_chunks)} chunks from {len(papers)} papers")
        return all_chunks


class EmbeddingGenerator:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME, device: str = None):
        """
        Initialize embedding model
        all-MiniLM-L6-v2: Fast, 384 dimensions, good for semantic search
        
        Args:
            model_name: Name of the sentence transformer model
            device: Device to use ('cuda', 'cpu', or None for auto-detection)
        """
        print(f"Loading embedding model: {model_name}")
        
        # Auto-detect device if not specified
        if device is None:
            try:
                import torch
                if torch.cuda.is_available():
                    device = 'cuda'
                    print("✓ CUDA GPU detected and available!")
                else:
                    device = 'cpu'
                    # Check if PyTorch is CPU-only version
                    if '+cpu' in torch.__version__:
                        print("⚠ PyTorch CPU-only version detected (no CUDA support)")
                        print("  To use GPU, install PyTorch with CUDA:")
                        print("  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
            except ImportError:
                device = 'cpu'
                print("⚠ PyTorch not found, using CPU")
        
        self.device = device
        self.model = SentenceTransformer(model_name, device=device)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        print(f"Model loaded! Embedding dimension: {self.embedding_dim}")
        print(f"Using device: {device.upper()}")
        
        if device == 'cuda':
            try:
                import torch
                print(f"GPU: {torch.cuda.get_device_name(0)}")
                print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
            except (ImportError, AttributeError):
                pass
    
    def generate_embeddings(self, chunks: List[Dict], batch_size: int = None) -> List[Dict]:
        """
        Generate embeddings for all chunks with optimized batch processing
        
        Args:
            chunks: List of chunk dictionaries with 'text' field
            batch_size: Batch size for processing (auto-adjusted if None)
        """
        texts = [chunk["text"] for chunk in chunks]
        
        # Auto-adjust batch size based on device and data size
        if batch_size is None:
            if self.device == 'cuda':
                # Larger batches for GPU
                batch_size = min(DEFAULT_BATCH_SIZE * 2, MAX_BATCH_SIZE)
            else:
                # For CPU, use larger batch size if we have enough chunks
                # This helps with CPU efficiency
                if len(texts) > 1000:
                    batch_size = min(DEFAULT_BATCH_SIZE * 2, 256)  # Up to 256 for CPU
                else:
                    batch_size = DEFAULT_BATCH_SIZE
        
        print(f"Generating embeddings for {len(texts)} chunks...")
        print(f"Batch size: {batch_size}")
        
        # Generate embeddings with optimized settings
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=False  # Slightly faster, normalize only if needed
        )
        
        # Efficiently add embeddings to chunks (vectorized conversion)
        print("Adding embeddings to chunks...")
        embeddings_list = embeddings.tolist()
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings_list[i]
        
        return chunks


def save_chunks_with_embeddings(chunks: List[Dict], output_directory: str = "", output_file: str = CHUNKS_WITH_EMBEDDINGS_FILE):
    """
    Save chunks with embeddings to JSON file
    """
    output_path = Path(output_directory) / output_file
    
    print(f"Saving {len(chunks)} chunks to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved to {output_path}")
    
    # Also save a summary
    summary = {
        "total_chunks": len(chunks),
        "embedding_dimension": len(chunks[0]["embedding"]) if chunks else 0,
        "papers": list(set(chunk["metadata"]["arxiv_id"] for chunk in chunks)),
        "avg_chunk_length": np.mean([len(chunk["text"]) for chunk in chunks]),
        "total_characters": sum(len(chunk["text"]) for chunk in chunks)
    }
    
    summary_path = Path(output_directory) / EMBEDDING_SUMMARY_FILE
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Summary saved to {summary_path}")
    return summary


def main():
    print("=" * 80)
    print("Chunking and Embedding Pipeline")
    print("=" * 80)
    print()
    
    # Step 1: Chunk the text
    chunker = TextChunker(
        chunk_size=DEFAULT_CHUNK_SIZE,
        chunk_overlap=DEFAULT_CHUNK_OVERLAP,
        extracted_data_dir=OUTPUT_DIR
    )
    chunks = chunker.process_all_papers()
    
    print()
    
    # Step 2: Generate embeddings
    embedder = EmbeddingGenerator()
    chunks_with_embeddings = embedder.generate_embeddings(chunks)
    
    print()
    
    # Step 3: Save results
    summary = save_chunks_with_embeddings(chunks=chunks_with_embeddings, output_directory=OUTPUT_DIR)
    
    print()
    print("=" * 80)
    print("Summary:")
    print(f"  Total chunks: {summary['total_chunks']}")
    print(f"  Embedding dimension: {summary['embedding_dimension']}")
    print(f"  Papers processed: {len(summary['papers'])}")
    print(f"  Average chunk length: {summary['avg_chunk_length']:.0f} characters")
    print(f"  Total characters: {summary['total_characters']:,}")
    print()
    print("Next: Upload to Pinecone vector database")
    print("=" * 80)


if __name__ == "__main__":
    main()

