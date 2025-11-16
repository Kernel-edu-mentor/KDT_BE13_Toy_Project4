package com.paper.service;

import com.paper.config.error.ErrorCode;
import com.paper.config.error.exceprion.BusinessException;
import com.paper.domain.Material;
import com.paper.domain.QAChat;
import com.paper.domain.QASession;
import com.paper.domain.User;
import com.paper.dto.client.ProblemQARequest;
import com.paper.dto.client.QASessionResponse;
import com.paper.dto.client.python.KeywordRequestToPython;
import com.paper.dto.client.python.MaterialUploadRequest;
import com.paper.repository.QAChatRepository;
import com.paper.repository.QARepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Slf4j
@Service
@Transactional
@RequiredArgsConstructor
public class QAService {

    private final QAChatRepository qaChatRepository;
    private final QARepository qaRepository;
    private final MaterialService materialService;
    private final UserService userService;

    private void validateChatOwnership(QAChat chat, Long userId) {
        if (!chat.getUser().getId().equals(userId)) {
            throw new BusinessException(ErrorCode.CHAT_ACCESS_DENIED);
        }
    }

    private void validateMaterialOwnership(Material material, Long userId) {
        if (!material.getUploadedBy().getId().equals(userId)) {
            throw new BusinessException(ErrorCode.MATERIAL_ACCESS_DENIED);
        }
    }

    public void saveSession(Long userId, MaterialUploadRequest.QARequest request, MaterialUploadRequest.QAResponse response) {

        Material material = materialService.findById(request.getMaterialId());
        User user = userService.findById(userId);

        QAChat chat = null;
        if (request.getChatId() != null) {
            chat = qaChatRepository.findById(request.getChatId())
                    .orElseThrow(() -> new BusinessException(ErrorCode.CHAT_NOT_FOUND));
        }

        QASession qaSession = QASession.builder()
                .user(user)
                .material(material)
                .chat(chat)
                .question(request.getQuestion())
                .answer(response.getAnswer())
                .sources(response.getSources())
                .responseTimeMs(response.getResponseTimeMs())
                .build();

        qaRepository.save(qaSession);

    }

    @Transactional(readOnly = true)
    public List<QASessionResponse> getSessions(Long materialId, Long chatId, Long userId) {
        List<QASession> sessions;

        if (chatId != null) {
            QAChat chat = qaChatRepository.findById(chatId)
                    .orElseThrow(() -> new BusinessException(ErrorCode.CHAT_NOT_FOUND));
            validateChatOwnership(chat, userId);
            sessions = qaRepository.findByChatIdOrderByCreatedAtAsc(chatId);
        } else if (materialId != null) {
            Material material = materialService.findById(materialId);
            validateMaterialOwnership(material, userId);
            sessions = qaRepository.findByMaterialIdOrderByCreatedAtDesc(materialId);
        } else {
            sessions = qaRepository.findByUserIdOrderByCreatedAtDesc(userId);
        }

        return sessions.stream()
                .map(QASessionResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public KeywordRequestToPython getQAHistory(ProblemQARequest request, Long userId) {
        if (request.getChatId() == null) {
            throw new IllegalArgumentException("chatId는 필수입니다.");
        }

        QAChat chat = qaChatRepository.findById(request.getChatId())
                .orElseThrow(() -> new BusinessException(ErrorCode.CHAT_NOT_FOUND));
        validateChatOwnership(chat, userId);

        List<QASession> sessions = qaRepository.findByUserIdAndChatIdByCreatedAtDesc(userId, request.getChatId());

        if (sessions.isEmpty()) {
            throw new BusinessException(ErrorCode.QA_SESSION_NOT_FOUND);
        }

        return KeywordRequestToPython.from(sessions);
    }
}
