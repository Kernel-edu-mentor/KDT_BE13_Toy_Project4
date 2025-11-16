package com.paper.service;

import com.paper.config.error.ErrorCode;
import com.paper.config.error.exceprion.BusinessException;
import com.paper.domain.Material;
import com.paper.domain.QAChat;
import com.paper.domain.User;
import com.paper.dto.client.QAChatResponse;
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
public class ChatService {

    private final QAChatRepository qaChatRepository;
    private final QARepository qaRepository;
    private final MaterialService materialService;
    private final UserService userService;

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

    @Transactional(readOnly = true)
    public List<QAChatResponse> getChats(Long userId) {
        List<QAChat> chats = qaChatRepository.findByUserId(userId);
        return chats.stream()
                .map(QAChatResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public List<QAChatResponse> getChats(Long materialId, Long userId) {
        List<QAChat> chats = qaChatRepository.findByMaterialIdAndUserId(materialId, userId);
        return chats.stream()
                .map(QAChatResponse::from)
                .toList();
    }

    public QAChatResponse updateChatTitle(Long chatId, String title, Long userId) {
        QAChat chat = qaChatRepository.findById(chatId)
                .orElseThrow(() -> new BusinessException(ErrorCode.CHAT_NOT_FOUND));

        validateChatOwnership(chat, userId);

        chat.setTitle(title);
        QAChat saved = qaChatRepository.save(chat);
        return QAChatResponse.from(saved);
    }

    public void deleteChat(Long chatId, Long userId) {
        QAChat chat = qaChatRepository.findById(chatId)
                .orElseThrow(() -> new BusinessException(ErrorCode.CHAT_NOT_FOUND));

        validateChatOwnership(chat, userId);

        qaRepository.deleteByChatId(chatId);
        qaChatRepository.delete(chat);
    }

    private void validateChatOwnership(QAChat chat, Long userId) {
        if (!chat.getUser().getId().equals(userId)) {
            throw new BusinessException(ErrorCode.USER_MISMATCH);
        }
    }
}