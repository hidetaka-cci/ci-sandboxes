# Method B: dependencies + model weights baked into the image.
# Built only by the image-update job (DLC enabled there; not on measure jobs).
FROM cimg/python:3.12

ARG STRANDS_DECIDER_VERSION=0.1.0
ARG DECIDER_HUB_ID=StrandsAgents/strands-decider-2B-hobson-v19
ARG BASE_MODEL_ID=Qwen/Qwen3.5-2B-Base
ARG BASE_MODEL_REVISION=b1485b2fa6dfa1287294f269f5fb618e03d52d7c

ENV VENV_DIR=/home/circleci/venv \
    HF_HOME=/home/circleci/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/circleci/.cache/huggingface/hub \
    PATH=/home/circleci/venv/bin:$PATH \
    STRANDS_DECIDER_VERSION=${STRANDS_DECIDER_VERSION} \
    DECIDER_HUB_ID=${DECIDER_HUB_ID} \
    BASE_MODEL_ID=${BASE_MODEL_ID} \
    BASE_MODEL_REVISION=${BASE_MODEL_REVISION}

USER circleci
WORKDIR /home/circleci

RUN python3 -m venv "${VENV_DIR}" \
 && . "${VENV_DIR}/bin/activate" \
 && python -m pip install --upgrade pip \
 && python -m pip install torch --index-url https://download.pytorch.org/whl/cpu \
 && python -m pip install "strands-decider==${STRANDS_DECIDER_VERSION}" \
 && python -c "from huggingface_hub import snapshot_download; import os; snapshot_download(os.environ['DECIDER_HUB_ID']); snapshot_download(os.environ['BASE_MODEL_ID'], revision=os.environ['BASE_MODEL_REVISION']); print('prefetch done')"

# Measure jobs should not hit the network for weights.
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1
