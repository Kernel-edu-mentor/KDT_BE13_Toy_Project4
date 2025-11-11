package com.paper.repository;

import com.paper.domain.QASession;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface QARepository extends JpaRepository<QASession, Long> {

    List<QASession> findByMaterialIdOrderByCreatedAtDesc(Long materialId);

    List<QASession> findByChatIdOrderByCreatedAtAsc(Long chatId);

    List<QASession> findAllByOrderByCreatedAtDesc();

    @Query("SELECT q FROM QASession q WHERE q.user.id = :userId ORDER BY q.createdAt DESC")
    List<QASession> findByUserIdOrderByCreatedAtDesc(@Param("userId") Long userId);

    void deleteByChatId(Long chatId);

    @Query("SELECT q FROM QASession q WHERE q.user.id = :userId AND q.chat.id = :chatId ORDER BY q.createdAt DESC")
    List<QASession> findByUserIdAndChatIdByCreatedAtDesc(@Param("userId") Long userId, @Param("chatId") Long chatId);
}
