# 🌐 Email Translator — Ru → Vi

Tự động dịch file Word đính kèm trong email từ **tiếng Nga → tiếng Việt**.

---

## 🏗️ Kiến Trúc

```
Clean Architecture
├── Domain          → Entities, Value Objects, Repository Interfaces
├── Application     → Use Cases, Ports (interfaces)
├── Infrastructure  → Gmail IMAP/SMTP, SQLite, Google Translate, python-docx
└── Presentation    → FastAPI JSON API + React Dashboard
```

---

## 🚀 Chạy Local (Development)

### Bước 1: Cấu hình Gmail

1. Bật **2-Factor Authentication** trong tài khoản Google
2. Vào https://myaccount.google.com/apppasswords
3. Tạo App Password (chọn "Mail" + "Windows Computer")
4. Bật **IMAP**: Gmail Settings → See all settings → Forwarding and POP/IMAP → Enable IMAP

### Bước 2: Cấu hình môi trường

```bash
cp .env.example .env
# Mở .env và điền thông tin Gmail
```

### Bước 3: Chạy Backend

```bash
# Tạo virtualenv
python -m venv venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate        # Linux/Mac

# Cài dependencies
pip install -r requirements.txt

# Chạy server
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Bước 4: Chạy Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173

---

## 📂 Cách Sử Dụng

1. **Gửi email** tới địa chỉ Gmail đã cấu hình
2. **Đính kèm** file Word tên chứa `(ru)` — ví dụ: `bai_viet(ru).docx`
3. **Chờ 5 phút** (hoặc bấm "Quét ngay" trên Dashboard)
4. Hệ thống tự động dịch và **gửi lại email** với file `bai_viet(vi).docx`

---

## 🌐 Deploy lên Render.com (FREE)

### Backend

1. Push code lên GitHub
2. Vào https://render.com → **New Web Service**
3. Connect GitHub repo
4. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Thêm **Environment Variables** (từ file .env)
6. Deploy!

### Frontend

1. Vào Render.com → **New Static Site**
2. Connect cùng GitHub repo
3. Settings:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
4. Deploy!

> ⚠️ **Lưu ý**: Render.com free tier "ngủ" sau 15 phút không có request. Scheduler sẽ dừng khi server ngủ. Để luôn chạy, dùng cron job bên ngoài ping server mỗi 10 phút (uptime robot miễn phí).

---

## 💡 Chi Phí Vận Hành

| Dịch vụ | Chi phí |
|---|---|
| Render.com (Backend + Frontend) | **FREE** |
| Google Translate (deep-translator) | **FREE** (không cần API key) |
| Gmail IMAP/SMTP | **FREE** |
| **Tổng** | **$0/tháng** |

---

## 🔧 Cấu Trúc Project

```
email-translator/
├── app/
│   ├── domain/              # Layer 1: Entities + Interfaces
│   ├── application/         # Layer 2: Use Cases + Ports
│   ├── infrastructure/      # Layer 3: Adapters (Gmail, DB, Translate, docx)
│   └── presentation/api/    # Layer 4: FastAPI JSON routes
├── core/
│   ├── config.py            # Settings (pydantic-settings)
│   ├── dependencies.py      # DI Container
│   └── scheduler.py         # APScheduler
├── frontend/                # React + Vite
│   └── src/
│       ├── api/             # Axios client
│       ├── components/      # Navbar, StatsCards, JobsTable, StatusBadge
│       ├── context/         # ToastContext
│       └── pages/           # Dashboard, JobDetail
├── main.py                  # FastAPI entry point
├── requirements.txt
├── render.yaml              # Render.com deploy config
└── .env.example
```
