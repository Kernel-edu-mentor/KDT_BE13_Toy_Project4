FROM gradle:8.5-jdk21 AS builder

WORKDIR /app

# Gradle 캐시 최적화를 위해 먼저 의존성 파일 복사
COPY build.gradle settings.gradle ./
COPY gradle ./gradle

# 의존성 다운로드 (캐싱)
RUN gradle dependencies --no-daemon || true

# 소스 코드 복사 및 빌드
COPY . .
RUN gradle bootJar --no-daemon

# 런타임 이미지
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# 공유 디렉토리 생성
RUN mkdir -p /app/shared/uploads

# 빌드된 JAR 복사
COPY --from=builder /app/build/libs/*.jar app.jar

# 포트 노출
EXPOSE 8080

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1

# 애플리케이션 실행
ENTRYPOINT ["java", "-jar", "app.jar"]