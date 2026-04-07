PROJECT_ID ?= scg-my-projects
REGION ?= us-east1
REPOSITORY ?= scg-projects-repository
IMAGE_NAME ?= ai-engineering-simple-chatbot
IMAGE_TAG ?= latest
IMAGE_URI = $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPOSITORY)/$(IMAGE_NAME):$(IMAGE_TAG)

SERVICE_NAME ?= ai-engineering-simple-chatbot

.PHONY: venv install format lint typecheck audit run docker-build docker-push deploy

venv:
	uv venv

install:
	uv sync

format:
	uv run ruff format .
	uv run ruff check . --fix

lint:
	uv run ruff check .

typecheck:
	uv run mypy .

audit:
	uv run pip-audit

run:
	uv run streamlit run app.py --server.runOnSave true

docker-build:
	docker buildx build --platform linux/amd64 --load -t $(IMAGE_URI) .

docker-push:
	docker push $(IMAGE_URI)

deploy:
	gcloud run deploy $(SERVICE_NAME) --image $(IMAGE_URI) --region $(REGION) --project $(PROJECT_ID) --allow-unauthenticated \
		--max-instances 2 --cpu 1 --memory 4Gi --concurrency 2
