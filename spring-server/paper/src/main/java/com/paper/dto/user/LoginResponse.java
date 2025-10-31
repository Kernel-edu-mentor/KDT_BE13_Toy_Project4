package com.paper.dto.user;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class LoginResponse {

    private final String accessToken;
    private final String tokenType;
    private final UserResponse user;

    public static LoginResponse of(String token, UserResponse user) {
        return LoginResponse.builder()
                .accessToken(token)
                .tokenType("Bearer")
                .user(user)
                .build();
    }
}
