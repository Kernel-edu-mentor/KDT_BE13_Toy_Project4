package com.paper.dto;

import com.paper.domain.Material;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MaterialResponse {

    private Long id;
    private String title;
    private String fileType;
    private Integer pageCount;
    private String parseStatus;
    private LocalDateTime createdAt;

    public static MaterialResponse from(Material material) {
        return MaterialResponse.builder()
                .id(material.getId())
                .title(material.getTitle())
                .fileType(material.getFileType().name())
                .pageCount(material.getPageCount())
                .parseStatus(material.getParseStatus().name())
                .createdAt(material.getCreatedAt())
                .build();
    }
}

