package com.paper.dto.client.python;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.paper.domain.QASession;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class KeywordRequestToPython {

    private List<String> questions;

    @JsonProperty("max_keywords")
    @Builder.Default
    private int maxKeywords = 5;

    public static KeywordRequestToPython from(List<QASession> qaSession) {

        List<String> list = qaSession.stream()
                .map(QASession::getQuestion)
                .toList();

        return KeywordRequestToPython.builder()
                .questions(list)
                .build();
    }
}
