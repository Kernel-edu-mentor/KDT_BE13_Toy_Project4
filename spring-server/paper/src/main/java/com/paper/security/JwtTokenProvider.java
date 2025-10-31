package com.paper.security;

import com.paper.domain.User;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

@Component
@RequiredArgsConstructor
public class JwtTokenProvider {

    private static final String HMAC_ALGORITHM = "HmacSHA256";

    private final JwtProperties jwtProperties;
    private final CustomUserDetailsService userDetailsService;
    private final ObjectMapper objectMapper;

    public String generateToken(String username, User.Role role) {
        long now = System.currentTimeMillis();
        long expiresAt = now + jwtProperties.getExpiration();

        Map<String, Object> header = new HashMap<>();
        header.put("alg", "HS256");
        header.put("typ", "JWT");

        Map<String, Object> payload = new HashMap<>();
        payload.put("sub", username);
        payload.put("role", role.name());
        payload.put("iat", now / 1000);
        payload.put("exp", expiresAt / 1000);

        String encodedHeader = encode(header);
        String encodedPayload = encode(payload);
        String signature = sign(encodedHeader + "." + encodedPayload);

        return encodedHeader + "." + encodedPayload + "." + signature;
    }

    public boolean validateToken(String token) {
        if (!StringUtils.hasText(token)) {
            return false;
        }
        try {
            Map<String, Object> claims = parseClaims(token);
            Object exp = claims.get("exp");
            if (!(exp instanceof Number)) {
                return false;
            }
            long expSeconds = ((Number) exp).longValue();
            return Instant.ofEpochSecond(expSeconds).isAfter(Instant.now());
        } catch (Exception e) {
            return false;
        }
    }

    public Authentication getAuthentication(String token) {
        Map<String, Object> claims = parseClaims(token);
        String username = (String) claims.get("sub");
        UserDetails userDetails = userDetailsService.loadUserByUsername(username);
        return new UsernamePasswordAuthenticationToken(userDetails, token, userDetails.getAuthorities());
    }

    private Map<String, Object> parseClaims(String token) {
        String[] parts = token.split("\\.");
        if (parts.length != 3) {
            throw new IllegalArgumentException("Invalid token format");
        }

        String headerAndPayload = parts[0] + "." + parts[1];
        String expectedSignature = sign(headerAndPayload);
        byte[] providedSig = parts[2].getBytes(StandardCharsets.UTF_8);
        byte[] expectedSig = expectedSignature.getBytes(StandardCharsets.UTF_8);
        if (!MessageDigest.isEqual(providedSig, expectedSig)) {
            throw new IllegalArgumentException("Invalid token signature");
        }

        String payloadJson = new String(Base64.getUrlDecoder().decode(parts[1]), StandardCharsets.UTF_8);
        try {
            return objectMapper.readValue(payloadJson, new TypeReference<Map<String, Object>>() {});
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("Failed to parse token payload", e);
        }
    }

    private String encode(Map<String, Object> data) {
        try {
            String json = objectMapper.writeValueAsString(data);
            return Base64.getUrlEncoder().withoutPadding().encodeToString(json.getBytes(StandardCharsets.UTF_8));
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("Failed to serialize token payload", e);
        }
    }

    private String sign(String data) {
        try {
            Mac mac = Mac.getInstance(HMAC_ALGORITHM);
            SecretKeySpec keySpec = new SecretKeySpec(jwtProperties.getSecret().getBytes(StandardCharsets.UTF_8), HMAC_ALGORITHM);
            byte[] signature = mac.doFinal(data.getBytes(StandardCharsets.UTF_8));
            return Base64.getUrlEncoder().withoutPadding().encodeToString(signature);
        } catch (GeneralSecurityException e) {
            throw new IllegalStateException("Failed to sign JWT", e);
        }
    }
}
