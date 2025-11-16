import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { getJson } from "@/lib/api";

interface User {
  id: number;
  username: string;
  role: "INSTRUCTOR" | "STUDENT";
  createdAt: string;
}

const Index = () => {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  const handleKakaoLogin = () => {
    window.location.href = "http://localhost:8080/oauth2/authorization/kakao";
  };

  useEffect(() => {
    // 백엔드 세션 쿠키로 로그인 상태 확인
    const checkAuthStatus = async () => {
      try {
        const userInfo = await getJson<User>("/auth/me");
        setIsLoggedIn(true);
        setUser(userInfo);
      } catch (error) {
        // 로그인되지 않은 경우 (401 Unauthorized) 무시
        setIsLoggedIn(false);
        setUser(null);
      }
    };

    checkAuthStatus();
  }, []);

  return (
    <section className="max-w-7xl mx-auto px-6 pt-36 pb-16 min-h-[75vh] flex flex-col items-center justify-center text-center gap-12">
      <div className="space-y-8">
        <h1 className="text-5xl md:text-6xl font-bold text-foreground leading-tight">
          AI와 함께하는
          <br />
          스마트한 학습
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          질문하고, 배우고, 퀴즈로 테스트하세요.
          <br />
          당신만의 AI 학습 파트너입니다.
        </p>
        <div className="flex gap-4 justify-center">
          {isLoggedIn ? (
            <>
              <Button
                onClick={() => navigate("/dashboard")}
                size="lg"
                className="h-14 px-8 rounded-full border border-gray-300 bg-white text-lg font-medium text-gray-800 transition hover:border-blue-600 hover:bg-blue-600 hover:text-white"
              >
                질문하기
              </Button>
              <Button
                onClick={() => navigate("/quiz")}
                size="lg"
                variant="outline"
                className="h-14 px-8 rounded-full border border-gray-300 text-lg font-medium text-gray-800 transition hover:border-blue-600 hover:bg-blue-600 hover:text-white"
              >
                퀴즈 풀기
              </Button>
            </>
          ) : (
            <Button
              onClick={handleKakaoLogin}
              size="lg"
              className="h-14 px-8 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 text-lg transition transform hover:-translate-y-1"
            >
              로그인 하기
            </Button>
          )}
        </div>
      </div>

      <p className="text-lg text-muted-foreground">
        {isLoggedIn ? (
          <>
            <span className="text-blue-600 font-semibold">{user?.username || "사용자"}</span>
            님, AI 멘토와 함께 학습 여정을 계속하세요.
          </>
        ) : (
          "카카오 계정으로 간편하게 로그인하고 AI 멘토와 학습 여정을 시작해 보세요."
        )}
      </p>
    </section>
  );
};

export default Index;
