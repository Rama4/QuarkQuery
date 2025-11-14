"""
Upload embeddings to Pinecone Vector Database
"""

import json
import os
from pathlib import Path
from typing import List, Dict
from pinecone import Pinecone, ServerlessSpec
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PineconeUploader:
    def __init__(self, index_name: str = "physics-rag"):
        """
        Initialize Pinecone client and create/connect to index
        """
        # Get API key from environment
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError(
                "PINECONE_API_KEY not found in environment variables.\n"
                "Please create a .env file with: PINECONE_API_KEY=your_key_here"
            )
        
        print("Initializing Pinecone...")
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.index = None
        
    def create_index(self, dimension: int = 384, metric: str = "cosine"):
        """
        Create Pinecone index if it doesn't exist
        """
        print(f"Checking if index '{self.index_name}' exists...")
        
        # Check if index already exists
        existing_indexes = self.pc.list_indexes()
        index_names = [idx.name for idx in existing_indexes]
        
        if self.index_name not in index_names:
            print(f"Creating new index '{self.index_name}'...")
            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            print(f"✓ Index '{self.index_name}' created successfully!")
        else:
            print(f"✓ Index '{self.index_name}' already exists")
        
        # Connect to the index
        self.index = self.pc.Index(self.index_name)
        
        # Get index stats
        stats = self.index.describe_index_stats()
        print(f"Index stats: {stats}")
    
    def prepare_vectors(self, chunks: List[Dict]) -> List[tuple]:
        """
        Prepare vectors in Pinecone format
        Format: (id, embedding, metadata)
        """
        vectors = []
        
        for i, chunk in enumerate(chunks):
            vector_id = f"{chunk['metadata']['arxiv_id']}_chunk_{i}"
            embedding = chunk["embedding"]
            
            # Prepare metadata (Pinecone has size limits, so be selective)
            metadata = {
                "text": chunk["text"][:1000],  # Limit text size
                "arxiv_id": chunk["metadata"]["arxiv_id"],
                "filename": chunk["metadata"]["filename"],
                "title": chunk["metadata"]["title"][:200],  # Limit title size
                "chunk_index": chunk["metadata"]["chunk_index"],
                "num_pages": chunk["metadata"]["num_pages"]
            }
            
            vectors.append((vector_id, embedding, metadata))
        
        return vectors
    
    def upload_vectors(self, vectors: List[tuple], batch_size: int = 100):
        """
        Upload vectors to Pinecone in batches
        """
        print(f"Uploading {len(vectors)} vectors to Pinecone...")
        
        # Upload in batches
        for i in tqdm(range(0, len(vectors), batch_size)):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
        
        print(f"✓ Successfully uploaded {len(vectors)} vectors!")
        
        # Get final stats
        stats = self.index.describe_index_stats()
        print(f"Final index stats: {stats}")
    
    def test_query(self, query_text: str = "What is the AdS/CFT correspondence?"):
        """
        Test query to verify the index is working
        """
        from sentence_transformers import SentenceTransformer
        
        print(f"\nTesting query: '{query_text}'")
        
        # Generate embedding for query
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        query_embedding = model.encode(query_text).tolist()
        
        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=3,
            include_metadata=True
        )
        
        print(f"\nTop {len(results['matches'])} results:")
        for i, match in enumerate(results['matches'], 1):
            print(f"\n{i}. Score: {match['score']:.4f}")
            print(f"   Paper: {match['metadata']['arxiv_id']}")
            print(f"   Title: {match['metadata']['title']}")
            print(f"   Text preview: {match['metadata']['text'][:200]}...")


def main():
    print("=" * 80)
    print("Pinecone Upload Pipeline")
    print("=" * 80)
    print()
    
    # Load chunks with embeddings
    chunks_file = Path("extracted_data") / "chunks_with_embeddings.json"
    
    if not chunks_file.exists():
        print(f"Error: {chunks_file} not found!")
        print("Please run chunk_and_embed.py first.")
        return
    
    print(f"Loading chunks from {chunks_file}...")
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"Loaded {len(chunks)} chunks")
    
    # Get embedding dimension
    embedding_dim = len(chunks[0]["embedding"])
    print(f"Embedding dimension: {embedding_dim}")
    
    print()
    
    # Initialize Pinecone
    uploader = PineconeUploader(index_name="physics-rag")
    
    # Create index
    uploader.create_index(dimension=embedding_dim)
    
    print()
    
    # Prepare vectors
    vectors = uploader.prepare_vectors(chunks)
    
    print()
    
    # Upload to Pinecone
    uploader.upload_vectors(vectors)
    
    print()
    
    # Test query
    uploader.test_query("What is the AdS/CFT correspondence?")
    
    print()
    print("=" * 80)
    print("✓ Upload complete! Your vector database is ready.")
    print("=" * 80)


if __name__ == "__main__":
    main()

