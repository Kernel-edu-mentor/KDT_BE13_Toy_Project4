package com.paper.dto.client;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@AllArgsConstructor
public class MaterialUploadResponse {

    private Long materialId;
    private String status;
    private Integer pageCount;
    private Integer chunkCount;
    private String message;
}
