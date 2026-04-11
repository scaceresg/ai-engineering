# Interviewer Chatbot

A Streamlit chatbot that simulates a technical interview using two specialised LLM services: one for streaming conversational responses and one for generating structured feedback at the end of the session.

## Architecture

A single `OpenAI` client is created once per process (via `@st.cache_resource`) and shared by two stateless services, each configured with its own model parameters from `configs/environment.yaml`. All per-user conversation state lives in Streamlit's `session_state`.

```
                        ┌──────────────────────────────┐
                        │  configs/environment.yaml    │
                        └──────┬───────────┬───────────┘
                               │           │
                 llm-models.chatbot  llm-models.feedback
                               │           │
                               ▼           ▼
┌───────────┐         ┌──────────────┐  ┌──────────────────┐
│  OpenAI() │────────▶│ ChatService  │  │ FeedbackService  │
│  (shared) │────────▶│              │  │                  │
└───────────┘         └──────┬───────┘  └────────┬─────────┘
                             │                   │
                   stream_response()    generate_feedback()
                             │                   │
                             ▼                   ▼
                        ┌──────────────────────────────┐
                        │   app.py (Streamlit UI)      │
                        └──────────────┬───────────────┘
                                       │
                                 session_state
                                       │
                                       ▼
                                 ┌───────────┐
                                 │  Browser  │
                                 └───────────┘
```

## Features

- **Setup form** — capture candidate name, experience, skills, level, position and company before the interview starts.
- **Streaming interview** — the chatbot asks role-specific questions one at a time, streaming responses token by token.
- **Automated feedback** — after a configurable number of candidate answers, a second LLM evaluates the transcript and returns a scored, structured report.
- **Cloud Run-ready** — services are initialised once per container process via `@st.cache_resource`, and all per-user state is isolated in Streamlit's session state, making the app safe for concurrent access.

## Project structure

```
interviewer-chatbot/
├── configs/
│   ├── __init__.py
│   ├── environment.yaml          # base config: model params, prompts, settings
│   └── environment-dev.yaml      # dev overrides: GCP project-id and secret-name
├── interviewer_chatbot/
│   ├── app.py                    # Streamlit UI — no business logic
│   ├── services/
│   │   ├── chat_service.py       # OpenAI wrapper for streaming interview turns
│   │   └── feedback_service.py   # OpenAI wrapper for feedback generation
│   └── utils/
│       ├── config.py             # hierarchical YAML config loader
│       ├── logger.py             # coloured structured logging
│       └── secrets.py            # API key loading (.env locally, Secret Manager on GCP)
├── Dockerfile
├── Makefile
└── pyproject.toml
```

## Local development

```bash
# Install dependencies
make install

# Copy and populate the API key
touch .env   # set OPENAI_API_KEY

# Run the app
make run
```

The app reads `APP_ENV` from the environment (defaults to `local`), which makes `secrets.py` load the key from `.env`.

## Configuration

Model parameters and prompts live in `configs/environment.yaml`:

```yaml
user-messages-count: 3          # number of candidate turns before feedback is offered

llm-models:
  chatbot:
    model: gpt-4o-mini
    temperature: 0.5
    max_completion_tokens: 250
  feedback:
    model: gpt-4o
    temperature: 0.1
    max_completion_tokens: 500

prompts:
  chatbot: |-
    You are an HR executive that will interview {name} ...
  feedback: |-
    You are a helpful assistant that provides feedback ...
```

Environment-specific overrides (e.g. `environment-dev.yaml`) are merged on top of the base file by the `Config` class.

## Deployment to Cloud Run

The `Makefile` wraps the full build-push-deploy pipeline. Prerequisites:

1. The secret `ai-engineering-interviewer-chatbot-openai-api-key` must exist in GCP Secret Manager.
2. The service account `ai-engineering@scg-my-projects.iam.gserviceaccount.com` must have `roles/secretmanager.secretAccessor` on that secret.

Then build and deploy:

```bash
make docker-build
make docker-push
make deploy
```

`APP_ENV=dev` is baked into the image so the container automatically fetches the API key from Secret Manager on startup.
