FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DB_BACKEND=sqlite
WORKDIR /app
COPY requirements_sqlite.txt ./requirements_sqlite.txt
RUN pip install --no-cache-dir -r requirements_sqlite.txt
COPY . .
RUN mkdir -p instance app/static/uploads/products
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "run:app"]
