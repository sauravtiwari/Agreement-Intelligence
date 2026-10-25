# Build context is the repo root so contract_core can be installed.
FROM python:3.12-slim

WORKDIR /srv
COPY contract_core /srv/contract_core
RUN pip install --no-cache-dir /srv/contract_core

COPY api/requirements.txt /srv/api/requirements.txt
RUN pip install --no-cache-dir -r /srv/api/requirements.txt

COPY api /srv/api
WORKDIR /srv/api
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
