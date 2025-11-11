package com.paper.service;

import com.paper.domain.Material;
import com.paper.domain.Problem;
import com.paper.dto.client.ProblemAnswerRequest;
import com.paper.dto.client.ProblemListDto;
import com.paper.dto.client.ProblemRequest;
import com.paper.dto.client.ProblemResponse;
import com.paper.dto.client.python.AnswerRequestToPython;
import com.paper.dto.client.python.ProblemResponseToPython;
import com.paper.repository.ProblemRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@Transactional
@RequiredArgsConstructor
public class ProblemService {

    private final ProblemRepository problemRepository;
    private final MaterialService materialService;

    // saveProblems 메서드를 Mono를 반환하는 Reactive 메서드로 변경
    public Mono<Void> saveProblems(ProblemRequest request, ProblemResponseToPython response) {
        return saveProblemsInternal(request.getMaterialId(), response, request.getTopic());
    }


    @Transactional(readOnly = true)
    public List<ProblemListDto> findAllByDifficulty(String difficulty, String topic) {
        Problem.Difficulty difficultyEnum = Problem.Difficulty.valueOf(difficulty.toUpperCase());
        return problemRepository.findByDifficultyOrderByCreatedAtDesc(difficultyEnum).stream()
                .filter(problem -> topic == null || topic.isEmpty() || (problem.getTopic() != null && problem.getTopic().equals(topic)))
                .map(ProblemListDto::from)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public List<ProblemListDto> findAllByMaterialAndDifficulty(Long materialId, String difficulty, String topic) {
        Material material = materialService.findById(materialId);
        Problem.Difficulty difficultyEnum = Problem.Difficulty.valueOf(difficulty.toUpperCase());
        return problemRepository.findByMaterialAndDifficultyOrderByCreatedAtDesc(material, difficultyEnum).stream()
                .filter(problem -> topic == null || topic.isEmpty() || (problem.getTopic() != null && problem.getTopic().equals(topic)))
                .map(ProblemListDto::from)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public List<String> findAllTopics() {
        return problemRepository.findAll().stream()
                .map(Problem::getTopic)
                .filter(topic -> topic != null && !topic.isEmpty())
                .distinct()
                .collect(Collectors.toList());
    }

    // QA 기반 문제 생성 시 키워드를 topic으로 저장하는 메서드
    public Mono<Void> saveProblemsWithKeywords(Long materialId, ProblemResponseToPython response, List<String> keywords) {
        String topic = keywords != null && !keywords.isEmpty() ? String.join(", ", keywords) : null;
        return saveProblemsInternal(materialId, response, topic);
    }

    public AnswerRequestToPython getRequestAnswer(Long id, ProblemAnswerRequest request) {
        Problem problem = findById(id);
        return AnswerRequestToPython.from(problem, request);
    }

    private Problem findById(Long id) {
        return problemRepository.findById(id).orElseThrow(() -> new IllegalArgumentException("데이터 조회 실패"));
    }

    // 공통 문제 저장 로직
    private Mono<Void> saveProblemsInternal(Long materialId, ProblemResponseToPython response, String topic) {
        return Mono.fromCallable(() -> {
                    Material material = materialService.findById(materialId);
                    ProblemResponse problemResponse = ProblemResponse.from(response);

                    List<Problem> problems = createProblemsWithTopic(material, response, problemResponse, topic);

                    problemRepository.saveAll(problems);
                    log.info("Saved {} problems{} for material {} on thread {}",
                        response.getGeneratedCount(),
                        topic != null ? " with topic '" + topic + "'" : "",
                        materialId,
                        Thread.currentThread().getName());
                    return null;
                })
                .subscribeOn(Schedulers.boundedElastic())
                .then();
    }

    // Problem 리스트 생성 로직
    private List<Problem> createProblemsWithTopic(Material material, ProblemResponseToPython response,
                                                   ProblemResponse problemResponse, String topic) {
        return problemResponse.getProblems().stream()
                .map(problemDto -> {
                    Problem problem = Problem.from(material, response.getDifficulty(), problemDto);
                    return setTopicIfPresent(problem, topic);
                })
                .toList();
    }

    // topic 설정 로직
    private Problem setTopicIfPresent(Problem problem, String topic) {
        if (topic == null) {
            return problem;
        }

        return Problem.from(problem, topic);
    }
}
