# Use an official Python runtime as a parent image
FROM python:3.11.9-bookworm

# Set working directory in the container to /app
WORKDIR /app

# Add current directory contents into the container at /app
ADD . /app

# Install system dependencies for cryptg
RUN apt-get update && apt-get install -y \
    clang \
    libjpeg-dev \
    libwebp-dev \
    python3-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Rust using rustup
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Upgrade setuptools
RUN pip install --upgrade setuptools

# Install cryptg and its dependencies separately
RUN pip install --no-cache-dir cryptg

# Install packages from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Start the bot
CMD ["python", "run.py"]