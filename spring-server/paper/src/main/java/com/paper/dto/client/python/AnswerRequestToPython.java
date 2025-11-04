package com.paper.dto.client.python;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.paper.domain.Problem;
import com.paper.dto.client.ProblemAnswerRequest;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AnswerRequestToPython {

    @JsonProperty("problem")
    private ProblemDto problem;

    @JsonProperty("user_answer")
    private String userAnswer;

    @Getter
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ProblemDto {

        @JsonProperty("question")
        private String question;

        @JsonProperty("answer")
        private String answer;

        @JsonProperty("hints")
        private List<String> hints;

        @JsonProperty("difficulty_score")
        private Integer difficultyScore;

        @JsonProperty("problem_type")
        private String problemType;

        @JsonProperty("test_cases")
        private List<Map<String, String>> testCases;

        private static AnswerRequestToPython.ProblemDto from(Problem problem) {
            return AnswerRequestToPython.ProblemDto.builder()
                    .question(problem.getQuestion())
                    .answer(problem.getAnswer())
                    .hints(problem.getHints())
                    .difficultyScore(problem.getDifficulty().ordinal())
                    .problemType(problem.getProblemType())
                    .testCases(problem.getTestCases())
                    .build();
        }
    }

    public static AnswerRequestToPython from(Problem problem, ProblemAnswerRequest answer) {

        ProblemDto problemDto = ProblemDto.from(problem);

        return AnswerRequestToPython.builder()
                .problem(problemDto)
                .userAnswer(answer.getAnswer())
                .build();
    }

}
