package com.paper.dto.client;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
public class QAChatUpdateRequest {

    @NotBlank(message = "채팅 제목은 필수입니다.")
    private String title;
}
