package com.paper.dto.client;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProblemListDto {
    private Long id;
    private String question;
    private String difficulty;
    private Long materialId;
    private String materialTitle;
    private String topic;  // 질문 주제
}

