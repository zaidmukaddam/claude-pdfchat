import Anthropic, { AI_PROMPT, HUMAN_PROMPT } from "@anthropic-ai/sdk";
import { FileChunk } from "../../types/file";
import { AnthropicStream, StreamingTextResponse } from "ai";

type Data = {
  answer?: string;
  error?: string;
};

export const runtime = 'edge'

const MAX_FILES_LENGTH = 2000 * 3;

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const handler = async (req: Request): Promise<Response> => {
  const body = await req.json();
  const { question, fileChunks } = body as unknown as {
    question: string;
    fileChunks: FileChunk[];
  };

  console.log("Question: ", question);
  console.log("File chunks: ", fileChunks);

  try {
    const filesString = fileChunks
      .map((fileChunk) => `###\n\"${fileChunk.filename}\"\n${fileChunk.text}`)
      .join("\n")
      .slice(0, MAX_FILES_LENGTH);

    console.log(filesString);

    const prompt = HUMAN_PROMPT +
      `Given a question, try to answer it using the content of the file extracts below, and if you cannot answer, or find a relevant file, just output \"I couldn't find the answer to that question in your files.\".\n\n` +
      `If the answer is not contained in the files or if there are no file extracts, respond with \"I couldn't find the answer to that question in your files.\" If the question is not actually a question, respond with \"That's not a valid question.\" YOU DO NOT HAVE TO SAY ANYTHING ELSE OR QUESTION ON YOUR OWN AT ALL COSTS!\n\n` +
      `In the cases where you can find the answer, first give the answer. Then explain how you found the answer from the source or sources, and use the exact filenames of the source files you mention. Do not make up the names of any other files other than those mentioned in the files context. Give the answer in markdown format.` +
      `Use the following format:\n\nQuestion: <question>\n\nFiles:\n<###\n\"filename 1\"\nfile text>\n<###\n\"filename 2\"\nfile text>...\n\nAnswer: <answer or "I couldn't find the answer to that question in your files" or "That's not a valid question.">\n\n` +
      `Question: ${question}\n\n` +
      `Files:\n${filesString}\n\n` +
      AI_PROMPT + `Answer:`;

    const result = await anthropic.completions.create(
      {
        prompt,
        max_tokens_to_sample: 300,
        temperature: 0,
        model: "claude-2.1",
        stream: true,
      },
    );

    const stream = AnthropicStream(result)

    return new StreamingTextResponse(stream)
  } catch (error) {
    console.error(error);
    console.error({ error: "Something went wrong" });
    return new Response(
      JSON.stringify(
        { error: "Something went wrong" }
      ),
      { status: 500, }
    );
  }
}

export default handler;