import { Pinecone } from '@pinecone-database/pinecone';

let pineconeClient: Pinecone | null = null;

export function getPineconeClient(): Pinecone {
  if (!pineconeClient) {
    const apiKey = process.env.PINECONE_API_KEY;
    
    if (!apiKey) {
      throw new Error('PINECONE_API_KEY is not set in environment variables');
    }
    
    pineconeClient = new Pinecone({
      apiKey,
    });
  }
  
  return pineconeClient;
}

export async function getPineconeIndex(indexName: string = 'physics-rag') {
  const client = getPineconeClient();
  return client.index(indexName);
}

