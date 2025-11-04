package com.paper.service;

import com.paper.domain.Material;
import com.paper.domain.Problem;
import com.paper.dto.client.ProblemAnswerRequest;
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
                            .map(problemDto -> Problem.from(material, response.getDifficulty(), problemDto))
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


    public AnswerRequestToPython getRequestAnswer(Long id, ProblemAnswerRequest request) {

        Problem problem = findById(id);
        return AnswerRequestToPython.from(problem, request);
    }

    private Problem findById(Long id) {
        return problemRepository.findById(id).orElseThrow(() -> new IllegalArgumentException("데이터 조회 실패"));
    }
}
