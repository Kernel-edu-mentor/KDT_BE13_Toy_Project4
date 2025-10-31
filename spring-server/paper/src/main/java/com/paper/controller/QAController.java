package com.paper.controller;

import com.paper.client.PythonClient;
import com.paper.dto.client.QARequest;
import com.paper.dto.client.QAResponse;
import com.paper.service.QAService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

@Slf4j
@RestController
@RequestMapping("/api/qa")
@RequiredArgsConstructor
public class QAController {

    private final PythonClient pythonClient;
    private final QAService qaService;

    @PostMapping("/ask")
    public Mono<ResponseEntity<QAResponse>> askQuestion (@RequestBody QARequest request
                                                         //@AuthenticationPrincipal UserDetails userDetails
                                                        ) {

        log.info("User {} ask question for material {}", "testuser", request.getMaterialId());

        return pythonClient.askQuestion(request)
                .doOnSuccess(response -> {
                    // DB에 저장 (비동기)
                    qaService.saveSession("testuser", request, response);
                })
                .map(ResponseEntity::ok)
                .onErrorResume(error -> {
                    log.error("QA error: {}", error.getMessage());
                    return Mono.just(ResponseEntity.internalServerError().build());
                });
    }
}
