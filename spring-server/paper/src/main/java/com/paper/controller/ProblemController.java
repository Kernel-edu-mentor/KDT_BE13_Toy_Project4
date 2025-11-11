package com.paper.controller;

import com.paper.client.PythonClient;
import com.paper.dto.client.*;
import com.paper.dto.client.python.*;
import com.paper.security.UserPrincipal;
import com.paper.service.ProblemService;
import com.paper.service.QAService;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.List;

@Slf4j
@RestController
@RequestMapping("/api/problems")
@RequiredArgsConstructor
public class ProblemController {

    private final PythonClient pythonClient;
    private final ProblemService problemService;
    private final QAService qaService;

    /**
     * 질문 내용 기반 문제 생성
     */
    @PostMapping("/generated/qa")
    public Mono<ResponseEntity<ProblemResponse>> generateProblemWithQA(@RequestBody ProblemQARequest request,
                                                                        @AuthenticationPrincipal UserPrincipal userPrincipal) {

        log.info("User {} generating QA-based {} problems for material {}",
                userPrincipal.getUsername(),
                request.getProblemCount(),
                request.getMaterialId()
        );

        KeywordRequestToPython getKeywordRequest = qaService.getQAHistory(request, userPrincipal.getId());

        return pythonClient.getKeyword(getKeywordRequest)
                .flatMap(keywordResponse -> {
                    // 키워드를 포함하여 문제 생성 요청
                    return pythonClient.generateProblems(ProblemRequestToPython.from(request, keywordResponse))
                            .flatMap(problemResponse -> {
                                // 키워드를 topic으로 저장
                                return problemService.saveProblemsWithKeywords(request.getMaterialId(), problemResponse, keywordResponse.getKeywords())
                                        .thenReturn(problemResponse);
                            });
                })
                .map(ProblemResponse::from)
                .map(ResponseEntity::ok)
                .onErrorResume(error -> {
                    log.error("QA-based problems generation failed", error);
                    return Mono.just(ResponseEntity.internalServerError().build());
                });
    }

    @PostMapping("/generated")
    public Mono<ResponseEntity<ProblemResponse>> generatedProblems(@RequestBody ProblemRequest request,
                                                                   @AuthenticationPrincipal UserPrincipal userPrincipal
                                                                   ) {

        log.info("User {} generating {} {} problems for material {}",
                userPrincipal.getUsername(),
                request.getProblemCount(),
                request.getDifficulty(),
                request.getMaterialId()
        );

        return pythonClient.generateProblems(ProblemRequestToPython.from(request))
                .flatMap(response -> {
                    return problemService.saveProblems(request, response)
                            .thenReturn(response);
                })
                .map(ProblemResponse::from)
                .map(ResponseEntity::ok)
                .onErrorResume(error -> {
                    log.error("Problems generation failed", error.getCause());
                    return Mono.just(ResponseEntity.internalServerError().build());
                });
    }

    @GetMapping("/list")
    public ResponseEntity<List<ProblemListDto>> getProblems(
            @RequestParam(required = false, defaultValue = "BEGINNER") String difficulty,
            @RequestParam(required = false) Long materialId,
            @RequestParam(required = false) String topic
    ) {
        log.info("Fetching problems with difficulty: {}, materialId: {}, topic: {}", difficulty, materialId, topic);
        List<ProblemListDto> problems;
        if (materialId != null) {
            problems = problemService.findAllByMaterialAndDifficulty(materialId, difficulty, topic);
        } else {
            problems = problemService.findAllByDifficulty(difficulty, topic);
        }
        return ResponseEntity.ok(problems);
    }

    @GetMapping("/topics")
    public ResponseEntity<List<String>> getTopics() {
        log.info("Fetching all topics");
        List<String> topics = problemService.findAllTopics();
        return ResponseEntity.ok(topics);
    }

    @PostMapping("/answer/{id}")
    public Mono<ResponseEntity<AnswerResponseToPython>> checkAnswer(@PathVariable("id") Long id,
                                                                    @RequestBody ProblemAnswerRequest request) {

        AnswerRequestToPython requestAnswer = problemService.getRequestAnswer(id, request);

        return pythonClient.checkAnswer(requestAnswer)
                .map(ResponseEntity::ok)
                .onErrorResume(error -> {
                    log.error("Problems check-answer failed", error.getCause());
                    return Mono.just(ResponseEntity.internalServerError().build());
                });
    }
}
