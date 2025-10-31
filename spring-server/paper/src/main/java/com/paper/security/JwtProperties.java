package com.paper.security;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "jwt")
public class JwtProperties {

    /**
     * HMAC 서명에 사용할 비밀 키.
     */
    private String secret = "default-secret-key-change-me";

    /**
     * 액세스 토큰 만료 시간 (밀리초).
     */
    private long expiration = 86_400_000L; // 24시간
}
