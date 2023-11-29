import React, { memo, useCallback, useRef, useState } from "react";
import { Transition } from "@headlessui/react";
import axios from "axios";
import ReactMarkdown from "react-markdown";

import FileViewerList from "./FileViewerList";
import LoadingText from "./LoadingText";
import { isFileNameInString } from "../services/utils";
import { FileChunk, FileLite } from "../types/file";

type FileQandAAreaProps = {
  files: FileLite[];
};

function FileQandAArea(props: FileQandAAreaProps) {
  const questionRef = useRef(null);
  const [hasAskedQuestion, setHasAskedQuestion] = useState(false);
  const [answerError, setAnswerError] = useState("");
  const [answerLoading, setAnswerLoading] = useState<boolean>(false);
  const [answer, setAnswer] = useState("");
  const [answerDone, setAnswerDone] = useState(false);

  const handleSearch = useCallback(async () => {
    if (answerLoading) {
      return;
    }

    const question = (questionRef?.current as any)?.value ?? "";
    setAnswer("");
    setAnswerDone(false);

    if (!question) {
      setAnswerError("Please ask a question.");
      return;
    }
    if (props.files.length === 0) {
      setAnswerError("Please upload files before asking a question.");
      return;
    }

    setAnswerLoading(true);
    setAnswerError("");

    let results = [];

    try {
      const searchResultsResponse = await axios.post(
        "/api/search-file-chunks",
        {
          searchQuery: question,
          files: props.files,
          maxResults: 10,
        }
      );

      console.log(searchResultsResponse);

      if (searchResultsResponse.status === 200) {
        results = searchResultsResponse.data.searchResults;
      } else {
        setAnswerError("Sorry, something went wrong!");
      }
    } catch (err: any) {
      setAnswerError("Sorry, something went wrong!");
    }

    setHasAskedQuestion(true);

    console.log("Question: ", question);
    console.log("File chunks: ", results);

    const res = await fetch("/api/get-answer-from-files", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
        fileChunks: results,
      }),
    });
    const reader = res.body!.getReader();

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        setAnswerDone(true);
        break;
      }
      setAnswer((prev) => prev + new TextDecoder().decode(value));
    }

    setAnswerLoading(false);
  }, [props.files, answerLoading]);

  const handleEnterInSearchBar = useCallback(
    async (event: React.SyntheticEvent) => {
      if ((event as any).key === "Enter") {
        await handleSearch();
      }
    },
    [handleSearch]
  );

  return (
    <div className="space-y-4 text-gray-800">
      <div className="mt-36">
        <h3>Starting asking questions after uploading your files:</h3>
      </div>
      <div className="flex justify-end items-center relative">
        <input
          className="border rounded border-gray-200 w-full py-3 px-2"
          name="search"
          autoFocus
          ref={questionRef}
          onKeyDown={handleEnterInSearchBar}
        />
        <div
          className="w-max rounded-md py-1 cursor-pointer absolute mx-3 mt-0.5"
          onClick={handleSearch}
        >
          {answerLoading ? (
            <LoadingText text="loading..." />
          ) : (
            <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" className="mr-1" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          )}
        </div>
      </div>
      <div className="sources-section">
        {answerError && <div className="text-red-500">{answerError}</div>}
        <Transition
          show={hasAskedQuestion}
          enter="transition duration-600 ease-out"
          enterFrom="transform opacity-0"
          enterTo="transform opacity-100"
          leave="transition duration-125 ease-out"
          leaveFrom="transform opacity-100"
          leaveTo="transform opacity-0"
          className="mb-8"
        >
          {answer && (
            <div className="">
              <ReactMarkdown className="prose" linkTarget="_blank">
                {`${answer}${answerDone ? "" : "  |"}`}
              </ReactMarkdown>
            </div>
          )}

          <Transition
            show={
              props.files.filter((file) =>
                isFileNameInString(file.name, answer)
              ).length > 0
            }
            enter="transition duration-600 ease-out"
            enterFrom="transform opacity-0"
            enterTo="transform opacity-100"
            leave="transition duration-125 ease-out"
            leaveFrom="transform opacity-100"
            leaveTo="transform opacity-0"
            className="mb-8"
          >
            <FileViewerList
              files={props.files.filter((file) =>
                isFileNameInString(file.name, answer)
              )}
              title="Sources"
              listExpanded={true}
            />
          </Transition>
        </Transition>
      </div>
    </div>
  );
}

export default memo(FileQandAArea);
