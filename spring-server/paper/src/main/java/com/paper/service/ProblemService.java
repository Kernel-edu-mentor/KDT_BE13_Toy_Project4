package com.paper.service;

import com.paper.domain.Material;
import com.paper.domain.Problem;
import com.paper.dto.client.ProblemAnswerRequest;
import com.paper.dto.client.ProblemListDto;
import com.paper.dto.client.ProblemQARequest;
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

        // 1. Mono.fromCallable로 블로킹 코드를 감싼다.
        return Mono.fromCallable(() -> {

                    // 이 블록 내의 모든 코드는 별도의 스레드(boundedElastic)에서 실행.
                    // 1. Material 조회 (블로킹 I/O)
                    Material material = materialService.findById(request.getMaterialId());
                    // 2. DTO 변환
                    ProblemResponse problemResponse = ProblemResponse.from(response);
                    // 3. Problem 엔티티 리스트로 변환
                    List<Problem> problems = problemResponse.getProblems().stream()
                            .map(problemDto -> {
                                Problem problem = Problem.from(material, response.getDifficulty(), problemDto);

                                // QA 기반 생성인 경우 topic 설정
                                if (request.getTopic() != null) {
                                    problem = Problem.builder()
                                            .id(problem.getId())
                                            .material(problem.getMaterial())
                                            .difficulty(problem.getDifficulty())
                                            .problemType(problem.getProblemType())
                                            .question(problem.getQuestion())
                                            .answer(problem.getAnswer())
                                            .hints(problem.getHints())
                                            .testCases(problem.getTestCases())
                                            .topic(request.getTopic())
                                            .createdAt(problem.getCreatedAt())
                                            .build();
                                }
                                return problem;
                            })
                            .toList();
                    // 4. 배치 저장을 위해 saveAll 사용 (N+1 방지)
                    problemRepository.saveAll(problems); // <-- saveAll 사용

                    log.info("Saved {} problems for material {} on thread {}", response.getGeneratedCount(), request.getMaterialId(), Thread.currentThread().getName());
                    return null; // Callable이 반환하는 값은 없으므로 null 반환
                })
                // 2. 반드시 별도의 스케줄러(I/O 전용 스레드 풀)를 지정.
                .subscribeOn(Schedulers.boundedElastic())
                // 3. 최종적으로 Mono<Void>로 변환하여 반환/
                .then();
    }


    @Transactional(readOnly = true)
    public List<ProblemListDto> findAllByDifficulty(String difficulty, String topic) {
        Problem.Difficulty difficultyEnum = Problem.Difficulty.valueOf(difficulty.toUpperCase());
        return problemRepository.findByDifficultyOrderByCreatedAtDesc(difficultyEnum).stream()
                .filter(problem -> topic == null || topic.isEmpty() || (problem.getTopic() != null && problem.getTopic().equals(topic)))
                .map(problem -> ProblemListDto.builder()
                        .id(problem.getId())
                        .question(problem.getQuestion())
                        .difficulty(problem.getDifficulty().name())
                        .materialId(problem.getMaterial() != null ? problem.getMaterial().getId() : null)
                        .materialTitle(problem.getMaterial() != null ? problem.getMaterial().getTitle() : null)
                        .topic(problem.getTopic())
                        .build())
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public List<ProblemListDto> findAllByMaterialAndDifficulty(Long materialId, String difficulty, String topic) {
        Material material = materialService.findById(materialId);
        Problem.Difficulty difficultyEnum = Problem.Difficulty.valueOf(difficulty.toUpperCase());
        return problemRepository.findByMaterialAndDifficultyOrderByCreatedAtDesc(material, difficultyEnum).stream()
                .filter(problem -> topic == null || topic.isEmpty() || (problem.getTopic() != null && problem.getTopic().equals(topic)))
                .map(problem -> ProblemListDto.builder()
                        .id(problem.getId())
                        .question(problem.getQuestion())
                        .difficulty(problem.getDifficulty().name())
                        .materialId(problem.getMaterial() != null ? problem.getMaterial().getId() : null)
                        .materialTitle(problem.getMaterial() != null ? problem.getMaterial().getTitle() : null)
                        .topic(problem.getTopic())
                        .build())
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
    public Mono<Void> saveProblemsWithKeywords(ProblemRequest request, ProblemResponseToPython response, List<String> keywords) {
        return Mono.fromCallable(() -> {
                    Material material = materialService.findById(request.getMaterialId());
                    ProblemResponse problemResponse = ProblemResponse.from(response);

                    // 키워드 리스트를 하나의 문자열로 결합 (예: "Java, Spring, REST API")
                    String topic = keywords != null && !keywords.isEmpty()
                        ? String.join(", ", keywords)
                        : null;

                    List<Problem> problems = problemResponse.getProblems().stream()
                            .map(problemDto -> {
                                Problem problem = Problem.from(material, response.getDifficulty(), problemDto);

                                // topic 설정
                                if (topic != null) {
                                    problem = Problem.builder()
                                            .id(problem.getId())
                                            .material(problem.getMaterial())
                                            .difficulty(problem.getDifficulty())
                                            .problemType(problem.getProblemType())
                                            .question(problem.getQuestion())
                                            .answer(problem.getAnswer())
                                            .hints(problem.getHints())
                                            .testCases(problem.getTestCases())
                                            .topic(topic)
                                            .createdAt(problem.getCreatedAt())
                                            .build();
                                }
                                return problem;
                            })
                            .toList();

                    problemRepository.saveAll(problems);
                    log.info("Saved {} problems with topic '{}' for material {}",
                        response.getGeneratedCount(), topic, request.getMaterialId());
                    return null;
                })
                .subscribeOn(Schedulers.boundedElastic())
                .then();
    }

    // QA 기반 문제 생성 시 키워드를 topic으로 저장하는 메서드 (ProblemQARequest 오버로드)
    public Mono<Void> saveProblemsWithKeywords(ProblemQARequest request, ProblemResponseToPython response, List<String> keywords) {
        return Mono.fromCallable(() -> {
                    Material material = materialService.findById(request.getMaterialId());
                    ProblemResponse problemResponse = ProblemResponse.from(response);

                    // 키워드 리스트를 하나의 문자열로 결합 (예: "Java, Spring, REST API")
                    String topic = keywords != null && !keywords.isEmpty()
                        ? String.join(", ", keywords)
                        : null;

                    List<Problem> problems = problemResponse.getProblems().stream()
                            .map(problemDto -> {
                                Problem problem = Problem.from(material, response.getDifficulty(), problemDto);

                                // topic 설정
                                if (topic != null) {
                                    problem = Problem.builder()
                                            .id(problem.getId())
                                            .material(problem.getMaterial())
                                            .difficulty(problem.getDifficulty())
                                            .problemType(problem.getProblemType())
                                            .question(problem.getQuestion())
                                            .answer(problem.getAnswer())
                                            .hints(problem.getHints())
                                            .testCases(problem.getTestCases())
                                            .topic(topic)
                                            .createdAt(problem.getCreatedAt())
                                            .build();
                                }
                                return problem;
                            })
                            .toList();

                    problemRepository.saveAll(problems);
                    log.info("Saved {} problems with topic '{}' for material {}",
                        response.getGeneratedCount(), topic, request.getMaterialId());
                    return null;
                })
                .subscribeOn(Schedulers.boundedElastic())
                .then();
    }

    public AnswerRequestToPython getRequestAnswer(Long id, ProblemAnswerRequest request) {
        Problem problem = findById(id);
        return AnswerRequestToPython.from(problem, request);
    }

    private Problem findById(Long id) {
        return problemRepository.findById(id).orElseThrow(() -> new IllegalArgumentException("데이터 조회 실패"));
    }
}
