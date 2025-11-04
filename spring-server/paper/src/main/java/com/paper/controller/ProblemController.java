package com.paper.controller;

import com.paper.client.PythonClient;
import com.paper.dto.client.ProblemAnswerRequest;
import com.paper.dto.client.ProblemRequest;
import com.paper.dto.client.ProblemResponse;
import com.paper.dto.client.python.AnswerRequestToPython;
import com.paper.dto.client.python.AnswerResponseToPython;
import com.paper.dto.client.python.ProblemRequestToPython;
import com.paper.service.ProblemService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@Slf4j
@RestController
@RequestMapping("/api/problems")
@RequiredArgsConstructor
public class ProblemController {

    private final PythonClient pythonClient;
    private final ProblemService problemService;

    @PostMapping("/generated")
    public Mono<ResponseEntity<ProblemResponse>> generatedProblems(@RequestBody ProblemRequest request
                                  //@AuthenticationPrincipal UserDetails userDetails  // TODO : 추후 실제 회원정보 연결
                                                                                    ) {

        log.info("User {} generating {} {} problems for material {}", "testUser", request.getProblemCount(), request.getDifficulty(), request.getMaterialId());

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
