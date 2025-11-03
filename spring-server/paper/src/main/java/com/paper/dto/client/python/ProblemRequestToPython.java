package com.paper.dto.client.python;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.paper.dto.client.ProblemRequest;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

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
    private String learningDescription;

    @JsonProperty("learning_topics")
    @Builder.Default
    private String learningTopics = null;

    public static ProblemRequestToPython from(ProblemRequest problemRequest) {
        return ProblemRequestToPython.builder()
                .materialId(problemRequest.getMaterialId())
                .difficulty(problemRequest.getDifficulty())
                .problemCount(problemRequest.getProblemCount())
                .learningDescription(problemRequest.getLearningDescription())
                .learningTopics(null)
                .build();
    }
}
