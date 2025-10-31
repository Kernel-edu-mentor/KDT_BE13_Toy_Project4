package com.paper.service;

import com.paper.domain.Material;
import com.paper.domain.QASession;
import com.paper.dto.client.QARequest;
import com.paper.dto.client.QAResponse;
import com.paper.repository.QARepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class QAService {

    private final QARepository qaRepository;
    private final MaterialService materialService;

    public void saveSession(String testuser, QARequest request, QAResponse response) {

        Material material = materialService.findById(request.getMaterialId());

        QASession.builder()
                .material(material)
                .question(request.getQuestion())
                .answer(response.getAnswer())
                .sources(response.getSources())
                .responseTimeMs(response.getResponseTimeMs())
                .build();
    }
}
