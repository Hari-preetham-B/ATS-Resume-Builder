# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install dependencies including gunicorn
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the rest of the application
COPY . .

# Make port 7860 available
EXPOSE 7860

# Run with gunicorn (production server)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:7860", "app:app"]