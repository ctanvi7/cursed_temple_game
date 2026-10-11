FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY cursed_temple_game/requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY cursed_temple_game/ ./

EXPOSE 8765
CMD ["sh", "-c", "exec python -m solara run app.py --host 0.0.0.0 --port ${PORT:-8765}"]
