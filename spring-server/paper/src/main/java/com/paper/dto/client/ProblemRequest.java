package com.paper.dto.client;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProblemRequest {

    private Long materialId;
    private String difficulty;  // BEGINNER, INTERMEDIATE, ADVANCED
    private Integer problemCount;
    private String learningDescription;
    private String question;  // QA 질문
    private String answer;  // QA 답변
    private String topic;  // 질문 주제 (분류용)

}
