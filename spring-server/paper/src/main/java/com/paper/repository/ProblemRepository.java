package com.paper.repository;

import com.paper.domain.Material;
import com.paper.domain.Problem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ProblemRepository extends JpaRepository<Problem, Long> {
    List<Problem> findByDifficultyOrderByCreatedAtDesc(Problem.Difficulty difficulty);
    List<Problem> findByMaterialAndDifficultyOrderByCreatedAtDesc(Material material, Problem.Difficulty difficulty);
}
