package com.paper.service;

import com.paper.config.FileStorageConfig;
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

        String originalFilename = StringUtils.cleanPath(file.getOriginalFilename());
        String fileExtension = getFileExtension(originalFilename);
        String storedFilename = UUID.randomUUID().toString() + "." + fileExtension;

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
            log.error("파일 저장 실패 : {}",originalFilename , e.getMessage());
            throw new RuntimeException("파일 저장 실패 : " + originalFilename , e); // TODO : 추후 GlobalException 적용
        }
    }

    private void validateFile(MultipartFile file) {

        if (file.isEmpty()) {
            throw new IllegalArgumentException("파일을 찾을 수 없습니다.");  // TODO : 추후 GlobalException 적용
        }

        if (file.getSize() > fileConfig.getMaxSize()) {
            throw new IllegalArgumentException(
                    String.format("File size exceeds maximum: %d bytes", fileConfig.getMaxSize())
            );  // TODO : 추후 GlobalException 적용
        }

        String filename = StringUtils.cleanPath(file.getOriginalFilename());
        String extension = getFileExtension(filename);

        if (!fileConfig.getAllowedExtensions().contains(extension.toLowerCase())) {
            throw new IllegalArgumentException(
                    String.format("File extension not allowed: %s", extension)
            );  // TODO : 추후 GlobalException 적용
        }

        if (filename.contains("..")) {
            throw new IllegalArgumentException("Invalid path sequence in filename");  // TODO : 추후 GlobalException 적용
        }
    }

    private String getFileExtension(String filename) {
        int lastDotIndex = filename.lastIndexOf('.');
        if (lastDotIndex == -1) {
            throw new IllegalArgumentException("File has no extension");  // TODO : 추후 GlobalException 적용
        }
        return filename.substring(lastDotIndex + 1);
    }

    public String getFileType(String filename) {
        String extension = getFileExtension(filename).toLowerCase();
        if ("pdf".equals(extension)) {
            return "PDF";
        }
        throw new IllegalArgumentException("Unsupported file type: " + extension);  // TODO : 추후 GlobalException 적용
    }
}
