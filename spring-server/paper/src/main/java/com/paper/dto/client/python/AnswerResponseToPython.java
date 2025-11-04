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
public class AnswerResponseToPython {


    @JsonProperty("is_correct")
    private Boolean isCorrect;

    private Integer score;

    private String feedback;

    @JsonProperty("correct_answer")
    private String correctAnswer;               // 오답일 경우만 표시

    @JsonProperty("similarity_score")
    private Double similarityScore;             // SHORT_ANSWER용 의미 유사도

    @JsonProperty("rubric_scores")
    private Map<String, Object> rubricScores;       // CODING용 루브릭 점수

    @JsonProperty("test_results")
    private List<Map<String, Object>> testResults;   // CODING용 테스트 결과

    @JsonProperty("response_time_ms")
    private Integer responseTimeMs;

}
