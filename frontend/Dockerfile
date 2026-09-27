# 多阶段构建：node 编译 → nginx 托管

# ---- build stage ----
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json ./
# 没有 lockfile，直接装依赖
RUN npm install --no-audit --no-fund

COPY . .
RUN npm run build

# ---- runtime stage ----
FROM nginx:alpine

# 拷构建产物
COPY --from=build /app/dist /usr/share/nginx/html

# nginx 配置（前端只服务静态资源）
RUN echo 'server { \
    listen 80; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { try_files $uri $uri/ /index.html; } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --retries=10 \
  CMD wget -qO- http://localhost/ >/dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]