#!/bin/bash
# ============================================================
# setup-vps.sh — Script cài đặt môi trường VPS lần đầu
# Chạy một lần duy nhất trên VPS mới (Ubuntu 20.04/22.04)
#
# Cách dùng trên VPS:
#   curl -fsSL https://raw.githubusercontent.com/YOUREPO/main/setup-vps.sh | bash
# Hoặc copy file lên và chạy:
#   chmod +x setup-vps.sh && ./setup-vps.sh
# ============================================================
set -e

echo "====================================================="
echo "  VPS Setup — Email Translator"
echo "====================================================="

# Cập nhật hệ thống
echo "[1/5] Cập nhật system packages..."
apt-get update -qq
apt-get upgrade -y -qq

# Cài Docker
echo "[2/5] Cài đặt Docker..."
if ! command -v docker &> /dev/null; then
    apt-get install -y -qq \
        ca-certificates curl gnupg lsb-release

    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
       https://download.docker.com/linux/ubuntu \
       $(lsb_release -cs) stable" \
      | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
                           docker-buildx-plugin docker-compose-plugin

    systemctl enable docker
    systemctl start docker
    echo "✅ Docker đã cài xong."
else
    echo "✅ Docker đã tồn tại: $(docker --version)"
fi

# Kiểm tra docker compose
echo "[3/5] Kiểm tra Docker Compose..."
docker compose version
echo "✅ Docker Compose OK."

# Tạo thư mục ứng dụng
echo "[4/5] Tạo thư mục ứng dụng..."
APP_DIR="/opt/email-translator"
mkdir -p $APP_DIR
chmod 750 $APP_DIR

# Tạo file .env mẫu trên VPS nếu chưa có
if [ ! -f "$APP_DIR/.env" ]; then
    cat > $APP_DIR/.env << 'ENV_TEMPLATE'
# ============================================
# GMAIL CONFIGURATION
# ============================================
GMAIL_ADDRESS=YOUR_EMAIL@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# ============================================
# IMAP / SMTP SETTINGS (Gmail default)
# ============================================
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# ============================================
# APP SETTINGS
# ============================================
POLL_INTERVAL_SECONDS=300
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs
DATABASE_URL=sqlite:///./translator.db
SECRET_KEY=CHANGE_THIS_TO_A_RANDOM_SECRET_KEY
ENV_TEMPLATE

    echo "⚠️  File .env mẫu đã tạo tại $APP_DIR/.env"
    echo "   Hãy chỉnh sửa file này với thông tin thực của bạn!"
fi

echo "[5/5] Cài đặt Nginx, Certbot SSL và các công cụ hữu ích..."
apt-get install -y -qq git htop curl wget nginx certbot python3-certbot-nginx

# Tạo file cấu hình Nginx Server Block cho tên miền russian-translatoz.xyz
echo "--- VPS: Cấu hình Nginx Reverse Proxy..."
cat > /etc/nginx/sites-available/russian-translatoz.xyz << 'NGINX_CONFIG'
server {
    listen 80;
    server_name russian-translatoz.xyz www.russian-translatoz.xyz;

    # Hạn mức dung lượng upload tối đa cho file Word lớn (50MB)
    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Hỗ trợ WebSockets (nếu cần cho live connection)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
NGINX_CONFIG

# Kích hoạt cấu hình Nginx và reload dịch vụ
ln -sf /etc/nginx/sites-available/russian-translatoz.xyz /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default || true
nginx -t
systemctl restart nginx

echo ""
echo "====================================================="
echo "  ✅ VPS đã sẵn sàng!"
echo ""
echo "  Bước tiếp theo:"
echo "  1. Chỉnh sửa file .env:"
echo "     nano $APP_DIR/.env"
echo "     (Điền GEMINI_API_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD, v.v.)"
echo ""
echo "  2. Clone code từ GitHub:"
echo "     cd $APP_DIR"
echo "     git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git ."
echo ""
echo "  3. Khởi chạy ứng dụng bằng Docker:"
echo "     docker compose up -d --build"
echo ""
echo "  4. Kích hoạt HTTPS bảo mật (SSL) qua Let's Encrypt:"
echo "     sudo certbot --nginx -d russian-translatoz.xyz -d www.russian-translatoz.xyz"
echo "     (Lưu ý: Bạn cần trỏ DNS của tên miền về IP 103.77.243.1 trước)"
echo ""
echo "  5. Kiểm tra logs hệ thống:"
echo "     docker compose logs -f"
echo "====================================================="
