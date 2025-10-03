FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI to execute commands in pcap-miner container
RUN apt-get update && \
    apt-get install -y docker.io && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY processor.py .

CMD ["python", "-u", "processor.py"]
