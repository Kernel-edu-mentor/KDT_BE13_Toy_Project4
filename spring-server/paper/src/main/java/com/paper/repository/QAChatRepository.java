package com.paper.repository;

import com.paper.domain.Material;
import com.paper.domain.QAChat;
import com.paper.domain.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface QAChatRepository extends JpaRepository<QAChat, Long> {

    @Query("SELECT q FROM QAChat q WHERE q.material.id = :materialId AND q.user.id = :userId ORDER BY q.createdAt DESC")
    List<QAChat> findByMaterialIdAndUserId(@Param("materialId") Long materialId, @Param("userId") Long userId);

    @Query("SELECT q FROM QAChat q WHERE q.user.id = :userId ORDER BY q.createdAt DESC")
    List<QAChat> findByUserId(@Param("userId") Long userId);
}
