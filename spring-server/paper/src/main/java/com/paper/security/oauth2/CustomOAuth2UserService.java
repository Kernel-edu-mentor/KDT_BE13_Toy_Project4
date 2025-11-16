package com.paper.security.oauth2;

import com.paper.domain.User;
import com.paper.repository.UserRepository;
import com.paper.security.UserPrincipal;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class CustomOAuth2UserService extends DefaultOAuth2UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {

        // 1. OAuth2 Provider로부터 사용자 정보 가져오기
        OAuth2User oAuth2User = super.loadUser(userRequest);

        // 2. Provider 식별 (Kakao, Google 등,,)
        String registrationId = userRequest.getClientRegistration().getRegistrationId();

        // 3. Provider별 사용자 정보 추출
        OAuth2UserInfo oAuth2UserInfo = getOAuth2UserInfo(registrationId, oAuth2User.getAttributes());

        // 4. 사용자 정보 처리 (회원가입 || 업데이트)
        User user = processOAuth2User(oAuth2UserInfo, registrationId);

        // 5. UserPrincipal 반한 (Spriing Security에서 사용)
        return UserPrincipal.from(user, oAuth2User.getAttributes());
    }

    private OAuth2UserInfo getOAuth2UserInfo(String registrationId, Map<String, Object> attributes) {

        if("kakao".equals(registrationId)) {
            return new KakaoOAuth2UserInfo(attributes);
        }
        // 다른 소셜 추가 가능.
        throw new OAuth2AuthenticationException("Unsupported registration id " + registrationId);
    }

    private User processOAuth2User(OAuth2UserInfo oAuth2UserInfo, String provider) {

        String username = provider + "_" + oAuth2UserInfo.getId();

        // 기존 사용자 조회 || 신규 생성
        return userRepository.findByUsername(username)
                .orElseGet(() -> createUser(oAuth2UserInfo, provider, username));
    }

    private User createUser(OAuth2UserInfo oAuth2UserInfo, String provider, String username) {
        User user = User.builder()
                .username(username)
                .password(passwordEncoder.encode("OAUTH2_USER")) // OAuth2 사용자는 비밀번호 불필요
                .role(User.Role.STUDENT)
                .provider(provider)
                .createdAt(LocalDateTime.now())
                .build();

        log.info("새 OAuth2 사용자 생성: {}", username);
        return userRepository.save(user);
    }

}
