package com.paper.client;

import com.paper.dto.TestResponse;
import com.paper.dto.client.MaterialUploadRequest;
import com.paper.dto.client.MaterialUploadResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatusCode;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;

@Slf4j
@Component
@RequiredArgsConstructor
public class PythonClient {

    private final WebClient pythonWebClient;

    /**
     * 테스트 api 호출
     */
    public Mono<TestResponse> test () {

        log.info("PythonClient test");

        return pythonWebClient.get()
                .uri("/")
                .retrieve()
                .bodyToMono(TestResponse.class)
                .timeout(Duration.ofSeconds(3))
                .doOnSuccess(resp ->
                        log.info("Call Test Python API response received!")
                )
                .doOnError(err ->
                        log.error("Call Test Python API Failed {}", err.getMessage())
                );

    }

    /**
     * ✨ 자료 업로드 (파일 경로만 전달)
     */
    public Mono<MaterialUploadResponse> uploadMaterial(MaterialUploadRequest request) {
        log.info("Sending material upload to Python: material_id={}, path={}",
                request.getMaterialId(), request.getFilePath());

        return pythonWebClient.post()
                .uri("/qa/qa/upload")
                .bodyValue(request)
                .retrieve()
                .onStatus(HttpStatusCode::isError, clientResponse ->
                        clientResponse.bodyToMono(String.class) // 응답 본문을 String으로 읽기
                                .flatMap(body -> {
                                    log.error("Upload failed with status {}. Response body: {}", clientResponse.statusCode(), body); // 🌟 본문 로그 출력
                                    return Mono.error(new RuntimeException("Upload failed: " + body));
                                })
                )
                .bodyToMono(MaterialUploadResponse.class)
                .timeout(Duration.ofSeconds(90))
                .doOnSuccess(response ->
                        log.info("Upload completed: materialId={}, status={}, chunks={}, page_count={}, message={}",
                                request.getMaterialId(), response.getStatus(), response.getChunkCount(), response.getPageCount(), response.getMessage(), response.getMessage())
                )
                .doOnError(error -> {
                    // 🌟 예외 클래스 이름을 포함하여 더 상세히 기록
                    log.error("Upload failed: Type={}, Message={}", error.getClass().getSimpleName(), error.getMessage());
                });
    }
}
