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

# Environment variable names
ENV_PINECONE_API_KEY = "PINECONE_API_KEY"
ENV_PINECONE_INDEX = "PINECONE_INDEX"

# Configuration constants
DEFAULT_INDEX_NAME = "physics-rag"  # Default index name if not set in env
PINECONE_INDEX_NAME = os.getenv(ENV_PINECONE_INDEX) or DEFAULT_INDEX_NAME
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_EMBEDDING_DIMENSION = 384
DEFAULT_METRIC = "cosine"
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"
DEFAULT_BATCH_SIZE = 100
DEFAULT_TOP_K = 3
TEXT_METADATA_LIMIT = 1000
TITLE_METADATA_LIMIT = 200

# File paths
EXTRACTED_DATA_DIR = "extracted_data"
CHUNKS_WITH_EMBEDDINGS_FILE = "chunks_with_embeddings.json"

class PineconeUploader:
    def __init__(self, index_name: str = None):
        """
        Initialize Pinecone client and create/connect to index
        
        Args:
            index_name: Name of the Pinecone index (defaults to PINECONE_INDEX env var or DEFAULT_INDEX_NAME)
        """            
        # Get API key from environment
        api_key = os.getenv(ENV_PINECONE_API_KEY)
        if not api_key:
            raise ValueError(
                f"{ENV_PINECONE_API_KEY} not found in environment variables.\n"
                f"Please create a .env file with: {ENV_PINECONE_API_KEY}=your_key_here"
            )
        
        # Use provided index_name, or fall back to env var, or use default
        if index_name is None:
            index_name = os.getenv(ENV_PINECONE_INDEX) or DEFAULT_INDEX_NAME
        
        if not index_name or index_name.strip() == "":
            raise ValueError(
                f"{ENV_PINECONE_INDEX} not found in environment variables.\n"
                f"Please set it in your .env file: {ENV_PINECONE_INDEX}=your_index_name\n"
                f"Or it will default to: {DEFAULT_INDEX_NAME}"
            )
        
        print("Initializing Pinecone...")
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name.strip()
        self.index = None
        
    def create_index(self, dimension: int = DEFAULT_EMBEDDING_DIMENSION, metric: str = DEFAULT_METRIC):
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
                    cloud=PINECONE_CLOUD,
                    region=PINECONE_REGION
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
                "text": chunk["text"][:TEXT_METADATA_LIMIT],  # Limit text size
                "arxiv_id": chunk["metadata"]["arxiv_id"],
                "filename": chunk["metadata"]["filename"],
                "title": chunk["metadata"]["title"][:TITLE_METADATA_LIMIT],  # Limit title size
                "chunk_index": chunk["metadata"]["chunk_index"],
                "num_pages": chunk["metadata"]["num_pages"]
            }
            
            vectors.append((vector_id, embedding, metadata))
        
        return vectors
    
    def upload_vectors(self, vectors: List[tuple], batch_size: int = DEFAULT_BATCH_SIZE):
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
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        query_embedding = model.encode(query_text).tolist()
        
        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=DEFAULT_TOP_K,
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
    chunks_file = Path(EXTRACTED_DATA_DIR) / CHUNKS_WITH_EMBEDDINGS_FILE
    
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
    # Use environment variable or default index name
    index_name = os.getenv(ENV_PINECONE_INDEX) or DEFAULT_INDEX_NAME
    
    if index_name == DEFAULT_INDEX_NAME and not os.getenv(ENV_PINECONE_INDEX):
        print(f"⚠ Using default index name: '{index_name}'")
        print(f"  To use a custom name, set {ENV_PINECONE_INDEX} in your .env file")
        print()
    
    uploader = PineconeUploader(index_name=index_name)
    
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

