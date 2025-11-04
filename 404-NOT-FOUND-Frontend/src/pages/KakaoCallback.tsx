import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ApiError, postJson } from "@/lib/api";

interface LoginResponse {
  sessionId: string;
  user: {
    id: number;
    username: string;
    role: "INSTRUCTOR" | "STUDENT";
    createdAt: string;
  };
}

const KakaoCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const code = searchParams.get("code");
    const errorParam = searchParams.get("error");

    if (errorParam) {
      setError(`카카오 로그인 오류: ${errorParam}`);
      setLoading(false);
      setTimeout(() => navigate("/auth"), 3000);
      return;
    }

    if (!code) {
      setError("인가 코드를 받지 못했습니다.");
      setLoading(false);
      setTimeout(() => navigate("/auth"), 3000);
      return;
    }

    // 인가 코드를 백엔드로 전달
    const handleKakaoLogin = async () => {
      try {
        const response = await postJson<LoginResponse>("/auth/kakao/callback", {
          code,
        });

        sessionStorage.setItem("ai-mentor-user", JSON.stringify(response.user));
        sessionStorage.setItem("ai-mentor-session", response.sessionId);
        navigate("/dashboard");
      } catch (err) {
        let message = "카카오 로그인 처리 중 문제가 발생했습니다.";
        if (err instanceof ApiError) {
          message = `[${err.status}] ${err.message}`;
          console.error("카카오 로그인 API 에러:", err.status, err.message);
        } else {
          console.error("카카오 로그인 에러:", err);
        }
        setError(message);
        setTimeout(() => navigate("/auth"), 3000);
      } finally {
        setLoading(false);
      }
    };

    handleKakaoLogin();
  }, [searchParams, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-sm text-muted-foreground">카카오 로그인 처리 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <p className="text-sm text-red-500">{error}</p>
          <p className="text-xs text-muted-foreground">잠시 후 로그인 페이지로 이동합니다.</p>
        </div>
      </div>
    );
  }

  return null;
};

export default KakaoCallback;
