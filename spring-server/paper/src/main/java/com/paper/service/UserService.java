package com.paper.service;

import com.paper.domain.User;
import com.paper.dto.user.LoginRequest;
import com.paper.dto.user.LoginResponse;
import com.paper.dto.user.UserRegistrationRequest;
import com.paper.dto.user.UserResponse;
import com.paper.exception.InvalidCredentialsException;
import com.paper.exception.UsernameAlreadyExistsException;
import com.paper.repository.UserRepository;
import com.paper.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;

    @Transactional
    public UserResponse register(UserRegistrationRequest request) {
        if (userRepository.existsByUsername(request.getUsername())) {
            throw new UsernameAlreadyExistsException(request.getUsername());
        }

        User user = User.builder()
                .username(request.getUsername())
                .password(passwordEncoder.encode(request.getPassword()))
                .role(request.resolveRole())
                .createdAt(LocalDateTime.now())
                .build();

        User saved = userRepository.save(user);
        return UserResponse.from(saved);
    }

    public LoginResponse login(LoginRequest request) {
        User user = userRepository.findByUsername(request.getUsername())
                .orElseThrow(InvalidCredentialsException::new);

        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new InvalidCredentialsException();
        }

        String token = jwtTokenProvider.generateToken(user.getUsername(), user.getRole());
        return LoginResponse.of(token, UserResponse.from(user));
    }

    public UserResponse getUserProfile(String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(InvalidCredentialsException::new);
        return UserResponse.from(user);
    }
}
