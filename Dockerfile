FROM python:3.12-slim AS runtime

ARG PTCG_VERSION=0.2.0-pre-alpha.2
LABEL org.opencontainers.image.title="Pokemon TCG Card Detector" \
      org.opencontainers.image.version="${PTCG_VERSION}" \
      org.opencontainers.image.description="Unreleased local-first Pre-Alpha evidence workflow"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PTCG_PROJECT_ROOT=/workspace

WORKDIR /opt/app
COPY pyproject.toml README.md LICENSE requirements-runtime.lock.txt ./
COPY src ./src
COPY templates ./templates
ARG PYTORCH_CPU_INDEX=https://download.pytorch.org/whl/cpu
RUN python -m pip install --no-cache-dir \
      --no-deps \
      --index-url "${PYTORCH_CPU_INDEX}" \
      torch==2.14.1 torchvision==0.29.1 \
    && python -m pip install --no-cache-dir -r requirements-runtime.lock.txt \
    && python -m pip install --no-cache-dir --no-deps --no-build-isolation .

RUN useradd --create-home --uid 10001 ptcg \
    && mkdir -p /workspace/.local/runs /workspace/.local/uploads /workspace/.models/easyocr \
    && chown -R ptcg:ptcg /workspace

USER 10001:10001
WORKDIR /workspace
ENTRYPOINT ["ptcg"]
CMD ["--help"]
