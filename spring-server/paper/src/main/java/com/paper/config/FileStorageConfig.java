package com.paper.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
@ConfigurationProperties(prefix = "file")
@Getter
@Setter
public class FileStorageConfig {

    /**
     * 파일 업로드 디렉토리 경로
     * Docker: /app/shared/uploads (Python과 공유)
     * Local: ./uploads
     */
    private String uploadDir;

    /**
     * 허용된 파일 확장자 목록
     */
    private List<String> allowedExtensions;

    /**
     * 최대 파일 크기 (bytes)
     */
    private long maxSize;

}
