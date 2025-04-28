FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean

COPY . .

RUN pip install .

# Start Jupyter notebook
#CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
