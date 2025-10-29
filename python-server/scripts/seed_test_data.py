"""
팀2 개발/테스트용 샘플 데이터 삽입 스크립트
ChromaDB에 테스트용 학습 자료를 직접 추가합니다.
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from shared.chroma_client import chroma_client
from shared.upstage_client import upstage_client

# 샘플 학습 자료 (Spring Boot JPA 관련)
SAMPLE_MATERIALS = {
    1: [
        {
            "content": """
            JPA (Java Persistence API)는 자바 객체와 데이터베이스 테이블 간의 매핑을 처리하는 ORM(Object-Relational Mapping) 기술입니다.

            주요 개념:
            1. Entity: 데이터베이스 테이블과 매핑되는 자바 클래스
            2. EntityManager: 엔티티의 생명주기를 관리하는 핵심 인터페이스
            3. Repository: 데이터 접근 계층을 추상화한 인터페이스

            예제:
            @Entity
            public class User {
                @Id
                @GeneratedValue(strategy = GenerationType.IDENTITY)
                private Long id;
                private String username;
                private String email;
            }
            """,
            "page": 1
        },
        {
            "content": """
            JPA 연관관계 매핑

            1. @OneToOne: 일대일 관계
            2. @OneToMany: 일대다 관계
            3. @ManyToOne: 다대일 관계
            4. @ManyToMany: 다대다 관계

            예제:
            @Entity
            public class Order {
                @ManyToOne
                @JoinColumn(name = "user_id")
                private User user;

                @OneToMany(mappedBy = "order")
                private List<OrderItem> items;
            }
            """,
            "page": 2
        },
        {
            "content": """
            Spring Data JPA Repository

            기본 제공 메서드:
            - save(): 엔티티 저장
            - findById(): ID로 조회
            - findAll(): 전체 조회
            - deleteById(): ID로 삭제

            커스텀 쿼리:
            public interface UserRepository extends JpaRepository<User, Long> {
                List<User> findByUsername(String username);

                @Query("SELECT u FROM User u WHERE u.email LIKE %:domain%")
                List<User> findByEmailDomain(@Param("domain") String domain);
            }
            """,
            "page": 3
        },
        {
            "content": """
            트랜잭션 관리

            @Transactional 어노테이션을 사용하여 트랜잭션을 관리합니다.

            주요 속성:
            - propagation: 트랜잭션 전파 방식
            - isolation: 격리 수준
            - readOnly: 읽기 전용 설정
            - rollbackFor: 롤백 예외 지정

            예제:
            @Service
            public class UserService {
                @Transactional
                public User createUser(UserDto dto) {
                    User user = new User();
                    user.setUsername(dto.getUsername());
                    return userRepository.save(user);
                }
            }
            """,
            "page": 4
        },
        {
            "content": """
            영속성 컨텍스트 (Persistence Context)

            영속성 컨텍스트는 엔티티를 영구 저장하는 환경입니다.

            엔티티 생명주기:
            1. 비영속(new/transient): 영속성 컨텍스트와 관계없는 상태
            2. 영속(managed): 영속성 컨텍스트에 저장된 상태
            3. 준영속(detached): 영속성 컨텍스트에서 분리된 상태
            4. 삭제(removed): 삭제된 상태

            1차 캐시와 변경 감지(Dirty Checking) 기능을 제공합니다.
            """,
            "page": 5
        }
    ],
    2: [
        {
            "content": """
            Python FastAPI 기초

            FastAPI는 현대적이고 빠른 Python 웹 프레임워크입니다.

            주요 특징:
            1. 자동 API 문서 생성 (Swagger UI)
            2. Pydantic을 이용한 데이터 검증
            3. 비동기 처리 지원
            4. 타입 힌트 기반 개발

            기본 예제:
            from fastapi import FastAPI

            app = FastAPI()

            @app.get("/")
            async def root():
                return {"message": "Hello World"}
            """,
            "page": 1
        },
        {
            "content": """
            Pydantic 모델

            FastAPI는 Pydantic을 사용하여 요청/응답 데이터를 검증합니다.

            예제:
            from pydantic import BaseModel

            class User(BaseModel):
                id: int
                name: str
                email: str
                is_active: bool = True

            @app.post("/users/")
            async def create_user(user: User):
                return {"user": user, "status": "created"}
            """,
            "page": 2
        }
    ]
}

async def seed_material(material_id: int):
    """특정 material_id로 샘플 데이터 삽입"""
    print(f"\n📦 Material {material_id} 샘플 데이터 삽입 중...")

    blocks = SAMPLE_MATERIALS.get(material_id)
    if not blocks:
        print(f"❌ Material {material_id}에 대한 샘플 데이터가 없습니다.")
        return

    # 텍스트 추출
    texts = [block['content'].strip() for block in blocks]

    # 임베딩 생성
    print(f"🔄 {len(texts)}개 블록 임베딩 생성 중...")
    embeddings = await upstage_client.embed_documents(texts)

    # ChromaDB에 저장
    documents = []
    metadatas = []
    ids = []

    for idx, block in enumerate(blocks):
        documents.append(block['content'].strip())
        metadatas.append({
            'material_id': material_id,
            'page': block['page'],
            'type': 'text'
        })
        ids.append(f"material_{material_id}_block_{idx}")

    chroma_client.add_documents(
        collection_name="learning_materials",
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings
    )

    print(f"✅ Material {material_id}: {len(blocks)}개 블록 저장 완료")

async def main():
    """모든 샘플 데이터 삽입"""
    print("=" * 60)
    print("🌱 팀2 테스트용 샘플 데이터 삽입 시작")
    print("=" * 60)

    # Material 1: Spring Boot JPA 학습자료
    await seed_material(1)

    # Material 2: Python FastAPI 학습자료
    await seed_material(2)

    print("\n" + "=" * 60)
    print("✅ 모든 샘플 데이터 삽입 완료!")
    print("=" * 60)
    print("\n📝 사용 방법:")
    print("  - Material 1 (JPA): BEGINNER, INTERMEDIATE, ADVANCED 문제 생성 가능")
    print("  - Material 2 (FastAPI): BEGINNER 문제 생성 가능")
    print("\n🧪 테스트 API 호출:")
    print("""
  curl -X POST http://localhost:8000/problems/generate \\
    -H "Content-Type: application/json" \\
    -d '{
      "material_id": 1,
      "difficulty": "BEGINNER",
      "problem_count": 3
    }'
    """)

if __name__ == "__main__":
    asyncio.run(main())
