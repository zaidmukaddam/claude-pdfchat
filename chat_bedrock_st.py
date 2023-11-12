import replicate
from openai import OpenAI
import base64
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from anthropic_bedrock import AnthropicBedrock, HUMAN_PROMPT, AI_PROMPT


client = AnthropicBedrock()
replicate_client = replicate.Client(
    api_token=st.secrets["REPLICATE_API_TOKEN"])

openai = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=0,
    )
    chunks = text_splitter.split_text(text)
    return chunks


with open("styles.css") as css:
    st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)


@st.cache(suppress_st_warning=True)
def process_pdfs(pdf_files):
    text = ""
    for pdf in pdf_files:
        pdf_reader = PdfReader(pdf)
        text += "".join(page.extract_text() or "" for page in pdf_reader.pages)
    return text


option = st.sidebar.radio("Choose an option:", [
                          'Chat', 'Chat with PDF', 'Chat with Llama2-70b-Chat', 'GPT-4V'])

if option == "Chat":
    st.title("Chat with Claude on Bedrock")
    st.markdown(
        "**Chat with Claude v2 on Bedrock. Get started by typing your query!**")
elif option == "Chat with PDF":
    st.title("ChatPDF with Claude on Bedrock")
    st.markdown(
        "**Chat with Claude v2 on Bedrock. Get started by uploading a PDF!**")
elif option == "Chat with Llama2-70b-Chat":
    st.title("Chat with Llama2-70b-Chat")
    st.markdown(
        "**Chat with Llama2-70b-Chat on Bedrock. Get started by typing your query!**")
elif option == "GPT-4V":
    st.title("GPT-4V")
    st.markdown(
        "**Chat with GPT-4V. Get started by typing your query!**")


pdf_docs = None
if 'doc' not in st.session_state:
    st.session_state['doc'] = ""

if option == "Chat with PDF":
    with st.sidebar:
        st.subheader('Your PDF documents')
        pdf_docs = st.file_uploader(
            "Upload your PDFs here and click on 'Process'", accept_multiple_files=True, type=['pdf'])

        if st.button('Process'):
            with st.spinner('Processing'):
                text = ""
                for pdf in pdf_docs:
                    pdf_reader = PdfReader(pdf)
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""

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
                # Corrected to count words instead of characters
                st.success(
                    f'Text chunks generated, total words: {len(st.session_state["doc"].split())}')

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def format_prompt_with_history(messages, new_user_message, include_pdf_content=False, pdf_content=""):
    """
    Formats a prompt including the conversation history, the new user message,
    and optionally the PDF content.
    """
    conversation_history = "\n".join(
        f"{HUMAN_PROMPT if m['role'] == 'user' else AI_PROMPT} {m['content']}"
        for m in messages
    )

    if include_pdf_content:
        pdf_content_section = f"This is PDF content:\n<pdf_content>{pdf_content}</pdf_content>\n\n"
    else:
        pdf_content_section = ""

    return f"{conversation_history}\n{HUMAN_PROMPT} {new_user_message} {AI_PROMPT}\n{pdf_content_section}"


def get_image_as_base64(image):
    # Read the file and encode it
    img_data = image.getvalue()
    base64_encoded_data = base64.b64encode(img_data)
    base64_message = base64_encoded_data.decode('utf-8')
    # Create the base64 URL
    return f"data:image/jpeg;base64,{base64_message}"


prompt_disabled = (option == "Chat with PDF" and st.session_state['doc'] == "")

if option == "GPT-4V":
    image = st.file_uploader("Upload an image", type=['png', 'jpg', 'jpeg'])
    if image:
        base64_url = get_image_as_base64(image)
        st.image(base64_url)

        user_message = st.chat_input("Enter your message:")
        user = st.empty()

        if user_message:
            # Append the user's text to the messages
            st.session_state.messages.append(
                {"role": "user", "content": user_message})
            user.markdown(user_message)
            message_placeholder = st.empty()
            full_response = ""

            # Start with the system message that sets the assistant's role
            openai_messages = [
                {"role": "system", "content": "You are a helpful assistant."}]

            # Append previous messages from the session history
            for message in st.session_state.messages:
                # Ensure messages containing images are formatted correctly
                if message.get("type") == "image":
                    openai_messages.append({"role": "user", "content": [
                                           {"type": "image_url", "image_url": message["content"]}]})
                else:
                    openai_messages.append(
                        {"role": "user", "content": message["content"]})

            # Include the current message and the image if it was uploaded in this turn
            if image:
                openai_messages.append({"role": "user", "content": [
                                       {"type": "image_url", "image_url": base64_url}, {"type": "text", "text": user_message}]})
            else:
                openai_messages.append(
                    {"role": "user", "content": user_message})

            print(len(openai_messages))

            # API call to GPT-4V with the full chat history
            stream = openai.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=openai_messages,
                max_tokens=2048,
                stream=True
            )

            for completion in stream:
                chunk = completion.choices[0].delta.content or ""
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")

            # Append the assistant's response to the messages
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response})
            message_placeholder.markdown(full_response)
elif prompt := st.chat_input("What is up?", disabled=prompt_disabled):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        if option == 'Chat':
            processed_prompt = format_prompt_with_history(
                messages=st.session_state.messages,
                new_user_message=prompt,
                include_pdf_content=(st.session_state['doc'] != ""),
                pdf_content=st.session_state['doc']
            )

            print(processed_prompt)

            # Using the anthropic_bedrock client to create a completion
            stream = client.completions.create(
                prompt=processed_prompt,
                max_tokens_to_sample=2048,
                model="anthropic.claude-v2",
                stream=True,
            )

            for completion in stream:
                chunk = completion.completion
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")

        elif option == "Chat with Llama2-70b-Chat":

            stream = replicate.run(
                "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",
                input={
                    "prompt": prompt,
                    "system_prompt": '''You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature. If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.''',
                    "max_new_tokens": 2048
                },
                stream=True
            )

            for completion in stream:
                chunk = completion
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")

        # Once done, display the final message
        message_placeholder.markdown(full_response)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response
        }
    )
