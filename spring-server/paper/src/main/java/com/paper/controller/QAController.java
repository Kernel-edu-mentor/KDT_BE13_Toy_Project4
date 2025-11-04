package com.paper.controller;

import com.paper.client.PythonClient;
import com.paper.dto.client.QARequest;
import com.paper.dto.client.QAResponse;
import com.paper.service.QAService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
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
    public Mono<ResponseEntity<QAResponse>> askQuestion (
            @Valid @RequestBody QARequest request
            //@AuthenticationPrincipal UserDetails userDetails
    ) {

        log.info("User {} ask question for material {}: {}", "testuser", request.getMaterialId(), request.getQuestion());

        return pythonClient.askQuestion(request)
                .doOnSuccess(response -> {
                    // DB에 저장 (비동기)
                    qaService.saveSession("testuser", request, response);
                    log.info("QA response saved successfully");
                })
                .map(ResponseEntity::ok)
                .onErrorResume(error -> {
                    log.error("QA error: {}", error.getMessage(), error);
                    
                    // 에러 메시지 생성
                    String errorMessage;
                    if (error.getMessage() != null && error.getMessage().contains("Connection refused")) {
                        errorMessage = "AI 서버에 연결할 수 없습니다. Python 서버가 실행 중인지 확인해주세요.";
                    } else if (error.getMessage() != null && error.getMessage().contains("timeout")) {
                        errorMessage = "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.";
                    } else {
                        errorMessage = "죄송합니다. 질문에 대한 답변을 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
                    }
                    
                    // 에러 응답 생성 (QAResponse 형식으로)
                    QAResponse errorResponse = QAResponse.builder()
                            .answer(errorMessage)
                            .responseTimeMs(0)
                            .build();
                    
                    return Mono.just(ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse));
                });
    }
}
