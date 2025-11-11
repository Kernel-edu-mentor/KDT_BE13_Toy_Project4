package com.paper.controller;

import com.paper.client.PythonClient;
import com.paper.dto.client.QAChatCreateRequest;
import com.paper.dto.client.QAChatResponse;
import com.paper.dto.client.QAChatUpdateRequest;
import com.paper.dto.client.QASessionResponse;
import com.paper.dto.client.python.MaterialUploadRequest;
import com.paper.security.UserPrincipal;
import com.paper.service.QAService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Optional;
import reactor.core.publisher.Mono;

@Slf4j
@RestController
@RequestMapping("/api/qa")
@RequiredArgsConstructor
public class QAController {

    private final PythonClient pythonClient;
    private final QAService qaService;

    @GetMapping("/sessions")
    public ResponseEntity<List<QASessionResponse>> getSessions(
            @RequestParam(value = "materialId", required = false) Long materialId,
            @RequestParam(value = "chatId", required = false) Long chatId,
            @AuthenticationPrincipal UserPrincipal userPrincipal
            ) {
        Long userId = userPrincipal.getId();

        List<QASessionResponse> sessions = qaService.getSessions(materialId, chatId, userId);
        return ResponseEntity.ok(sessions);
    }

    @GetMapping("/chats")
    public ResponseEntity<List<QAChatResponse>> getChats(
            @RequestParam(value = "materialId", required = false) Long materialId,
            @AuthenticationPrincipal UserPrincipal userPrincipal
    ) {
        Long userId = userPrincipal.getId();

        List<QAChatResponse> chats = qaService.getChats(Optional.ofNullable(materialId), userId);
        return ResponseEntity.ok(chats);
    }

    @PostMapping("/chats")
    public ResponseEntity<QAChatResponse> createChat(
            @Valid @RequestBody QAChatCreateRequest request,
            @AuthenticationPrincipal UserPrincipal userPrincipal
    ) {
        Long userId = userPrincipal.getId();

        QAChatResponse chat = qaService.createChat(request.getTitle(), request.getMaterialId(), userId);
        return ResponseEntity.status(HttpStatus.CREATED).body(chat);
    }

    @PatchMapping("/chats/{chatId}")
    public ResponseEntity<QAChatResponse> updateChat(
            @PathVariable Long chatId,
            @Valid @RequestBody QAChatUpdateRequest request,
            @AuthenticationPrincipal UserPrincipal userPrincipal
    ) {
        QAChatResponse chat = qaService.updateChatTitle(chatId, request.getTitle(), userPrincipal.getId());
        return ResponseEntity.ok(chat);
    }

    @GetMapping("/chats/{chatId}/sessions")
    public ResponseEntity<List<QASessionResponse>> getChatSessions(@PathVariable Long chatId,
                                                                   @AuthenticationPrincipal UserPrincipal userPrincipal) {

        List<QASessionResponse> sessions = qaService.getSessions(null, chatId, userPrincipal.getId());
        return ResponseEntity.ok(sessions);
    }

    @DeleteMapping("/chats/{chatId}")
    public ResponseEntity<Void> deleteChat(@PathVariable Long chatId, @AuthenticationPrincipal UserPrincipal userPrincipal) {
        qaService.deleteChat(chatId, userPrincipal.getId());
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/ask")
    public Mono<ResponseEntity<MaterialUploadRequest.QAResponse>> askQuestion (
            @Valid @RequestBody MaterialUploadRequest.QARequest request,
            @AuthenticationPrincipal UserPrincipal userPrincipal
    ) {

        log.info("User {} ask question for material {}: {}", userPrincipal.getId(), request.getMaterialId(), request.getQuestion());

        return pythonClient.askQuestion(request)
                .doOnSuccess(response -> {
                    // DB에 저장 (비동기)
                    qaService.saveSession(userPrincipal.getId(), request, response);
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
                    MaterialUploadRequest.QAResponse errorResponse = MaterialUploadRequest.QAResponse.builder()
                            .answer(errorMessage)
                            .responseTimeMs(0)
                            .build();
                    
                    return Mono.just(ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse));
                });
    }
}
