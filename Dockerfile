FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# For local development we use a simple server
# (Vercel will use serverless functions in production)
EXPOSE 3000
CMD ["python", "api/index.py"]