package com.paper.dto.client;

import com.paper.domain.QAChat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class QAChatResponse {

    private Long id;
    private String title;
    private Long materialId;
    private String materialTitle;
    private LocalDateTime createdAt;

    public static QAChatResponse from(QAChat chat) {
        return QAChatResponse.builder()
                .id(chat.getId())
                .title(chat.getTitle())
                .materialId(chat.getMaterial() != null ? chat.getMaterial().getId() : null)
                .materialTitle(chat.getMaterial() != null ? chat.getMaterial().getTitle() : null)
                .createdAt(chat.getCreatedAt())
                .build();
    }
}
