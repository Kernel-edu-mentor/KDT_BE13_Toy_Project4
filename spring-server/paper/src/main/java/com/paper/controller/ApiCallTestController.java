package com.paper.controller;

import com.paper.client.PythonClient;
import com.paper.dto.TestResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/test")
@RequiredArgsConstructor
public class ApiCallTestController {

    private final PythonClient pythonClient;

    @GetMapping()
    public Mono<TestResponse> test() {
        return pythonClient.test();
    }
}
