FROM python:3.10-slim

# Prevent python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY userbot_forwarder.py userbot_forwarder.py
COPY autosum_session.session autosum_session.session

CMD ["python", "userbot_forwarder.py"]
