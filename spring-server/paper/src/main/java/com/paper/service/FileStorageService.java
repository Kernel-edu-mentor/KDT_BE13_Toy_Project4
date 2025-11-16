package com.paper.service;

import com.paper.config.FileStorageConfig;
import com.paper.config.error.ErrorCode;
import com.paper.config.error.exceprion.BusinessException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.Objects;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class FileStorageService {

    private final FileStorageConfig fileConfig;

    /**
     * 파일을 공유 디렉터리에 저장
     */
    public String storeFile(MultipartFile file) {

        validateFile(file);

        String originalFilename = StringUtils.cleanPath(Objects.requireNonNull(file.getOriginalFilename()));
        String fileExtension = getFileExtension(originalFilename);
        String storedFilename = UUID.randomUUID() + "." + fileExtension;

        try {
            Path uploadPath = Paths.get(fileConfig.getUploadDir());

            if (!Files.exists(uploadPath)) {
                Files.createDirectories(uploadPath);
                log.info("파일 저장 폴더 생성 : {}", uploadPath);
            }

            Path targetLocation = uploadPath.resolve(storedFilename);
            Files.copy(file.getInputStream(), targetLocation, StandardCopyOption.REPLACE_EXISTING);

            String absolutePath = targetLocation.toAbsolutePath().toString();
            log.info("파일 저장 성공! : {}", absolutePath);

            return absolutePath;
        } catch (IOException e) {
            log.error("파일 저장 실패 : {}, errMsg : {}",originalFilename , e.getMessage());
            throw new BusinessException(ErrorCode.FILE_STORAGE_FAILED);

        }
    }

    private void validateFile(MultipartFile file) {

        if (file.isEmpty()) {
            throw new BusinessException(ErrorCode.FILE_NOT_FOUND);
        }

        if (file.getSize() > fileConfig.getMaxSize()) {
            throw new BusinessException(ErrorCode.FILE_SIZE_EXCEEDED);
        }

        String filename = StringUtils.cleanPath(Objects.requireNonNull(file.getOriginalFilename()));
        String extension = getFileExtension(filename);

        if (!fileConfig.getAllowedExtensions().contains(extension.toLowerCase())) {
            throw new BusinessException(ErrorCode.FILE_EXTENSION_NOT_ALLOWED);
        }

        if (filename.contains("..")) {
            throw new BusinessException(ErrorCode.INVALID_FILE_PATH);
        }
    }

    private String getFileExtension(String filename) {
        int lastDotIndex = filename.lastIndexOf('.');
        if (lastDotIndex == -1) {
            throw new BusinessException(ErrorCode.FILE_NO_EXTENSION);
        }
        return filename.substring(lastDotIndex + 1);
    }

    public String getFileType(String filename) {
        String extension = getFileExtension(filename).toLowerCase();
        if ("pdf".equals(extension)) {
            return "PDF";
        }
        throw new BusinessException(ErrorCode.UNSUPPORTED_FILE_TYPE);
    }
}
