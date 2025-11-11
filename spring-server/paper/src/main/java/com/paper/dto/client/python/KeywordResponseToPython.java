package com.paper.dto.client.python;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;

import java.util.List;

@Getter
@AllArgsConstructor
public class KeywordResponseToPython {

    private List<String> keywords;

    @JsonProperty("response_time_ms")
    private int responseTimeMs;

}
