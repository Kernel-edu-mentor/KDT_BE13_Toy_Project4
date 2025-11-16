package com.paper.config.error;

import lombok.Getter;
import org.springframework.http.HttpStatus;

@Getter
public enum ErrorCode {

    // test
    TEST(HttpStatus.BAD_REQUEST, "001", "test error"),

    // chat
    CHAT_NOT_FOUND(HttpStatus.NOT_FOUND, "C-002", "존재하지 않는 채팅입니다."),
    USER_MISMATCH(HttpStatus.FORBIDDEN, "C-003", "회원 정보가 일치하지 않습니다."),

    // file
    FILE_NOT_FOUND(HttpStatus.BAD_REQUEST, "F-001", "파일을 찾을 수 없습니다."),
    FILE_SIZE_EXCEEDED(HttpStatus.BAD_REQUEST, "F-002", "파일 크기가 최대 용량을 초과했습니다."),
    FILE_EXTENSION_NOT_ALLOWED(HttpStatus.BAD_REQUEST, "F-003", "허용되지 않는 파일 확장자입니다."),
    INVALID_FILE_PATH(HttpStatus.BAD_REQUEST, "F-004", "잘못된 파일 경로입니다."),
    FILE_NO_EXTENSION(HttpStatus.BAD_REQUEST, "F-005", "파일 확장자가 없습니다."),
    UNSUPPORTED_FILE_TYPE(HttpStatus.BAD_REQUEST, "F-006", "지원하지 않는 파일 형식입니다."),
    FILE_STORAGE_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "F-007", "파일 저장에 실패했습니다."),

    // user
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "U-001", "사용자를 찾을 수 없습니다."),
    USERNAME_ALREADY_EXISTS(HttpStatus.CONFLICT, "U-002", "이미 존재하는 사용자명입니다."),
    INVALID_CREDENTIALS(HttpStatus.UNAUTHORIZED, "U-003", "인증 정보가 올바르지 않습니다."),

    // material
    MATERIAL_NOT_FOUND(HttpStatus.NOT_FOUND, "M-001", "자료를 찾을 수 없습니다."),
    MATERIAL_ACCESS_DENIED(HttpStatus.FORBIDDEN, "M-002", "해당 자료에 접근할 권한이 없습니다."),

    // problem
    PROBLEM_NOT_FOUND(HttpStatus.NOT_FOUND, "P-001", "문제를 찾을 수 없습니다."),

    // qa
    CHAT_ACCESS_DENIED(HttpStatus.FORBIDDEN, "Q-001", "해당 채팅에 접근할 권한이 없습니다."),
    CHAT_ID_REQUIRED(HttpStatus.BAD_REQUEST, "Q-002", "chatId는 필수입니다."),
    QA_SESSION_NOT_FOUND(HttpStatus.NOT_FOUND, "Q-003", "해당 채팅에 QA 세션이 없습니다.");

    private final HttpStatus httpStatus;
    private final String errorCode;
    private final String message;

    ErrorCode(HttpStatus httpStatus, String errorCode, String message) {
        this.httpStatus = httpStatus;
        this.errorCode = errorCode;
        this.message = message;
    }
}
