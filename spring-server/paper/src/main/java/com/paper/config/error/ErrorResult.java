package com.paper.config.error;

import lombok.Builder;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;

import java.time.LocalDateTime;

@Getter
@Builder
@Slf4j
public class ErrorResult {

    private String errorCode;
    private LocalDateTime timestamp;

    public static ErrorResult of (String errorCode, String message){

        log.info("ErrorResult.message : " + message);

        return ErrorResult.builder()
                .errorCode(errorCode)
                .timestamp(LocalDateTime.now())
                .build();
    }
}
