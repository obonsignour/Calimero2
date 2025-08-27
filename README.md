# Calimero — Local development

This project uses a local virtual environment (`.venv`) at the repository root.

Quick setup

1. Create the virtual environment (if not already created):

```bash
cd /home/obo/sources/calimero
python3 -m venv .venv
```

2. Activate the venv and install dependencies:

```bash
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Run the app (development)

```bash
. .venv/bin/activate
uvicorn app.api.main:app --reload
```

VS Code helper tasks

Open the Command Palette (Ctrl+Shift+P) -> "Tasks: Run Task" and choose one of:

- "Install requirements (venv)" — activates `.venv` and installs `requirements.txt`.
- "Run dev server (venv)" — activates `.venv` and launches the Uvicorn dev server.

Notes
- The scripts above assume the project root is `/home/obo/sources/calimero` and the app entrypoint is `app.api.main:app`.
- If `python3-venv` is missing on your system, install it (Debian/Ubuntu):

```bash
sudo apt update
sudo apt install -y python3-venv
```

Run the tests
Single file:
make test-file TEST=tests/test_api_routes.py

Single test (node id):
make test-node NODEID=tests/test_api_routes.py::test_impact_route_ok

Keyword expression:
make test-k K="impact and not api_routes"

All tests:
make test