# Use an official Python runtime as a parent image
FROM python:3.7-slim
# Disables buffered output - for logging
ENV PYTHONUNBUFFERD=0

RUN mkdir ClusterFrequencyManager && \
pip install grpcio-tools googleapis-common-protos

COPY *.py *.proto ClusterFrequencyManager/

WORKDIR ClusterFrequencyManager
RUN python run_codegen.py

ENTRYPOINT  ["python", "clusterFrequencyManager.py"]