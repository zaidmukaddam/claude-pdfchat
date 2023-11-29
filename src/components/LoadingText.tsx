import React, { memo } from "react";

import LoadingSpinner from "./LoadingSpinner";

type LoadingTextProps = {
  text: string;
};

function LoadingText(props: LoadingTextProps) {
  return (
    <div className="text-gray-500 text-md flex flex-row justify-center items-end  ">
      <LoadingSpinner />
    </div>
  );
}

export default memo(LoadingText);
