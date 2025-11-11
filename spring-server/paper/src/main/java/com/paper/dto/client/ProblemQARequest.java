package com.paper.dto.client;

import lombok.*;

import java.util.List;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProblemQARequest {

    private Long chatId;
    private Long materialId;
    private String difficulty;  // BEGINNER, INTERMEDIATE, ADVANCED
    private Integer problemCount;

}
