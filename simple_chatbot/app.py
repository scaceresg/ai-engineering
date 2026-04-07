import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

st.title("Simple Chatbot")

model = ChatOpenAI(model="gpt-5.4-mini")
