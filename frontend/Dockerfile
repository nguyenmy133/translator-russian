# ============================================================
# Dockerfile.frontend — React/Vite + Nginx
# ============================================================

# Stage 1: Build React app
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files trước (tận dụng Docker layer cache)
COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

# Copy toàn bộ source và build
COPY . .

# VITE_API_BASE_URL trống = React sẽ gọi /api (relative path)
# Nginx sẽ proxy /api → backend container
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

ARG VITE_GOOGLE_CLIENT_ID=""
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID

RUN npm run build

# ============================================================
# Stage 2: Serve bằng Nginx
FROM nginx:1.27-alpine AS runtime

# Xoá config default của Nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copy Nginx config tùy chỉnh
COPY nginx.conf /etc/nginx/conf.d/app.conf

# Copy build output từ stage 1
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
