# ============================================================
# Dockerfile — Backend (FastAPI + APScheduler)
# ============================================================
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Cài hệ thống phụ thuộc cho python-docx (lxml, libxml2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy và cài requirements vào virtualenv riêng
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================================
# Stage 2: Runtime (image nhỏ gọn nhất)
FROM python:3.11-slim AS runtime

WORKDIR /app

# Chỉ copy thư viện đã cài, bỏ compiler/build tools
COPY --from=builder /install /usr/local

# Copy source code application
COPY app/       app/
COPY core/      core/
COPY main.py    .

# Thư mục lưu file tạm (sẽ được mount qua volume)
RUN mkdir -p uploads outputs

# Expose port backend
EXPOSE 8000

# Tạo user non-root để bảo mật
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
# USER appuser

# Khởi động FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
