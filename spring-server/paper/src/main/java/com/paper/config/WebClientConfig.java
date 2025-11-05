package com.paper.config;


import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class WebClientConfig {

    @Value("${python.ai-service.url}")
    private String aiServiceUrl;

    @Bean
    public WebClient pythonWebClient() {
        return WebClient.builder()
                .baseUrl(aiServiceUrl)
                .defaultHeader("Content-Type", "application/json")
                .build();
    }

}
