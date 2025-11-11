package com.paper.service;

import com.paper.domain.Material;
import com.paper.domain.QAChat;
import com.paper.domain.QASession;
import com.paper.domain.User;
import com.paper.dto.client.ProblemQARequest;
import com.paper.dto.client.QAChatResponse;
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
import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class QAService {

    private final QAChatRepository qaChatRepository;
    private final QARepository qaRepository;
    private final MaterialService materialService;
    private final UserService userService;

    public void saveSession(Long userId, MaterialUploadRequest.QARequest request, MaterialUploadRequest.QAResponse response) {

        Material material = materialService.findById(request.getMaterialId());
        User user = userService.findById(userId);

        QAChat chat = null;
        if (request.getChatId() != null) {
            chat = qaChatRepository.findById(request.getChatId())
                    .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 채팅입니다."));
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

    public List<QASessionResponse> getSessions(Long materialId, Long chatId, Long userId) {
        List<QASession> sessions;

        if (chatId != null) {
            // 채팅방 소유자 확인
            QAChat chat = qaChatRepository.findById(chatId)
                    .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 채팅입니다."));

            if (!chat.getUser().getId().equals(userId)) {
                throw new IllegalArgumentException("해당 채팅에 접근할 권한이 없습니다.");
            }

            sessions = qaRepository.findByChatIdOrderByCreatedAtAsc(chatId);
        } else if (materialId != null) {
            // 자료 업로더 확인
            Material material = materialService.findById(materialId);

            if (!material.getUploadedBy().getId().equals(userId)) {
                throw new IllegalArgumentException("해당 자료에 접근할 권한이 없습니다.");
            }

            sessions = qaRepository.findByMaterialIdOrderByCreatedAtDesc(materialId);
        } else {
            // 자신의 모든 세션만 조회
            sessions = qaRepository.findByUserIdOrderByCreatedAtDesc(userId);
        }

        return sessions.stream()
                .map(QASessionResponse::from)
                .toList();
    }

    public QAChatResponse createChat(String title, Long materialId, Long userId) {
        Material material = materialService.findById(materialId);

        User user = userService.findById(userId);

        QAChat chat = QAChat.builder()
                .title(title)
                .material(material)
                .user(user)
                .build();

        QAChat saved = qaChatRepository.save(chat);
        return QAChatResponse.from(saved);
    }

    public List<QAChatResponse> getChats(Optional<Long> materialId, Long userId) {
        List<QAChat> chats;

        if (materialId.isPresent()) {
            chats = qaChatRepository.findByMaterialIdAndUserId(materialId.get(), userId);
        } else {
            chats = qaChatRepository.findByUserId(userId);
        }

        return chats.stream()
                .map(QAChatResponse::from)
                .toList();
    }

    public QAChatResponse updateChatTitle(Long chatId, String title, Long userId) {
        QAChat chat = qaChatRepository.findById(chatId)
                .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 채팅입니다."));

        if (!chat.getUser().getId().equals(userId))
            throw new IllegalArgumentException("회원 정보가 일치하지 않습니다.");

        chat.setTitle(title);
        QAChat saved = qaChatRepository.save(chat);
        return QAChatResponse.from(saved);
    }

    @Transactional
    public void deleteChat(Long chatId, Long userId) {

        QAChat chat = qaChatRepository.findById(chatId)
                .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 채팅입니다."));

        if (! chat.getUser().getId().equals(userId)) {
            throw new IllegalArgumentException("회원 정보가 일치하지 않습니다.");
        }

        qaRepository.deleteByChatId(chatId);
        qaChatRepository.delete(chat);
    }

    @Transactional(readOnly = true)
    public KeywordRequestToPython getQAHistory(ProblemQARequest request, Long userId) {

        if (request.getChatId() == null) {
            throw new IllegalArgumentException("chatId는 필수입니다.");
        }

        // chatId 소유자 확인
        QAChat chat = qaChatRepository.findById(request.getChatId())
                .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 채팅입니다."));

        if (!chat.getUser().getId().equals(userId)) {
            throw new IllegalArgumentException("해당 채팅에 접근할 권한이 없습니다.");
        }

        List<QASession> sessions = qaRepository.findByUserIdAndChatIdByCreatedAtDesc(userId, request.getChatId());

        if (sessions.isEmpty()) {
            throw new IllegalArgumentException("해당 채팅에 QA 세션이 없습니다.");
        }

        return KeywordRequestToPython.from(sessions);

    }
}
