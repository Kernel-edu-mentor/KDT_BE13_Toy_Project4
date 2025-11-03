package com.paper.domain;

import com.paper.dto.client.ProblemResponse;
import com.paper.dto.client.python.ProblemResponseToPython;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Entity
@Table(name = "practice_problems")
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Problem {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "material_id")
    private Material material;

    @Column(nullable = false, length = 20)
    @Enumerated(EnumType.STRING)
    private Difficulty difficulty;

    @Column(length = 50)
    private String problemType;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String question;

    @Column(columnDefinition = "TEXT")
    private String answer;

    @JdbcTypeCode(SqlTypes.JSON)
    private List<String> hints;

    @JdbcTypeCode(SqlTypes.JSON)
    private List<Map<String, String>> testCases;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    public enum Difficulty {
        BEGINNER, INTERMEDIATE, ADVANCED
    }

    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
    }

    public static Problem from(Material material, String difficulty, ProblemResponse.ProblemDto problemDto) {
        return Problem.builder()
                .material(material)
                .difficulty(Difficulty.valueOf(difficulty.toUpperCase()))
                .problemType(problemDto.getProblemType())
                .question(problemDto.getQuestion())
                .answer(problemDto.getAnswer())
                .hints(problemDto.getHints())
                .testCases(problemDto.getTestCases())
                .build();
    }
}