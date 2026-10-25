# Build context is the repo root so contract_core can be installed.
FROM python:3.12-slim

WORKDIR /srv
COPY contract_core /srv/contract_core
RUN pip install --no-cache-dir /srv/contract_core

COPY worker/requirements.txt /srv/worker/requirements.txt
RUN pip install --no-cache-dir -r /srv/worker/requirements.txt

COPY worker /srv/worker
WORKDIR /srv/worker
CMD ["arq", "worker.main.WorkerSettings"]
