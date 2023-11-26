# Use an official Python 3.10 image based on Alpine Linux
FROM python:3.10-alpine

# Set environment variables for Python (you can adjust as needed)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies, including libmagic
RUN apk add --no-cache libmagic



# Create and set the working directory inside the container
WORKDIR /app

# Create a non-root user
RUN adduser -D inspector
USER inspector

# Copy the requirements file and install Python dependencies
COPY src/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pika
# Copy your application code to the container
COPY src /app/

CMD ["python", "main.py"]

