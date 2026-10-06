# Method B: dependencies + model weights baked into the image.
# Built only by the image-update job (DLC enabled there; not on measure jobs).
FROM cimg/python:3.12

ARG STRANDS_DECIDER_VERSION=0.1.0
ARG DECIDER_HUB_ID=StrandsAgents/strands-decider-2B-hobson-v19
ARG BASE_MODEL_ID=Qwen/Qwen3.5-2B-Base
ARG BASE_MODEL_REVISION=b1485b2fa6dfa1287294f269f5fb618e03d52d7c

# Use /opt (not $HOME) so CircleCI checkout/workdir cannot obscure the cache.
USER root
RUN mkdir -p /opt/hf-cache /opt/venv \
 && chown -R circleci:circleci /opt/hf-cache /opt/venv

USER circleci
WORKDIR /home/circleci

ENV VENV_DIR=/opt/venv \
    HF_HOME=/opt/hf-cache \
    HF_HUB_CACHE=/opt/hf-cache/hub \
    TRANSFORMERS_CACHE=/opt/hf-cache/hub \
    PATH=/opt/venv/bin:$PATH \
    STRANDS_DECIDER_VERSION=${STRANDS_DECIDER_VERSION} \
    DECIDER_HUB_ID=${DECIDER_HUB_ID} \
    BASE_MODEL_ID=${BASE_MODEL_ID} \
    BASE_MODEL_REVISION=${BASE_MODEL_REVISION}

COPY prefetch_into_image.py /opt/prefetch_into_image.py

RUN python3 -m venv "${VENV_DIR}" \
 && . "${VENV_DIR}/bin/activate" \
 && python -m pip install --upgrade pip \
 && python -m pip install torch --index-url https://download.pytorch.org/whl/cpu \
 && python -m pip install "strands-decider==${STRANDS_DECIDER_VERSION}" \
 && python /opt/prefetch_into_image.py \
 && du -sh /opt/models "${VENV_DIR}" \
 && ls -la /opt/models /opt/models/decider /opt/models/base | head -80

# Offline: checkpoint config points at /opt/models/base.
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1
