import os

import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval  # type: ignore[import-untyped]

from interviewer_chatbot.services.chat_service import ChatService
from interviewer_chatbot.services.feedback_service import FeedbackService
from interviewer_chatbot.utils.config import Config
from interviewer_chatbot.utils.secrets import load_secrets

environment = os.environ.get("APP_ENV", "local")
load_secrets(environment)
config = Config(environment=environment).env_vars

user_messages_count: int = config.get("user-messages-count", 3)
prompts: dict = config.get("prompts", {})


@st.cache_resource
def get_services() -> tuple[ChatService, FeedbackService]:
    llm_models: dict = config.get("llm-models", {})
    client = OpenAI()
    return (
        ChatService(client, llm_models.get("chatbot", {})),
        FeedbackService(client, llm_models.get("feedback", {})),
    )


chat_service, feedback_service = get_services()

st.set_page_config(page_title="Interviewer Chatbot", page_icon=":robot:")
st.title("Interviewer Chatbot  :robot:")

# Setup state variables
if "setup_completed" not in st.session_state:
    st.session_state.setup_completed = False

if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_completed" not in st.session_state:
    st.session_state.chat_completed = False

if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False


# Setup state functions
def complete_setup():
    st.session_state.setup_completed = True


def show_feedback():
    st.session_state.feedback_shown = True


# If setup is not completed, show the setup form
if not st.session_state.setup_completed:
    st.write("This is a simple interviewer chatbot that helps you prepare for an interview for a given position.")
    st.write(
        "* First, you need to setup the interviewer chatbot by providing your information and the desired position."
    )
    st.write("* Then, the interviewer chatbot will ask you questions related to the desired position and your skills.")
    st.write(
        "* Once the interview is completed, the interviewer chatbot will then provide feedback on your performance."
    )

    # Candidate Information section
    st.subheader("Candidate Information", divider="gray")

    if "name" not in st.session_state:
        st.session_state.name = ""
    if "experience" not in st.session_state:
        st.session_state.experience = ""
    if "skills" not in st.session_state:
        st.session_state.skills = ""

    st.session_state.name = st.text_input(
        label="Candidate Name:",
        max_chars=20,
        placeholder="Enter your name",
        value=st.session_state.name,
    )
    st.session_state.experience = st.text_area(
        label="Candidate Experience:",
        height=None,
        max_chars=200,
        placeholder="Enter your experience",
        value=st.session_state.experience,
    )
    st.session_state.skills = st.text_area(
        label="Candidate Skills:",
        height=None,
        max_chars=200,
        placeholder="Enter your skills",
        value=st.session_state.skills,
    )

    # Job Information section (2 cols)
    st.subheader("Job Information", divider="gray")

    if "level" not in st.session_state:
        st.session_state.level = "Junior"
    if "position" not in st.session_state:
        st.session_state.position = "Data Analyst"
    if "company" not in st.session_state:
        st.session_state.company = "Google"

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.level = st.radio(
            "Choose evaluation level:",
            key="visibility",
            options=["Junior", "Mid-Level", "Senior"],
        )
    with col2:
        st.session_state.position = st.selectbox(
            "Choose job position:",
            ("Data Analyst", "Data Scientist", "Data Engineer", "ML Engineer", "AI Engineer"),
        )

    st.session_state.company = st.selectbox(
        "Choose company:",
        ("Google", "Amazon", "Microsoft", "Apple", "Tesla", "Meta", "Nvidia"),
    )

    # Complete setup
    if st.button("Start Interview", on_click=complete_setup, type="primary"):
        st.write("Setup completed! Starting interview...")

# If setup is completed and feedback is not shown and chat is not completed, show the interviewer chatbot
if st.session_state.setup_completed and not st.session_state.feedback_shown and not st.session_state.chat_completed:
    st.info(
        """
        Start by introducing yourself!
        """,
        icon="👋",
    )

    # Initialize chat history
    if not st.session_state.messages:
        st.session_state.messages = [
            {
                "role": "system",
                "content": prompts.get("chatbot", "").format(
                    name=st.session_state.name,
                    experience=st.session_state.experience,
                    skills=st.session_state.skills,
                    level=st.session_state.level,
                    position=st.session_state.position,
                    company=st.session_state.company,
                ),
            },
        ]

    # Display chat history (except system messages)
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # If user message count is less, handle user input
    if st.session_state.user_message_count < user_messages_count:
        if prompt := st.chat_input("Enter a message", max_chars=500):
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            if st.session_state.user_message_count < user_messages_count - 1:
                with st.chat_message("assistant"):
                    response = st.write_stream(chat_service.stream_response(st.session_state.messages))
                st.session_state.messages.append({"role": "assistant", "content": response})

            st.session_state.user_message_count += 1

    if st.session_state.user_message_count >= user_messages_count:
        st.session_state.chat_completed = True

# If chat is completed and feedback is not shown, show the feedback
if st.session_state.chat_completed and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback, type="primary"):
        st.write("Showing feedback...")

if st.session_state.feedback_shown:
    st.subheader("Feedback", divider="gray")

    if "feedback_content" not in st.session_state:
        conversation_history = "\n".join(
            [f"{message['role']}: {message['content']}" for message in st.session_state.messages]
        )
        with st.spinner("Generating feedback..."):
            st.session_state.feedback_content = feedback_service.generate_feedback(
                feedback_prompt=prompts.get("feedback", ""),
                conversation_history=conversation_history,
            )

    st.markdown(st.session_state.feedback_content)

    if st.button("Restart Interview", type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
