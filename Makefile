PY := python3
PIP := $(PY) -m pip
VENV := .venv
ACT := . $(VENV)/bin/activate

APP := cast-imaging-agent
IMAGE := $(APP):latest

# --------- Pytest controls ---------
# Examples:
#   make test                       # all tests
#   make test-file TEST=tests/test_api_routes.py
#   make test-node NODEID=tests/test_api_routes.py::test_impact_route_ok
#   make test-k K=impact
TEST ?=
NODEID ?=
K ?=
PYTEST_OPTS ?= -q

.PHONY: help
help:
	@echo "Targets:"
	@echo "  make venv               # Create virtualenv"
	@echo "  make install            # Install runtime deps"
	@echo "  make dev                # Install runtime + dev deps"
	@echo "  make test               # Run ALL tests"
	@echo "  make test-file TEST=... # Run tests in a specific file"
	@echo "  make test-node NODEID=... # Run a single test (file::test)"
	@echo "  make test-k K=...       # Run tests matching -k expression"
	@echo "  make run                # Run FastAPI locally"
	@echo "  make docker-build       # Build Docker image"
	@echo "  make up                 # docker compose up (build+run)"
	@echo "  make down               # docker compose down"
	@echo "  make logs               # follow agent logs"

$(VENV):
	$(PY) -m venv $(VENV)

.PHONY: venv
venv: $(VENV)

.PHONY: install
install: venv
	$(ACT) && $(PIP) install --upgrade pip
	$(ACT) && $(PIP) install -r requirements.txt

.PHONY: dev
dev: venv
	$(ACT) && $(PIP) install --upgrade pip
	# Install both files in one resolver pass to avoid conflicts
	$(ACT) && $(PIP) install -r requirements.txt -r requirements-dev.txt
	$(ACT) && $(PIP) check

.PHONY: test
test:
	$(ACT) && pytest $(PYTEST_OPTS)

.PHONY: test-file tf t
test-file tf t:
	@if [ -z "$(TEST)" ]; then echo "Usage: make test-file TEST=tests/test_api_routes.py"; exit 2; fi
	$(ACT) && pytest $(PYTEST_OPTS) $(TEST)

.PHONY: test-node tn
test-node tn:
	@if [ -z "$(NODEID)" ]; then echo "Usage: make test-node NODEID=tests/test_api_routes.py::test_impact_route_ok"; exit 2; fi
	$(ACT) && pytest $(PYTEST_OPTS) $(NODEID)

.PHONY: test-k tk
test-k tk:
	@if [ -z "$(K)" ]; then echo "Usage: make test-k K=impact"; exit 2; fi
	$(ACT) && pytest $(PYTEST_OPTS) -k "$(K)"

.PHONY: run
run:
	$(ACT) && $(PY) -m app.api.main

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
