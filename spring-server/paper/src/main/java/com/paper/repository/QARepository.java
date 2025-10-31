package com.paper.repository;

import com.paper.domain.QASession;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface QARepository extends JpaRepository<QASession, Long> {
}
