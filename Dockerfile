# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set a default value for the handler function environment variable.
ENV HANDLER_FUNCTION="function.handler.handle"

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using Uvicorn
# The path is now 'app.main:app' to reflect the new directory structure.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]