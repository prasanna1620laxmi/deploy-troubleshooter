FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN sed -i 's/^tensorflow>=/tensorflow-cpu>=/' requirements.txt && pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python scripts/generate_data.py && python scripts/train_model.py
EXPOSE 8501 8000
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
