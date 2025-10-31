package com.paper.service;

import com.paper.domain.Material;
import com.paper.repository.MaterialRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class MaterialService {

    private final MaterialRepository materialRepository;

    public Material createMaterial(String testuser, String title, String fileType, String filePath, Material.ParseStatus parseStatus) {

        Material material = Material.builder()
                .title(title)
                .fileType(Material.FileType.valueOf(fileType))
                .filePath(filePath)
                .parseStatus(parseStatus)

                .build();

        return materialRepository.save(material);
    }

    public void updateParseStatus(Long materialId, Material.ParseStatus parseStatus, Integer pageCount) {

        // 1. ID로 객체를 다시 로드합니다 (트랜잭션 내에서 managed 상태로 만듦)
        Material material = materialRepository.findById(materialId)
                .orElseThrow(() -> new IllegalArgumentException("Material not found: " + materialId));

        // 2. 로드된 객체의 필드를 변경합니다.
        material.setParseStatus(parseStatus);
        if(pageCount != null) {
            material.setPageCount(pageCount);
        }
    }
}
