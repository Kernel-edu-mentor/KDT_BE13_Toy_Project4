package com.paper.controller;

import com.paper.client.PythonClient;
import com.paper.domain.Material;
import com.paper.dto.client.MaterialUploadRequest;
import com.paper.service.FileStorageService;
import com.paper.service.MaterialService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import reactor.core.publisher.Mono;

@Slf4j
@RestController
@RequestMapping("/api/materials")
@RequiredArgsConstructor
public class MaterialController {

    private final FileStorageService fileStorageService;
    private final MaterialService materialService;
    private final PythonClient pythonClient;

    /**
     * 학습 자료 업로드
     * 1. Spring에서 파일을 공유 불륨에 저장. (개발 환경에서는 local에 저장)
     * 2. PostgreSql에 메타데이터 저장 (PENDING)
     * 3. Python에 파일 경로만 전달
     * 4. Python이 파일을 읽어 파싱
     * 5. Python 작업 완료 후 COMPLETED로 업데이트
     */
    @PostMapping("/upload")
    public Mono<ResponseEntity<Material>> uploadMaterial (
            @RequestParam("file") MultipartFile file,
            @RequestParam("title") String title
            //@AuthenticationPrincipal UserDetails userDetails // TODO : 회원 로직 생성 후 연결
    ) {

        log.info("User {} uploading : {}", "testuser", title);  // TODO : 실제 user 연결

        try {
            String filePath = fileStorageService.storeFile(file);
            String fileType = fileStorageService.getFileType(file.getOriginalFilename());

            // PostgreSQL에 메타데이터 저장 (동기 실행)
            Material material = materialService.createMaterial (
                    "testuser", title, fileType, filePath, Material.ParseStatus.PENDING
            );
            log.info("Material saved : id = {}, path = {}", material.getId(), filePath);

            // Python에 파일 경로만 전달 및 Mono 체인 시작
            MaterialUploadRequest request = MaterialUploadRequest.builder()
                    .materialId(material.getId())
                    .filePath(filePath)
                    .fileType(fileType.toLowerCase())
                    .build();

            // 🌟 Mono 체인 반환
            return pythonClient.uploadMaterial(request)
                    .doOnSuccess(resp -> {
                        materialService.updateParseStatus(
                                material.getId(),
                                Material.ParseStatus.COMPLETED,
                                resp.getPageCount()
                        );
                        // 🌟 이 로그가 출력됩니다.
                        log.info("Parsing completed : id = {}", material.getId());
                    })
                    .map(resp -> ResponseEntity.ok(material))
                    .onErrorResume(err -> {
                        // Python 클라이언트 통신 실패 시
                        log.error("Parsing Failed : {}",err.getMessage());
                        materialService.updateParseStatus(
                                material.getId(),
                                Material.ParseStatus.FAILED,
                                null
                        );
                        return Mono.just(ResponseEntity.internalServerError().build());
                    })
                    .doFinally(signal -> log.info("Controller Mono 체인 최종 상태 : {}", signal));

        } catch (Exception e) {
            // 파일 저장 또는 DB 저장(createMaterial) 중 동기 예외 발생 시 처리
            log.error("Upload Failed (Synchronous Error) : {}", e.getMessage(), e);
            // 🌟 동기 예외를 Mono.error()로 감싸서 반환하거나,
            // 🌟 여기서는 요청을 즉시 종료하는 ResponseEntity.badRequest()를 반환합니다.
            return Mono.just(ResponseEntity.badRequest().body(null)); // null 대신 적절한 메시지 바디 사용 권장
        }
    }
}

