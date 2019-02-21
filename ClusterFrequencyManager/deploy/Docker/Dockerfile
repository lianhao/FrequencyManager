# Use an official Python runtime as a parent image
FROM python:3.6-slim
# Disables buffered output - for logging
RUN mkdir ClusterFrequencyManager && \
pip install grpcio-tools googleapis-common-protos  &&\
cp *.py *.proto NodeFrequencyManager/

WORKDIR ClusterFrequencyManager
RUN python run_codegen.py

ENTRYPOINT  ["python", "clusterFrequencyManager.py"]