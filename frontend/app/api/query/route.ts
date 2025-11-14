import { NextRequest, NextResponse } from 'next/server';
import { getPineconeIndex } from '@/lib/pinecone';
import { generateEmbedding } from '@/lib/embeddings';
import { generateResponse } from '@/lib/groq';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

interface QueryResult {
  id: string;
  score: number;
  metadata: {
    text: string;
    arxiv_id: string;
    title: string;
    filename: string;
  };
}

export async function POST(request: NextRequest) {
  try {
    const { question } = await request.json();
    
    if (!question || typeof question !== 'string') {
      return NextResponse.json(
        { error: 'Invalid question provided' },
        { status: 400 }
      );
    }
    
    // Step 1: Generate embedding for the question
    console.log('Generating embedding for question...');
    const queryEmbedding = await generateEmbedding(question);
    
    // Step 2: Query Pinecone for similar chunks
    console.log('Querying Pinecone...');
    const index = await getPineconeIndex();
    const queryResponse = await index.query({
      vector: queryEmbedding,
      topK: 5,
      includeMetadata: true,
    });
    
    const matches = queryResponse.matches as unknown as QueryResult[];
    
    if (!matches || matches.length === 0) {
      return NextResponse.json({
        answer: "I couldn't find relevant information in the physics papers to answer your question.",
        sources: [],
      });
    }
    
    // Step 3: Prepare context from retrieved chunks
    const context = matches
      .map((match, idx) => {
        return `[Source ${idx + 1} - ${match.metadata.title} (${match.metadata.arxiv_id})]\n${match.metadata.text}`;
      })
      .join('\n\n---\n\n');
    
    // Step 4: Generate response using Groq
    console.log('Generating response with Groq...');
    const systemPrompt = `You are an expert physics assistant. Answer questions based on the provided context from physics research papers.
- Be precise and technical when appropriate
- Cite sources by their number [Source N]
- If the context doesn't contain enough information, say so
- Use mathematical notation when helpful`;
    
    const userPrompt = `Context from physics papers:\n\n${context}\n\n---\n\nQuestion: ${question}\n\nPlease provide a detailed answer based on the context above.`;
    
    const answer = await generateResponse([
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt },
    ]);
    
    // Prepare sources
    const sources = matches.map((match) => ({
      arxiv_id: match.metadata.arxiv_id,
      title: match.metadata.title,
      text: match.metadata.text.substring(0, 200) + '...',
      score: match.score,
    }));
    
    return NextResponse.json({
      answer,
      sources,
      question,
    });
    
  } catch (error) {
    console.error('Error in query route:', error);
    return NextResponse.json(
      { 
        error: 'Failed to process query',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

