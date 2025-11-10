import { useEffect, useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Sparkles, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { logout } from "@/lib/api";

interface User {
  id: number;
  username: string;
  role: "INSTRUCTOR" | "STUDENT";
  createdAt: string;
}

const MainLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  // 로그인 상태 확인 함수
  const checkLoginStatus = () => {
    const userStr = sessionStorage.getItem("ai-mentor-user");
    if (userStr) {
      try {
        const parsedUser: User = JSON.parse(userStr);
        if (parsedUser && parsedUser.id) {
          setIsLoggedIn(true);
          setUser(parsedUser);
        } else {
          setIsLoggedIn(false);
          setUser(null);
        }
      } catch (error) {
        console.error("사용자 정보 파싱 실패:", error);
        sessionStorage.removeItem("ai-mentor-user");
        sessionStorage.removeItem("ai-mentor-session");
        setIsLoggedIn(false);
        setUser(null);
      }
    } else {
      setIsLoggedIn(false);
      setUser(null);
    }
  };

  // 컴포넌트 마운트 시 확인
  useEffect(() => {
    checkLoginStatus();
  }, []);

  // 라우트 변경 시마다 로그인 상태 재확인
  useEffect(() => {
    checkLoginStatus();
  }, [location.pathname]);

  const handleLogout = async () => {
    // 백엔드 세션 정리 및 sessionStorage 정리
    await logout();

    // 추가 세션 데이터 정리
    sessionStorage.removeItem("ai-mentor-material-id");
    sessionStorage.removeItem("qa-last-chat-id");

    setIsLoggedIn(false);
    setUser(null);

    // 카카오 계정 로그아웃 페이지로 리다이렉트
    const kakaoRestApiKey = import.meta.env.VITE_KAKAO_REST_API_KEY;
    const logoutRedirectUri = import.meta.env.VITE_KAKAO_LOGOUT_REDIRECT_URI;
    const kakaoLogoutUrl = `https://kauth.kakao.com/oauth/logout?client_id=${kakaoRestApiKey}&logout_redirect_uri=${logoutRedirectUri}`;

    window.location.href = kakaoLogoutUrl;
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col overflow-hidden">
      <header className="border-b border-border">
        <div className="max-w-full mx-auto px-4 h-16 flex items-center justify-between">
          <button
            type="button"
            onClick={() => navigate("/")}
            className="flex items-center gap-2 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-md px-1 py-1"
          >
            <img src="/logo.png" alt="AI Mentor Logo" className="w-8 h-8" />
            <span className="text-xl font-bold">AI MENTOR</span>
          </button>
          
          {isLoggedIn && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">
                {user?.username || "사용자"}님
              </span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleLogout}
                className="flex items-center gap-2"
              >
                <LogOut size={16} />
                로그아웃
              </Button>
            </div>
          )}
        </div>
      </header>

      <main className="flex-1 min-h-0">
        <Outlet />
      </main>
    </div>
  );
};

export default MainLayout;
