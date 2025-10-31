package com.paper.config;

import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
@ConfigurationProperties(prefix = "file")
@RequiredArgsConstructor
@Getter
public class FileStorageConfig {

    /**
     * 파일 업로드 디렉토리 경로
     * Docker: /app/shared/uploads (Python과 공유)
     * Local: ./uploads
     */
    @Value("${file.upload-dir}")
    private String uploadDir;

    /**
     * 허용된 파일 확장자 목록
     */
    @Value("${file.allowed-extensions}")
    private List<String> allowedExtensions;

    /**
     * 최대 파일 크기 (bytes)
     */
    @Value("${file.max-size}")
    private long maxSize;

}
