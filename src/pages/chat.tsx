import Head from "next/head";
import { useState } from "react";

import FileQandAArea from "../components/FileQandAArea";

import { FileLite } from "../types/file";
import FileUploadArea from "../components/FileUploadArea";

export default function FileQandA() {
  const [files, setFiles] = useState<FileLite[]>([]);

  return (
    <div className="flex items-left text-left h-100 flex-col">
      <Head>
        <title>PDFChat | Get Instant Answers to Your Questions on Any PDF File</title>
      </Head>
      <div className="max-w-3xl mx-auto my-16 space-y-8 text-gray-800">

        <h1 className="text-4xl">Get Quick and Accurate Answers to Your Questions</h1>

        <div className="">
          Upload your files and find answers to your questions quickly and easily. Our powerful AI technology, 
          including OpenAI embeddings and Anthropic's Claude-2.1, searches the content within your documents to provide accurate and relevant answers.
        </div>

        <FileUploadArea
          handleSetFiles={setFiles}
          maxNumFiles={75}
          maxFileSizeMB={70}
        /> 

        <FileQandAArea files={files} />
      </div>
    </div>
  );
}
