import time

import boto3
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import ConversationChain
from langchain.llms.bedrock import Bedrock
from langchain.memory import ConversationBufferMemory
from langchain.prompts.prompt import PromptTemplate



st.title("Chat with PDF with Claude on Bedrock")
st.markdown(
    "**Chat with Claude v2 on Bedrock. Get started by uploading a PDF!**"
    )

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
    
)


@st.cache_resource
def load_llm():
    llm = Bedrock(client=bedrock_runtime, model_id="anthropic.claude-v2")
    llm.model_kwargs = {"temperature": 0.7, "max_tokens_to_sample": 2048}

    DEFAULT_TEMPLATE = """{history}\n\nHuman: Answer in proper markdown format only. {input}\n\nAssistant:"""
    prompt = PromptTemplate(
        input_variables=["history", "input"],
        template=DEFAULT_TEMPLATE
    )

    model = ConversationChain(
        prompt=prompt,
        llm=llm,
        verbose=True,
        memory=ConversationBufferMemory(
            human_prefix="\n\nHuman: ",
            ai_prefix="\n\nAssistant:"
        )
    )

    return model


model = load_llm()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

pdf = st.file_uploader("Upload a PDF file", type=["pdf"])
pdf_text = None

if pdf is not None:
    pdf_reader = PdfReader(pdf)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()

    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text=text)

    # Chunk to one string
    pdf_text = ""
    for chunk in chunks:
        pdf_text += chunk + "\n\n"
 
if prompt := st.chat_input("What is up?", disabled=not pdf):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        processed_prompt = prompt
        if pdf is not None:
            processed_prompt = f"Here's some context:\n\n<article>{pdf_text}\n\n</article>\n\n{prompt}"

        result = model.predict(input=processed_prompt)

        for chunk in result:
            full_response += chunk
            time.sleep(0.005)
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(result)

    st.session_state.messages.append({"role": "assistant", "content": full_response})