package com.paper.dto.client.python;

import com.fasterxml.jackson.annotation.JsonProperty;
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
public class ProblemResponseToPython {

    @JsonProperty("problems")
    private List<ProblemDto> problems;

    @JsonProperty("difficulty")
    private String difficulty;

    @JsonProperty("generated_count")
    private Integer generatedCount;

    @JsonProperty("rejected_count")
    private Integer rejectedCount;

    @JsonProperty("response_time_ms")
    private Integer responseTimeMs;

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
    }
}
