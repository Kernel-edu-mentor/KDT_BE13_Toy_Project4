package com.paper.dto.client;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class QARequest {

    @JsonProperty("material_id")
    @NotNull(message = "material_id는 필수입니다.")
    private Long materialId;

    @JsonProperty("question")
    @NotBlank(message = "question은 필수입니다.")
    private String question;
}