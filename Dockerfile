# Use an official Python runtime as a parent image
FROM python:3.11.9-bookworm

# Set working directory in the container to /app
WORKDIR /app

# Add requirements.txt before other files to leverage caching
ADD requirements.txt /app/

# Install packages from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Add the rest of the application code
ADD . /app

# Start the bot
CMD ["python", "run.py"]
