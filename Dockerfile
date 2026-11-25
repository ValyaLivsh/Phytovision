FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir numpy pillow onnxruntime fastapi "uvicorn[standard]" \
    python-multipart pydantic "psycopg[binary]"
COPY src/ src/
COPY models/plant_classifier.onnx models/model_meta.json models/
ENV PYTHONPATH=/app/src
EXPOSE 8000
CMD ["uvicorn", "phytovision.api:app", "--host", "0.0.0.0", "--port", "8000"]
