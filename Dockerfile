# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
# This includes main.py, the 'function' directory, and decoders.py
COPY . .

# Set a default value for the handler function environment variable.
# This can be overridden at runtime (e.g., with `docker run -e ...`).
ENV HANDLER_FUNCTION="function.handler.handle"

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using Uvicorn
# --host 0.0.0.0 makes it accessible from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
