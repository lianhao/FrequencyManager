# Use an official Python runtime as a parent image
FROM python:3.7-slim

RUN mkdir NodeFrequencyManager && \
pip install grpcio-tools googleapis-common-protos  

COPY *.py *.proto NodeFrequencyManager/

WORKDIR NodeFrequencyManager
RUN ls
RUN python run_codegen.py

ENTRYPOINT  ["python", "nodeFrequencyManager.py"]
