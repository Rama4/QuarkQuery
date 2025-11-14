import { HfInference } from "@huggingface/inference";

/**
 * Generate embeddings using HuggingFace Inference API
 * Uses the official @huggingface/inference client library
 * Reference: https://huggingface.co/docs/huggingface.js/inference/README
 */

export async function generateEmbedding(text: string): Promise<number[]> {
  const hfToken = process.env.HUGGINGFACE_API_KEY;

  if (!hfToken) {
    throw new Error(
      "HUGGINGFACE_API_KEY is not set. " +
        "Get a free key from https://huggingface.co/settings/tokens"
    );
  }

  const hf = new HfInference(hfToken);

  try {
    // Use feature extraction - same model as ingestion pipeline (384 dimensions)
    const result = await hf.featureExtraction({
      model: "sentence-transformers/all-MiniLM-L6-v2",
      inputs: text,
    });

    // The result should be a number array
    if (Array.isArray(result)) {
      return result as number[];
    }

    throw new Error("Unexpected response format from HuggingFace API");
  } catch (error) {
    console.error("HuggingFace embedding error:", error);
    throw new Error(`Failed to generate embedding: ${error}`);
  }
}
