FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY interviewer_chatbot/ interviewer_chatbot/
RUN uv sync --no-dev

COPY configs/ configs/
COPY .streamlit/ .streamlit/

ENV APP_ENV=dev
EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "interviewer_chatbot/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
