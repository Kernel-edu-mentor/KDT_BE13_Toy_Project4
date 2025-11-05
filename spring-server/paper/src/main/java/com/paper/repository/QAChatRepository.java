package com.paper.repository;

import com.paper.domain.QAChat;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface QAChatRepository extends JpaRepository<QAChat, Long> {

    List<QAChat> findAllByOrderByCreatedAtDesc();
}
