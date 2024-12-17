# Use an official Python runtime as a parent image
FROM python:3.11.9-bookworm

# Install necessary packages
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Add and run the UV installer script
ADD https://astral.sh/uv/0.5.9/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Set environment variables
ENV PATH="/root/.local/bin/:$PATH"

# Set working directory in the container to /app
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Add the rest of the application code
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Start the bot
CMD ["uv", "run", "python", "run.py"]