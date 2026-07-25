# liqflow_api service image.
# Build context is the api/ Polylith workspace (see compose.yaml) so we can
# copy the bricks (bases/ + components/) into the image.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/bases:/app/components \
    LIQFLOW_API_PORT=8000

WORKDIR /app

# Install runtime dependencies from the project's [project.dependencies].
# uv reads pyproject.toml directly, so there is no separate requirements file.
RUN pip install --no-cache-dir uv
COPY projects/liqflow_api/pyproject.toml /app/pyproject.toml
RUN uv pip install --system --requirement /app/pyproject.toml

# Copy the source bricks (loose Polylith layout; run straight from PYTHONPATH).
COPY bases /app/bases
COPY components /app/components

# Run as a non-root user.
RUN addgroup --system app \
    && adduser --system --ingroup app --uid 10001 app \
    && chown -R app:app /app
USER app

EXPOSE 8000
CMD ["python", "-m", "lf_tool.liqflow_api.core"]
