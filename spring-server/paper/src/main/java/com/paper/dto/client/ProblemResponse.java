package com.paper.dto.client;

import com.paper.dto.client.python.ProblemResponseToPython;
import lombok.*;

import java.util.List;
import java.util.Map;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProblemResponse {

    private List<ProblemDto> problems;
    private String difficulty;
    private Integer generatedCount;
    private Integer rejectedCount;
    private Integer responseTimeMs;

    @Getter
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ProblemDto {
        private String question;
        private String answer;
        private List<String> hints;
        private Integer difficultyScore;
        private String problemType;
        private List<Map<String, String>> testCases;

        private static ProblemDto fromProblem(ProblemResponseToPython.ProblemDto problemDto) {
            return ProblemDto.builder()
                    .question(problemDto.getQuestion())
                    .answer(problemDto.getAnswer())
                    .hints(problemDto.getHints())
                    .difficultyScore(problemDto.getDifficultyScore())
                    .problemType(problemDto.getProblemType())
                    .testCases(problemDto.getTestCases())
                    .build();
        }
    }

    public static ProblemResponse from(ProblemResponseToPython problem) {

        List<ProblemDto> problemDtos = problem.getProblems().stream()
                .map(ProblemDto::fromProblem)
                .toList();

        return ProblemResponse.builder()
                .problems(problemDtos)
                .difficulty(problem.getDifficulty())
                .generatedCount(problem.getGeneratedCount())
                .rejectedCount(problem.getRejectedCount())
                .responseTimeMs(problem.getResponseTimeMs())
                .build();
    }
    
}
