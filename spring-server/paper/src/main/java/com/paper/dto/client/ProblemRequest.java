package com.paper.dto.client;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProblemRequest {

    private Long materialId;
    private String difficulty;  // BEGINNER, INTERMEDIATE, ADVANCED
    private Integer problemCount;
    private String learningDescription;

}
