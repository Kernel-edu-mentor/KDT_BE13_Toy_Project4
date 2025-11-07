# -------------------------
# STAGE 1: BUILD STAGE
# 의존성 설치 및 프로덕션 빌드 수행
# -------------------------
FROM node:20-alpine AS builder

# 작업 디렉토리 설정
WORKDIR /app

# 패키지 파일 복사 (캐시 활용을 위해 먼저 복사)
COPY package.json package-lock.json ./

# 의존성 설치
# CI 환경에서는 --frozen-lockfile, 개발 환경에서는 npm install
RUN npm install

# 나머지 소스 코드 복사
COPY . .

# 프로덕션 빌드 실행
# 생성된 정적 파일은 일반적으로 'build' 또는 'dist' 폴더에 저장됩니다.
RUN npm run build


# -------------------------
# STAGE 2: PRODUCTION/RUNTIME STAGE
# 최종 실행 환경 구성 (최소한의 Nginx 이미지 사용)
# -------------------------
FROM nginx:alpine

# Nginx 기본 설정 파일 삭제
RUN rm /etc/nginx/conf.d/default.conf

# Nginx 설정 파일 복사
# 프로젝트 루트에 'nginx.conf' 파일이 있다고 가정합니다.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 빌드 스테이지에서 생성된 정적 파일 복사
# 프로젝트에 맞게 '/app/build' 부분을 수정하세요 (예: '/app/dist').
COPY --from=builder /app/build /usr/share/nginx/html

# 80번 포트를 외부에 노출
EXPOSE 80

# Nginx 시작 (기본 이미지의 CMD를 그대로 사용)
CMD ["nginx", "-g", "daemon off;"]