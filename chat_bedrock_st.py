import time
import boto3
import streamlit as st
from PyPDF2 import PdfReader
from langchain.schema import Document
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.chains import ConversationChain
from langchain.llms.bedrock import Bedrock
from langchain.memory import ConversationBufferMemory
from langchain.prompts.prompt import PromptTemplate


def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=0,
    )
    chunks = text_splitter.split_text(text)
    return chunks


with open("styles.css") as css:
    st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)

option = st.sidebar.radio("Choose an option:", ['Chat', 'Chat with PDF'])

if option == "Chat":
    st.title("Chat with Claude on Bedrock")
    st.markdown(
        "**Chat with Claude v2 on Bedrock. Get started by typing your query!**")
else:
    st.title("ChatPDF with Claude on Bedrock")
    st.markdown(
        "**Chat with Claude v2 on Bedrock. Get started by uploading a PDF!**")

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
)


@st.cache_resource
def load_llm():
    llm = Bedrock(client=bedrock_runtime, model_id="anthropic.claude-v2")
    llm.model_kwargs = {"temperature": 0.7, "max_tokens_to_sample": 2048}

    DEFAULT_TEMPLATE = """{history}\n\nHuman: {input}\n\nAssistant:"""
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

pdf_docs = None
if 'doc' not in st.session_state:
    st.session_state['doc'] = ""

if option == "Chat with PDF":
    with st.sidebar:
        st.subheader('Your PDF documents')
        pdf_docs = st.file_uploader(
            "Upload your pdfs here and click on 'Process'", accept_multiple_files=True, type=['pdf'])

        if st.button('Process'):
            with st.spinner('Processing'):
                text = ""
                for pdf in pdf_docs:
                    pdf_reader = PdfReader(pdf)
                    for page in pdf_reader.pages:
                        text += page.extract_text()

                text_splitter = CharacterTextSplitter(
                    separator="\n",
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len
                )
                chunks = text_splitter.split_text(text=text)

                data = ""
                for chunk in chunks:
                    data += chunk

                st.success('PDFs extracted to data string')
                st.session_state['doc'] = data
                st.success(f'Text chunks generated, total words: {len(st.session_state["doc"])}')

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt_disabled = (option == "Chat with PDF" and st.session_state['doc'] == "")
if prompt := st.chat_input("What is up?", disabled=prompt_disabled):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        processed_prompt = prompt
        if st.session_state['doc'] != "":
            processed_prompt = f"Here's some context:\n\n<article>{st.session_state['doc']}\n\n</article>\n\n{prompt}"

        result = model.predict(input=processed_prompt)

        for chunk in result:
            full_response += chunk
            time.sleep(0.01)
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(result)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
