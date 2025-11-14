import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET() {
  const checks = {
    pinecone: !!process.env.PINECONE_API_KEY,
    groq: !!process.env.GROQ_API_KEY,
    huggingface: !!process.env.HUGGINGFACE_API_KEY,
  };
  
  const allHealthy = Object.values(checks).every(Boolean);
  
  return NextResponse.json({
    status: allHealthy ? 'healthy' : 'degraded',
    checks,
    timestamp: new Date().toISOString(),
  });
}

