package com.paper.dto.user;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class LoginResponse {

    private final String sessionId;
    private final UserResponse user;

    public static LoginResponse of(String sessionId, UserResponse user) {
        return LoginResponse.builder()
                .sessionId(sessionId)
                .user(user)
                .build();
    }
}
