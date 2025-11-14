import Groq from 'groq-sdk';

let groqClient: Groq | null = null;

export function getGroqClient(): Groq {
  if (!groqClient) {
    const apiKey = process.env.GROQ_API_KEY;
    
    if (!apiKey) {
      throw new Error('GROQ_API_KEY is not set in environment variables');
    }
    
    groqClient = new Groq({
      apiKey,
    });
  }
  
  return groqClient;
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export async function generateResponse(
  messages: ChatMessage[],
  model: string = 'llama-3.3-70b-versatile'
): Promise<string> {
  const client = getGroqClient();
  
  try {
    const completion = await client.chat.completions.create({
      messages,
      model,
      temperature: 0.3,
      max_tokens: 2048,
      top_p: 1,
      stream: false,
    });
    
    return completion.choices[0]?.message?.content || 'No response generated';
  } catch (error) {
    console.error('Error generating response:', error);
    throw error;
  }
}

