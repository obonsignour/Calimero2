PY := python3
PIP := $(PY) -m pip
VENV := .venv
ACT := . $(VENV)/bin/activate

APP := cast-imaging-agent
IMAGE := $(APP):latest

.PHONY: help
help:
	@echo "Targets:"
	@echo "  make venv           # Create virtualenv"
	@echo "  make install        # Install runtime deps"
	@echo "  make dev            # Install dev deps (pytest, etc.)"
	@echo "  make test           # Run tests"
	@echo "  make run            # Run FastAPI locally"
	@echo "  make docker-build   # Build Docker image"
	@echo "  make up             # docker compose up (build+run)"
	@echo "  make down           # docker compose down"
	@echo "  make logs           # follow agent logs"

$(VENV):
	$(PY) -m venv $(VENV)

.PHONY: venv
venv: $(VENV)

.PHONY: install
install: venv
	$(ACT) && $(PIP) install --upgrade pip
	$(ACT) && $(PIP) install -r requirements.txt

.PHONY: dev
dev: install
	$(ACT) && $(PIP) install -r requirements-dev.txt

.PHONY: test
test:
	$(ACT) && pytest -q

.PHONY: run
run:
	$(ACT) && ANTHROPIC_API_KEY=$${ANTHROPIC_API_KEY} IMAGING_API_KEY=$${IMAGING_API_KEY} \
	MCP_IMAGING_URL=$${MCP_IMAGING_URL:-http://localhost:8282/mcp/} \
	$(PY) -m app.api.main

.PHONY: docker-build
docker-build:
	docker build -t $(IMAGE) .

.PHONY: up
up:
	docker compose up --build -d

.PHONY: down
down:
	docker compose down

.PHONY: logs
logs:
	docker compose logs -f agent
