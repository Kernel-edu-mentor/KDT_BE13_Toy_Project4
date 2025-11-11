package com.paper.dto.client.python;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.paper.dto.client.ProblemQARequest;
import com.paper.dto.client.ProblemRequest;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProblemRequestToPython {

    @JsonProperty("material_id")
    private Long materialId;

    @JsonProperty("difficulty")
    private String difficulty;  // BEGINNER, INTERMEDIATE, ADVANCED

    @JsonProperty("problem_count")
    private Integer problemCount;

    @JsonProperty("learning_description")
    @Builder.Default
    private String learningDescription = null;

    @JsonProperty("learning_topics")
    @Builder.Default
    private List<String> learningTopics = null;

    public static ProblemRequestToPython from(ProblemQARequest problemRequest, KeywordResponseToPython topic) {
        return ProblemRequestToPython.builder()
                .materialId(problemRequest.getMaterialId())
                .difficulty(problemRequest.getDifficulty())
                .problemCount(problemRequest.getProblemCount())
                .learningTopics(topic.getKeywords())
                .build();
    }

    public static ProblemRequestToPython from(ProblemRequest problemRequest) {
        return ProblemRequestToPython.builder()
                .materialId(problemRequest.getMaterialId())
                .difficulty(problemRequest.getDifficulty())
                .problemCount(problemRequest.getProblemCount())
                .learningDescription(problemRequest.getLearningDescription())
                .build();
    }
}
