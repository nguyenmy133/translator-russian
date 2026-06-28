#!/bin/bash
# ============================================================
# deploy.sh — Deploy Email Translator lên VPS qua SSH
#
# Cách dùng:
#   chmod +x deploy.sh
#   ./deploy.sh
#
# Yêu cầu: VPS đã cài Docker + Docker Compose
# ============================================================
set -e  # Dừng ngay khi có lỗi

# ── THAY ĐỔI CÁC BIẾN SAU CHO PHÙ HỢP VPS CỦA BẠN ────────
VPS_USER="root"                      # user SSH trên VPS
VPS_HOST="YOUR_VPS_IP"              # IP hoặc domain VPS của bạn
VPS_PORT="22"                        # Port SSH (mặc định 22)
APP_DIR="/opt/email-translator"      # Thư mục triển khai trên VPS
# ────────────────────────────────────────────────────────────

echo "====================================================="
echo "  Email Translator — Deploying to VPS"
echo "  Host: $VPS_USER@$VPS_HOST"
echo "====================================================="

# Bước 1: Đảm bảo git đã commit mới nhất
echo ""
echo "[1/5] Kiểm tra git status..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Có file chưa commit. Vui lòng commit trước khi deploy."
    git status --short
    exit 1
fi
echo "✅ Git clean."

# Bước 2: Push code lên GitHub
echo ""
echo "[2/5] Đẩy code lên GitHub..."
git push origin main
echo "✅ Đã push code."

# Bước 3: SSH vào VPS và pull code + rebuild Docker
echo ""
echo "[3/5] SSH vào VPS và deploy..."
ssh -p "$VPS_PORT" "$VPS_USER@$VPS_HOST" bash << REMOTE_SCRIPT
set -e

echo "--- VPS: Chuẩn bị thư mục ứng dụng..."
mkdir -p $APP_DIR
cd $APP_DIR

# Nếu chưa có repo thì clone, ngược lại thì pull
if [ ! -d ".git" ]; then
    echo "--- VPS: Clone repository lần đầu..."
    git clone https://github.com/$(git remote get-url origin | sed 's|.*github.com/||') .
else
    echo "--- VPS: Pull code mới nhất..."
    git pull origin main
fi

# Đảm bảo file .env tồn tại (phải copy thủ công lần đầu)
if [ ! -f ".env" ]; then
    echo "⚠️  CẢNH BÁO: File .env chưa có trên VPS!"
    echo "   Hãy tạo file $APP_DIR/.env với nội dung từ .env.example"
    exit 1
fi

echo "--- VPS: Build và restart Docker containers..."
docker compose pull 2>/dev/null || true
docker compose build --no-cache
docker compose up -d --remove-orphans

echo "--- VPS: Xoá image cũ không dùng..."
docker image prune -f

echo ""
echo "✅ Deploy thành công!"
docker compose ps
REMOTE_SCRIPT

echo ""
echo "[4/5] Kiểm tra trạng thái services..."
sleep 3
ssh -p "$VPS_PORT" "$VPS_USER@$VPS_HOST" "cd $APP_DIR && docker compose ps"

echo ""
echo "[5/5] Xong!"
echo "====================================================="
echo "  🚀 Ứng dụng đang chạy tại: http://$VPS_HOST"
echo "  📋 API docs: http://$VPS_HOST/api/docs"
echo "====================================================="
