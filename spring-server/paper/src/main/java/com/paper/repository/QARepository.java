package com.paper.repository;

import com.paper.domain.QASession;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface QARepository extends JpaRepository<QASession, Long> {

    List<QASession> findByMaterialIdOrderByCreatedAtDesc(Long materialId);

    List<QASession> findByChatIdOrderByCreatedAtAsc(Long chatId);

    List<QASession> findAllByOrderByCreatedAtDesc();

    void deleteByChatId(Long chatId);
}
