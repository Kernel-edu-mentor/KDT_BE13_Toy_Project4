package com.paper.dto.client.python;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.paper.domain.Material;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;

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

    public static MaterialUploadRequest from(Material material, String filePath, String fileType) {
        return MaterialUploadRequest.builder()
                .materialId(material.getId())
                .filePath(filePath)
                .fileType(fileType.toLowerCase())
                .build();
    }

    @Getter
    @Builder
    @AllArgsConstructor
    @NoArgsConstructor
    public static class QARequest {

        @JsonProperty("material_id")
        @NotNull(message = "material_id는 필수입니다.")
        private Long materialId;

        @JsonProperty("question")
        @NotBlank(message = "question은 필수입니다.")
        private String question;

        @JsonProperty("chat_id")
        private Long chatId;
    }

    @Getter
    @Builder
    @AllArgsConstructor
    @NoArgsConstructor
    public static class QAResponse {

        @JsonProperty("answer")
        private String answer;

        @JsonProperty("sources")
        private List<Source> sources;

        @JsonProperty("response_time_ms")
        private Integer responseTimeMs;

        @Getter
        public static class Source {
            private Integer page;
            private String excerpt;
        }
    }
}
