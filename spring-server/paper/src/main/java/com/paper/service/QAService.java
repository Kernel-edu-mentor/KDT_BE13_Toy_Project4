package com.paper.service;

import com.paper.domain.Material;
import com.paper.domain.QAChat;
import com.paper.domain.QASession;
import com.paper.dto.client.QAChatResponse;
import com.paper.dto.client.QASessionResponse;
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

    public void saveSession(String testuser, MaterialUploadRequest.QARequest request, MaterialUploadRequest.QAResponse response) {

        Material material = materialService.findById(request.getMaterialId());

        QAChat chat = null;
        if (request.getChatId() != null) {
            chat = qaChatRepository.findById(request.getChatId())
                    .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 채팅입니다."));
        }

        QASession qaSession = QASession.builder()
                .material(material)
                .chat(chat)
                .question(request.getQuestion())
                .answer(response.getAnswer())
                .sources(response.getSources())
                .responseTimeMs(response.getResponseTimeMs())
                .build();

        qaRepository.save(qaSession);

    }

    public List<QASessionResponse> getSessions(Long materialId, Long chatId) {
        List<QASession> sessions;
        if (chatId != null) {
            sessions = qaRepository.findByChatIdOrderByCreatedAtAsc(chatId);
        } else if (materialId != null) {
            sessions = qaRepository.findByMaterialIdOrderByCreatedAtDesc(materialId);
        } else {
            sessions = qaRepository.findAllByOrderByCreatedAtDesc();
        }

        return sessions.stream()
                .map(QASessionResponse::from)
                .toList();
    }

    public QAChatResponse createChat(String title, Long materialId) {
        Material material = materialService.findById(materialId);

        QAChat chat = QAChat.builder()
                .title(title)
                .material(material)
                .build();

        QAChat saved = qaChatRepository.save(chat);
        return QAChatResponse.from(saved);
    }

    public List<QAChatResponse> getChats(Optional<Long> materialId) {
        List<QAChat> chats = qaChatRepository.findAllByOrderByCreatedAtDesc();

        return chats.stream()
                .filter(chat -> materialId.map(id -> chat.getMaterial() != null && chat.getMaterial().getId().equals(id)).orElse(true))
                .map(QAChatResponse::from)
                .toList();
    }

    public QAChatResponse updateChatTitle(Long chatId, String title) {
        QAChat chat = qaChatRepository.findById(chatId)
                .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 채팅입니다."));

        chat.setTitle(title);
        QAChat saved = qaChatRepository.save(chat);
        return QAChatResponse.from(saved);
    }

    @Transactional
    public void deleteChat(Long chatId) {
        QAChat chat = qaChatRepository.findById(chatId)
                .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 채팅입니다."));

        qaRepository.deleteByChatId(chatId);
        qaChatRepository.delete(chat);
    }
}
