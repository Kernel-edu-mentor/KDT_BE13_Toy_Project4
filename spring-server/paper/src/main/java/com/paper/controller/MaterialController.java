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
    public Mono<ResponseEntity<String>> uploadMaterial (
            @RequestParam("file") MultipartFile file,
            @RequestParam("title") String title
            //@AuthenticationPrincipal UserDetails userDetails // TODO : 회원 로직 생성 후 연결
    ) {

        log.info("User {} uploading : {}", "testuser", title);  // TODO : 실제 user 연결

        try {

            // 1. 서비스에 전체 업로드 로직 위임 (파일 I/O + DB 저장)
            Material material = materialService.uploadAndCreateMaterial("user", file, title);

            // 2. 외부 호출용 DTO로 변환
            MaterialUploadRequest request = MaterialUploadRequest.from(
                    material,
                    material.getFilePath(),
                    material.getFileType().toString() // DTO가 문자열을 받도록 가정
            );

            // Mono 체인 반환
            return pythonClient.uploadMaterial(request)
                    .doOnSuccess(resp -> {
                        materialService.updateParseStatus(
                                request.getMaterialId(),
                                Material.ParseStatus.COMPLETED,
                                resp.getPageCount()
                        );
                        log.info("Parsing completed : id = {}", request.getMaterialId());
                    })
                    .map(resp -> ResponseEntity.ok("파일 업로드 완료!"))
                    .onErrorResume(err -> {
                        // Python 클라이언트 통신 실패 시
                        log.error("Parsing Failed : {}",err.getMessage());
                        materialService.updateParseStatus(
                                request.getMaterialId(),
                                Material.ParseStatus.FAILED,
                                null
                        );
                        return Mono.just(ResponseEntity.internalServerError().build());
                    })
                    .doFinally(signal -> log.info("Controller Mono 체인 최종 상태 : {}", signal));

        } catch (Exception e) {
            // 파일 저장 또는 DB 저장(createMaterial) 중 동기 예외 발생 시 처리
            log.error("Upload Failed (Synchronous Error) : {}", e.getMessage(), e);
            // 동기 예외를 Mono.error()로 감싸서 반환하거나,
            // 여기서는 요청을 즉시 종료하는 ResponseEntity.badRequest()를 반환합니다.
            return Mono.just(ResponseEntity.badRequest().body("파일 업로드에 실패하였습니다."));
        }
    }
}

