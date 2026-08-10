# Level2-mathmodel engine image (separate from level2-collector).
FROM python:3.12-bookworm

WORKDIR /app

COPY services/engine/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/engine /app/services/engine
COPY contracts /app/contracts

ENV PYTHONPATH=/app/services/engine/src
ENV LEVEL2_API_URL=http://level2-collector:8080
ENV MATHMODEL_PORT=8090

EXPOSE 8090

# Wave 0: scaffold entrypoint (no real HTTP server yet).
CMD ["python", "-c", "from level2_mathmodel.api.app import create_app; print(create_app())"]
