package com.paper.domain;

import com.paper.config.converter.SourceListConverter;
import com.paper.dto.client.QAResponse;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;

import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "qa_sessions")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class QASession {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "material_id")
    private Material material;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String question;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String answer;

    @Convert(converter = SourceListConverter.class) // 컨버터 지정
    @Column(columnDefinition = "JSONB")
    private List<QAResponse.Source> sources;  // JSON 형태로 저장

    private Integer responseTimeMs;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;
}