FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean

RUN pip install jupyter notebook

COPY . .

RUN pip install -e .

WORKDIR /app/notebooks

# Expose Jupyter port
EXPOSE 8888

# Start Jupyter notebook
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
