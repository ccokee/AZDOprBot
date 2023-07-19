# Use an official Python runtime as a base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot script file into the container
COPY azprbot.py .

# Set environment variables for Azure DevOps access token, Telegram bot token, and organization
ENV AZURE_DEVOPS_TOKEN=""
ENV TELEGRAM_BOT_TOKEN=""
ENV AZURE_DEVOPS_ORG=""

# Expose the port the bot will run on (adjust if needed)
EXPOSE 8443

# Run the bot when the container starts
CMD ["python", "azprbot.py"]
