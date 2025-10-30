package com.paper.client;

import com.paper.dto.TestResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
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
}
