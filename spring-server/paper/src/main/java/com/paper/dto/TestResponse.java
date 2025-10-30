package com.paper.dto;

import lombok.*;

@Getter
@NoArgsConstructor
@AllArgsConstructor
public class TestResponse {

    private String service;
    private String version;
    private Endpoints endpoints;

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Endpoints {
        private String qa;
        private String problems;
        private String docs;
    }
}
