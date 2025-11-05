package com.paper.dto.client;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
public class QAChatCreateRequest {

    @NotBlank(message = "채팅 제목은 필수입니다.")
    private String title;

    @NotNull(message = "자료 ID는 필수입니다.")
    private Long materialId;
}
