package com.paper.dto.client;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.paper.domain.Material;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@AllArgsConstructor
public class MaterialUploadRequest {

    @JsonProperty("material_id")
    private Long materialId;

    @JsonProperty("file_path")
    private String filePath;  // 파일 경로만 전달

    @JsonProperty("file_type")
    private String fileType;
}
