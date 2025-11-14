import { NextResponse } from 'next/server';
import { Pinecone } from '@pinecone-database/pinecone';
import { HfInference } from '@huggingface/inference';
import Groq from 'groq-sdk';

/**
 * API Status Endpoint
 * Returns usage information and limits for all integrated services
 */

export async function GET() {
  try {
    const status = {
      timestamp: new Date().toISOString(),
      services: {
        pinecone: await getPineconeStatus(),
        huggingface: await getHuggingFaceStatus(),
        groq: await getGroqStatus(),
      },
    };

    return NextResponse.json(status);
  } catch (error) {
    console.error('Error fetching status:', error);
    return NextResponse.json(
      { error: 'Failed to fetch status', details: String(error) },
      { status: 500 }
    );
  }
}

async function getPineconeStatus() {
  try {
    const apiKey = process.env.PINECONE_API_KEY;
    if (!apiKey) {
      return { status: 'not_configured', message: 'PINECONE_API_KEY not set' };
    }

    const pc = new Pinecone({ apiKey });
    const indexName = process.env.PINECONE_INDEX || 'quarkquery';
    
    // Get index stats
    const index = pc.index(indexName);
    const stats = await index.describeIndexStats();

    return {
      status: 'active',
      index: indexName,
      totalVectors: stats.totalRecordCount || 0,
      dimensions: stats.dimension || 384,
      namespaces: Object.keys(stats.namespaces || {}).length,
      message: 'Pinecone Free Tier: 1 index, 100K vectors max',
    };
  } catch (error) {
    return {
      status: 'error',
      message: String(error),
    };
  }
}

async function getHuggingFaceStatus() {
  try {
    const apiKey = process.env.HUGGINGFACE_API_KEY;
    if (!apiKey) {
      return { status: 'not_configured', message: 'HUGGINGFACE_API_KEY not set' };
    }

    // HuggingFace doesn't provide a direct usage API endpoint
    // But we can test if the token is valid
    const hf = new HfInference(apiKey);
    
    try {
      // Quick test call to verify token
      await hf.featureExtraction({
        model: 'sentence-transformers/all-MiniLM-L6-v2',
        inputs: 'test',
      });

      return {
        status: 'active',
        model: 'sentence-transformers/all-MiniLM-L6-v2',
        dimensions: 384,
        message: 'HuggingFace Free Tier: Rate-limited requests, model may need loading time',
        rateLimits: {
          note: 'Free tier has dynamic rate limits based on usage',
          typical: '~1000 requests/hour for embeddings',
        },
      };
    } catch (testError: any) {
      if (testError.message?.includes('rate limit')) {
        return {
          status: 'rate_limited',
          message: 'Currently rate-limited, try again in a few seconds',
        };
      }
      throw testError;
    }
  } catch (error: any) {
    return {
      status: 'error',
      message: error.message || String(error),
    };
  }
}

async function getGroqStatus() {
  try {
    const apiKey = process.env.GROQ_API_KEY;
    if (!apiKey) {
      return { status: 'not_configured', message: 'GROQ_API_KEY not set' };
    }

    const groq = new Groq({ apiKey });

    // Groq doesn't have a direct usage endpoint, but we can list available models
    try {
      const models = await groq.models.list();
      
      return {
        status: 'active',
        model: 'llama-3.3-70b-versatile',
        availableModels: models.data.map((m: any) => m.id).slice(0, 5),
        message: 'Groq Free Tier: 14,400 requests/day, 30 requests/min',
        rateLimits: {
          daily: '14,400 requests',
          perMinute: '30 requests',
          tokens: '6,000 tokens/min',
        },
      };
    } catch (testError: any) {
      if (testError.message?.includes('rate limit')) {
        return {
          status: 'rate_limited',
          message: 'Currently rate-limited, try again in a minute',
          rateLimits: {
            daily: '14,400 requests',
            perMinute: '30 requests',
          },
        };
      }
      throw testError;
    }
  } catch (error: any) {
    return {
      status: 'error',
      message: error.message || String(error),
    };
  }
}

