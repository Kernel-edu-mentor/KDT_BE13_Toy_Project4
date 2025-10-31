package com.paper.dto.client;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@AllArgsConstructor
public class MaterialUploadResponse {

    @JsonProperty("material_id")
    private Long materialId;

    @JsonProperty("status")
    private String status;

    @JsonProperty("page_count")
    private Integer pageCount;

    @JsonProperty("chunk_count")
    private Integer chunkCount;

    @JsonProperty("message")
    private String message;
}
