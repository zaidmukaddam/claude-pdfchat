FROM python:3.9-slim

COPY . /app

# Copy a start script to the image that will handle the PORT
COPY start.sh /start.sh
RUN chmod +x /start.sh

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install -r requirements.txt

ENTRYPOINT ["/start.sh"]