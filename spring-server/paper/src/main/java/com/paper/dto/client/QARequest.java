package com.paper.dto.client;

import com.fasterxml.jackson.annotation.JsonProperty;
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
    private Long materialId;

    @JsonProperty("question")
    private String question;
}