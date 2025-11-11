package com.paper.dto.client;

import com.paper.domain.Problem;
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

    public static ProblemListDto from(Problem problem) {

        return ProblemListDto.builder()
                .id(problem.getId())
                .question(problem.getQuestion())
                .difficulty(problem.getDifficulty().name())
                .materialId(problem.getMaterial() != null ? problem.getMaterial().getId() : null)
                .materialTitle(problem.getMaterial() != null ? problem.getMaterial().getTitle() : null)
                .topic(problem.getTopic())
                .build();
    }
}

