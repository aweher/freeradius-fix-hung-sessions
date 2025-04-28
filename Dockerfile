FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY fix_sessions.py .

CMD ["sh", "-c", "while true; do python fix_sessions.py; sleep ${EXEC_INTERVAL:-3600}; done"]
