package com.paper.dto.client;

import lombok.*;

import java.util.List;

@Getter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class QAResponse {

    private String answer;
    private List<Source> sources;
    private Integer responseTimeMs;

    @Getter
    public static class Source {
        private Integer page;
    }
}
