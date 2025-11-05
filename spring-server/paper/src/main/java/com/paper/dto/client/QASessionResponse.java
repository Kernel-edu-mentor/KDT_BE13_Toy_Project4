package com.paper.dto.client;

import com.paper.domain.QASession;
import com.paper.dto.client.python.MaterialUploadRequest;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class QASessionResponse {

    private Long id;
    private Long materialId;
    private String materialTitle;
    private Long chatId;
    private String question;
    private String answer;
    private Integer responseTimeMs;
    private List<MaterialUploadRequest.QAResponse.Source> sources;
    private LocalDateTime createdAt;

    public static QASessionResponse from(QASession session) {
        return QASessionResponse.builder()
                .id(session.getId())
                .materialId(session.getMaterial() != null ? session.getMaterial().getId() : null)
                .materialTitle(session.getMaterial() != null ? session.getMaterial().getTitle() : null)
                .chatId(session.getChat() != null ? session.getChat().getId() : null)
                .question(session.getQuestion())
                .answer(session.getAnswer())
                .responseTimeMs(session.getResponseTimeMs())
                .sources(session.getSources())
                .createdAt(session.getCreatedAt())
                .build();
    }
}
