### 📄 [프로젝트 설명서 다운로드 (PDF)](https://github.com/Kernel-edu-mentor/KDT_BE13_Toy_Project4/raw/dev/project-doc.pdf)

### 1-1. **네이밍 규칙 (Naming Rules)**

- **변수 및 함수 이름**: CamelCase 사용 (ex: `getUserData`, `userInfo`)
- **클래스 이름**: PascalCase 사용 (ex: `UserProfile`, `ProductManager`)
- **상수**: UPPER_SNAKE_CASE 사용 (ex: `MAX_RETRY_COUNT`)0
- **파일 이름**: 소문자 및 hyphen(-) 사용 (ex: `user-controller.js`, `app-config.ts`)

### 1-2. **들여쓰기 및 공백 (Indentation & Spacing)**

- **탭 크기**: Tabs
- **라인 길이**: 80자 제한 권장
- **함수 간 공백**: 함수와 함수 사이 한 줄 공백 유지
- **중괄호 위치**: 중괄호는 한 줄 아래
- (ex:
    
    `if (condition) {`
    
             `...`    
    
    `}`            ) 
    

### 1-3. **주석 규칙 (Commenting Rules)**

- **함수 주석**: 함수 상단에 해당 함수의 목적, 입력값, 반환값 명시
- **코드 설명 주석**: 코드가 복잡하거나 중요한 부분에 설명 추가
- 단, 무분별한 주석은 제한

### 1-4. **코드 구조 (Code Structure)**

- **모듈화**: 관련 기능별로 코드를 모듈화 (ex: services, controllers, utils 등)
    
    ### 1-5. **Git 전략 & 커밋 컨벤션**
    
    - **브랜치 네이밍**
        
        ```
        main       → 운영 배포용
        develop    → 개발 통합
        feature/*  → 기능 단위
        fix/*      → 버그 수정
        hotfix/*   → 긴급 수정
        refactor/* -> 코드 리팩토링 
        ```
        
    - **커밋 메시지**
        
        ```
        [Feat] 회원가입 API 추가
        [Fix] 로그인 비밀번호 검증 오류 수정
        [Refactor] JWT 토큰 검증 로직 분리
        [Chore] logback 설정 변경
        ```
        
    
