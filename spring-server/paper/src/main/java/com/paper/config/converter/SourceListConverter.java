package com.paper.config.converter;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.paper.dto.client.python.MaterialUploadRequest;
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import lombok.extern.slf4j.Slf4j;

import java.io.IOException;
import java.util.List;

@Slf4j
@Converter
public class SourceListConverter implements AttributeConverter<List<MaterialUploadRequest.QAResponse.Source>, String> {

    private final ObjectMapper objectMapper = new ObjectMapper();
    // Jackson이 List<Source> 타입을 인식하도록 TypeReference 사용
    private final com.fasterxml.jackson.core.type.TypeReference<List<MaterialUploadRequest.QAResponse.Source>> typeRef =
            new com.fasterxml.jackson.core.type.TypeReference<List<MaterialUploadRequest.QAResponse.Source>>() {};

    /**
     * 엔티티 필드 (List<Source>) -> DB 컬럼 (String/JSONB)으로 변환
     */
    @Override
    public String convertToDatabaseColumn(List<MaterialUploadRequest.QAResponse.Source> attribute) {
        if (attribute == null) {
            return null;
        }
        try {
            // List<Source> 객체를 JSON 문자열로 직렬화
            return objectMapper.writeValueAsString(attribute);
        } catch (JsonProcessingException e) {
            log.error("Error converting List<Source> to JSON string: " + attribute, e);
            // 직렬화 실패 시 빈 JSON 배열 또는 null 반환 선택
            return "[]";
        }
    }

    /**
     * DB 컬럼 (String/JSONB) -> 엔티티 필드 (List<Source>)로 변환
     */
    @Override
    public List<MaterialUploadRequest.QAResponse.Source> convertToEntityAttribute(String dbData) {
        if (dbData == null || dbData.isEmpty()) {
            return null;
        }
        try {
            // JSON 문자열을 List<Source> 객체로 역직렬화
            return objectMapper.readValue(dbData, typeRef);
        } catch (IOException e) {
            log.error("Error converting JSON string to List<Source>: " + dbData, e);
            // 역직렬화 실패 시 빈 리스트 또는 null 반환 선택
            return List.of();
        }
    }
}
