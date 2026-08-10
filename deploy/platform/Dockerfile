# Level2-mathmodel lab image: FastAPI engine + built React UI on :8090.
# Separate from level2-collector / jenkins.

FROM node:22-bookworm AS web
WORKDIR /web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

FROM python:3.12-bookworm

WORKDIR /app

COPY services/engine/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/engine /app/services/engine
COPY contracts /app/contracts
COPY technologies/copper_electrorefining /app/technologies/copper_electrorefining
COPY --from=web /web/dist /app/web/dist

# Engine src + copper tech pack (same dual path as engine pytest).
ENV PYTHONPATH=/app/services/engine/src:/app/technologies/copper_electrorefining
ENV LEVEL2_API_URL=http://level2-collector:8080
ENV MATHMODEL_PORT=8090
ENV MATHMODEL_WEB_DIST=/app/web/dist

EXPOSE 8090

# Lab/platform entrypoint: API + static UI on MATHMODEL_PORT (default 8090).
CMD ["sh", "-c", "exec uvicorn level2_mathmodel.api.app:create_app --factory --host 0.0.0.0 --port ${MATHMODEL_PORT:-8090}"]
