package com.paper.service;

import com.paper.config.error.ErrorCode;
import com.paper.config.error.exceprion.BusinessException;
import com.paper.domain.User;
import com.paper.dto.user.LoginRequest;
import com.paper.dto.user.UserRegistrationRequest;
import com.paper.dto.user.UserResponse;
import com.paper.exception.UsernameAlreadyExistsException;
import com.paper.repository.UserRepository;
import com.paper.security.UserPrincipal;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuthenticationManager authenticationManager;

    @Transactional
    public UserResponse register(UserRegistrationRequest request) {
        if (userRepository.existsByUsername(request.getUsername())) {
            throw new UsernameAlreadyExistsException(request.getUsername());
        }

        User user = User.builder()
                .username(request.getUsername())
                .password(passwordEncoder.encode(request.getPassword()))
                .role(request.resolveRole())
                .provider("local")
                .createdAt(LocalDateTime.now())
                .build();

        User saved = userRepository.save(user);
        return UserResponse.from(saved);
    }

    public Authentication authenticate(LoginRequest request) {
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.getUsername(), request.getPassword())
        );

        if (!(authentication.getPrincipal() instanceof UserPrincipal)) {
            throw new BusinessException(ErrorCode.INVALID_CREDENTIALS);
        }
        return authentication;
    }

    public UserResponse getUserProfile(String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_CREDENTIALS));
        return UserResponse.from(user);
    }

    public User findById(Long id) {
        return userRepository.findById(id)
                .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));
    }
}
