"""
Chunking and Embedding Script for Physics Papers
Chunks extracted text and generates embeddings for vector database
"""

import json
import os
from pathlib import Path
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import numpy as np


class TextChunker:
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        extracted_data_dir: str = "extracted_data"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.extracted_data_dir = Path(extracted_data_dir)
        
    def chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Split text into overlapping chunks with metadata
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            
            if len(chunk_text.strip()) > 50:  # Skip very small chunks
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
        Process all papers and return all chunks
        """
        all_papers_file = self.extracted_data_dir / "all_papers.json"
        
        with open(all_papers_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        
        all_chunks = []
        
        print(f"Processing {len(papers)} papers...")
        for paper in tqdm(papers):
            chunks = self.process_paper(paper)
            all_chunks.extend(chunks)
        
        print(f"Created {len(all_chunks)} chunks from {len(papers)} papers")
        return all_chunks


class EmbeddingGenerator:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding model
        all-MiniLM-L6-v2: Fast, 384 dimensions, good for semantic search
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"Model loaded! Embedding dimension: {self.embedding_dim}")
    
    def generate_embeddings(self, chunks: List[Dict], batch_size: int = 32) -> List[Dict]:
        """
        Generate embeddings for all chunks
        """
        texts = [chunk["text"] for chunk in chunks]
        
        print(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Add embeddings to chunks
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i].tolist()
        
        return chunks


def save_chunks_with_embeddings(chunks: List[Dict], output_file: str = "chunks_with_embeddings.json"):
    """
    Save chunks with embeddings to JSON file
    """
    output_path = Path("extracted_data") / output_file
    
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
    
    summary_path = Path("extracted_data") / "embedding_summary.json"
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
    chunker = TextChunker(chunk_size=500, chunk_overlap=100)
    chunks = chunker.process_all_papers()
    
    print()
    
    # Step 2: Generate embeddings
    embedder = EmbeddingGenerator()
    chunks_with_embeddings = embedder.generate_embeddings(chunks)
    
    print()
    
    # Step 3: Save results
    summary = save_chunks_with_embeddings(chunks_with_embeddings)
    
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

