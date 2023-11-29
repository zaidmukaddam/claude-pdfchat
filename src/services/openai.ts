import OpenAI from "openai";

// This file contains utility functions for interacting with the OpenAI API

if (!process.env.OPENAI_API_KEY) {
  throw new Error("Missing OPENAI_API_KEY environment variable");
}

export const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

type EmbeddingOptions = {
  input: string | string[];
  model?: string;
};

export async function embedding({
  input,
  model = "text-embedding-ada-002",
}: EmbeddingOptions): Promise<number[][]> {
  const result = await openai.embeddings.create({
    model,
    input,
  });

  if (!result.data[0].embedding) {
    throw new Error("No embedding returned from the completions endpoint");
  }

  // Otherwise, return the embeddings
  return result.data.map((d) => d.embedding);
}
