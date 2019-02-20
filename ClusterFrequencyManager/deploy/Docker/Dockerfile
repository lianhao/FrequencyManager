# Use an official Python runtime as a parent image
FROM python:3.6-slim
# Disables buffered output - for logging
ENV PYTHONUNBUFFERD=0

RUN mkdir NodeFrequencyManager && \
pip install grpcio-tools googleapis-common-protos  

COPY *.py *.proto NodeFrequencyManager/


WORKDIR NodeFrequencyManager
RUN ls
RUN python run_codegen.py

ENTRYPOINT  ["python", "nodeFrequencyManager.py"]