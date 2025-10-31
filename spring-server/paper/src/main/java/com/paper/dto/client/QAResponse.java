package com.paper.dto.client;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

import java.util.List;

@Getter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class QAResponse {

    @JsonProperty("answer")
    private String answer;

    @JsonProperty("sources")
    private List<Source> sources;

    @JsonProperty("response_time_ms")
    private Integer responseTimeMs;

 /*   @JsonProperty("file_type")
    private String fineType;*/

    @Getter
    public static class Source {
        private Integer page;
        private String excerpt;
    }
}
