# ============================================================
# deploy.ps1 — Deploy Email Translator lên VPS qua PowerShell (Windows Native)
#
# Cách dùng:
#   .\deploy.ps1
# ============================================================

$VPS_USER = "root"                      # user SSH trên VPS
$VPS_HOST = "103.77.243.1"              # IP hoặc domain VPS của bạn
$VPS_PORT = "22"                        # Port SSH (mặc định 22)
$APP_DIR = "/opt/email-translator"      # Thư mục triển khai trên VPS

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  Email Translator — Deploying to VPS (PowerShell)" -ForegroundColor Cyan
Write-Host "  Host: $VPS_USER@$VPS_HOST" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# Bước 1: Kiểm tra git status
Write-Host ""
Write-Host "[1/5] Kiểm tra git status..."
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "⚠️  Có file chưa commit. Vui lòng commit trước khi deploy." -ForegroundColor Yellow
    git status --short
    Exit
}
Write-Host "✅ Git sạch." -ForegroundColor Green

# Bước 2: Push code lên GitHub
Write-Host ""
Write-Host "[2/5] Đẩy code lên GitHub..."
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Đẩy code lên GitHub thất bại." -ForegroundColor Red
    Exit
}
Write-Host "✅ Đã push code." -ForegroundColor Green

# Bước 3: SSH vào VPS và deploy
Write-Host ""
Write-Host "[3/5] SSH vào VPS và deploy..."

# Lấy URL remote để clone nếu repo trên VPS chưa được khởi tạo
$remoteUrl = git remote get-url origin
if ($remoteUrl -match "github.com[:/](.+)$") {
    $repoPath = $Matches[1]
    if ($repoPath.EndsWith(".git")) {
        $repoPath = $repoPath.Substring(0, $repoPath.Length - 4)
    }
} else {
    $repoPath = "YOUR_USERNAME/YOUR_REPO"
}

# Gom các lệnh chạy trên VPS thành một chuỗi duy nhất để thực thi qua SSH
$commands = @(
    "set -e",
    "echo '--- VPS: Chuẩn bị thư mục ứng dụng...'",
    "mkdir -p $APP_DIR",
    "cd $APP_DIR",
    "if [ ! -d '.git' ]; then",
    "    echo '--- VPS: Clone repository lần đầu...'",
    "    git clone https://github.com/$repoPath .",
    "else",
    "    echo '--- VPS: Pull code mới nhất...'",
    "    git pull origin main",
    "fi",
    "if [ ! -f '.env' ]; then",
    "    echo '⚠️ CẢNH BÁO: File .env chưa có trên VPS!'",
    "    exit 1",
    "fi",
    "echo '--- VPS: Build và khởi động lại các container...'",
    "docker compose build --no-cache",
    "docker compose up -d --remove-orphans",
    "echo '--- VPS: Xoá image cũ không dùng...'",
    "docker image prune -f",
    "echo '--- VPS: Danh sách container hiện tại...'",
    "docker compose ps"
) -join " && "

# Thực thi lệnh trên VPS qua SSH
ssh -p $VPS_PORT "$VPS_USER@$VPS_HOST" "bash -c '$commands'"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Quá trình chạy lệnh trên VPS gặp lỗi." -ForegroundColor Red
    Exit
}

# Bước 4: Đợi và kiểm tra lại trạng thái
Write-Host ""
Write-Host "[4/5] Đợi kiểm tra trạng thái dịch vụ..."
Start-Sleep -Seconds 3
ssh -p $VPS_PORT "$VPS_USER@$VPS_HOST" "cd $APP_DIR && docker compose ps"

# Bước 5: Hoàn tất
Write-Host ""
Write-Host "[5/5] Hoàn tất!" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
Write-Host "  🚀 Ứng dụng đang chạy tại: https://russian-translatoz.xyz" -ForegroundColor Green
Write-Host "  📋 API docs: https://russian-translatoz.xyz/api/docs" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
