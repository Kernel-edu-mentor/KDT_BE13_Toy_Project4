# -------------------------------
# 1️⃣ 빌드 스테이지 (Vite 빌드)
# -------------------------------
FROM node:20-alpine AS builder

# 작업 디렉토리 설정
WORKDIR /app

# 패키지 파일 복사 및 의존성 설치
COPY package.json package-lock.json ./
RUN npm install

# 전체 코드 복사
COPY . .

# Vite로 빌드 (결과물은 dist 폴더에 생성)
RUN npm run build

# -------------------------------
# 2️⃣ 배포 스테이지 (Nginx)
# -------------------------------
FROM nginx:alpine

# 기본 설정 제거 후 사용자 설정 복사
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 빌드 결과(dist 폴더)를 Nginx 기본 루트로 복사
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx 포트 노출
EXPOSE 80

# 컨테이너 실행 시 Nginx 시작
CMD ["nginx", "-g", "daemon off;"]