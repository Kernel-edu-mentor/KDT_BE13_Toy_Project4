package com.paper.service;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

@Slf4j
@Service
@RequiredArgsConstructor
public class KakaoService {

    private final RestTemplate restTemplate;

    @Value("${kakao.rest-api-key}")
    private String restApiKey;

    @Value("${kakao.client-secret:}")
    private String clientSecret;

    @Value("${kakao.redirect-uri}")
    private String redirectUri;

    @Value("${kakao.token-url}")
    private String tokenUrl;

    @Value("${kakao.user-info-url}")
    private String userInfoUrl;

    public String exchangeCodeForToken(String code) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

            MultiValueMap<String, String> params = new LinkedMultiValueMap<>();
            params.add("grant_type", "authorization_code");
            params.add("client_id", restApiKey);
            params.add("redirect_uri", redirectUri);
            params.add("code", code);
            if (clientSecret != null && !clientSecret.isEmpty()) {
                params.add("client_secret", clientSecret);
            }

            HttpEntity<MultiValueMap<String, String>> entity = new HttpEntity<>(params, headers);
            ResponseEntity<TokenResponse> response = restTemplate.exchange(
                    tokenUrl,
                    HttpMethod.POST,
                    entity,
                    TokenResponse.class
            );

            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                log.info("카카오 토큰 교환 성공");
                return response.getBody().getAccessToken();
            }

            log.error("카카오 토큰 교환 실패 - Status: {}, Body: {}", response.getStatusCode(), response.getBody());
            throw new RuntimeException("카카오 토큰 교환 실패: HTTP " + response.getStatusCode());
        } catch (org.springframework.web.client.HttpClientErrorException e) {
            log.error("카카오 토큰 교환 중 HTTP 에러 발생: Status={}, Response={}", e.getStatusCode(), e.getResponseBodyAsString());
            if (e.getStatusCode().value() == 401) {
                throw new RuntimeException("카카오 인증 실패 (401): 인가 코드가 잘못되었거나 redirect_uri가 일치하지 않습니다. Response: " + e.getResponseBodyAsString());
            }
            throw new RuntimeException("카카오 토큰 교환 실패: " + e.getMessage());
        } catch (Exception e) {
            log.error("카카오 토큰 교환 중 오류 발생: {}", e.getMessage(), e);
            throw new RuntimeException("카카오 토큰 교환 실패: " + e.getMessage());
        }
    }

    public KakaoUserInfo getUserInfo(String accessToken) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.set("Authorization", "Bearer " + accessToken);
            headers.set("Content-type", "application/x-www-form-urlencoded;charset=utf-8");

            HttpEntity<String> entity = new HttpEntity<>(headers);
            ResponseEntity<KakaoUserInfo> response = restTemplate.exchange(
                    userInfoUrl,
                    HttpMethod.GET,
                    entity,
                    KakaoUserInfo.class
            );

            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                log.info("카카오 사용자 정보 조회 성공: {}", response.getBody().getId());
                return response.getBody();
            }

            log.error("카카오 사용자 정보 조회 실패 - Status: {}, Body: {}", response.getStatusCode(), response.getBody());
            throw new RuntimeException("카카오 사용자 정보 조회 실패: HTTP " + response.getStatusCode());
        } catch (org.springframework.web.client.HttpClientErrorException e) {
            log.error("카카오 사용자 정보 조회 중 HTTP 에러 발생: Status={}, Response={}", e.getStatusCode(), e.getResponseBodyAsString());
            if (e.getStatusCode().value() == 401) {
                throw new RuntimeException("카카오 사용자 정보 조회 실패 (401): Access Token이 잘못되었거나 만료되었습니다. Response: " + e.getResponseBodyAsString());
            }
            throw new RuntimeException("카카오 사용자 정보 조회 실패: " + e.getMessage());
        } catch (Exception e) {
            log.error("카카오 사용자 정보 조회 중 오류 발생: {}", e.getMessage(), e);
            throw new RuntimeException("카카오 사용자 정보 조회 실패: " + e.getMessage());
        }
    }

    @Getter
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class KakaoUserInfo {
        private Long id;
        @JsonProperty("kakao_account")
        private KakaoAccount kakaoAccount;

        @Getter
        @JsonIgnoreProperties(ignoreUnknown = true)
        public static class KakaoAccount {
            private String email;
            private Profile profile;

            @Getter
            @JsonIgnoreProperties(ignoreUnknown = true)
            public static class Profile {
                private String nickname;
            }
        }
    }

    public void logout(String accessToken) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.set("Authorization", "Bearer " + accessToken);
            headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

            HttpEntity<String> entity = new HttpEntity<>(headers);
            ResponseEntity<String> response = restTemplate.exchange(
                    "https://kapi.kakao.com/v1/user/logout",
                    HttpMethod.POST,
                    entity,
                    String.class
            );

            if (response.getStatusCode().is2xxSuccessful()) {
                log.info("카카오 로그아웃 성공");
            } else {
                log.warn("카카오 로그아웃 실패 - Status: {}", response.getStatusCode());
            }
        } catch (Exception e) {
            log.error("카카오 로그아웃 중 오류 발생: {}", e.getMessage(), e);
            // 로그아웃 실패해도 세션은 무효화되어야 하므로 예외를 던지지 않음
        }
    }

    @Getter
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class TokenResponse {
        @JsonProperty("access_token")
        private String accessToken;
        @JsonProperty("token_type")
        private String tokenType;
        @JsonProperty("refresh_token")
        private String refreshToken;
        @JsonProperty("expires_in")
        private Integer expiresIn;
        private String scope;
    }
}

