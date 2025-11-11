package com.paper.service;

import com.paper.domain.Material;
import com.paper.domain.User;
import com.paper.dto.client.ProblemAnswerRequest;
import com.paper.repository.MaterialRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class MaterialService {

    private final MaterialRepository materialRepository;
    private final FileStorageService fileStorageService;
    private final UserService userService;

    public Material uploadAndCreateMaterial(Long userId, MultipartFile file, String title) {

        // 1. 파일 저장 (파일 I/O 로직을 서비스 안으로 가져옴)
        String filePath = fileStorageService.storeFile(file);
        String fileType = fileStorageService.getFileType(file.getOriginalFilename());

        User user = userService.findById(userId);

        // 2. DB 저장 (메타데이터)
        Material material = Material.builder()
                .title(title)
                .fileType(Material.FileType.valueOf(fileType))
                .filePath(filePath)
                .uploadedBy(user)
                .build();

        return materialRepository.save(material);
    }

    public void updateParseStatus(Long materialId, Material.ParseStatus parseStatus, Integer pageCount) {

        // 1. ID로 객체를 다시 로드
        Material material = materialRepository.findById(materialId)
                .orElseThrow(() -> new IllegalArgumentException("Material not found: " + materialId));

        // 2. 로드된 객체의 필드를 변경합니다.
        material.setParseStatus(parseStatus);
        if(pageCount != null) {
            material.setPageCount(pageCount);
        }
    }

    public Material findById(Long materialId) {

        Material material = materialRepository.findById(materialId)
                .orElseThrow(() -> new IllegalArgumentException("Material not found: " + materialId));

        return material;
    }

    @Transactional(readOnly = true)
    public List<ProblemAnswerRequest.MaterialResponse> findAll() {
        return materialRepository.findAll().stream()
                .map(ProblemAnswerRequest.MaterialResponse::from)
                .sorted(Comparator.comparing(ProblemAnswerRequest.MaterialResponse::getCreatedAt).reversed())
                .collect(Collectors.toList());
    }
}
