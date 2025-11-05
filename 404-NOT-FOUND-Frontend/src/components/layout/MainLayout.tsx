import { useEffect, useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Sparkles, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";

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

  const handleLogout = () => {
    // sessionStorage에서 모든 인증 관련 데이터 제거
    sessionStorage.removeItem("ai-mentor-user");
    sessionStorage.removeItem("ai-mentor-session");
    sessionStorage.removeItem("ai-mentor-material-id");
    sessionStorage.removeItem("qa-last-chat-id");
    
    setIsLoggedIn(false);
    setUser(null);

    // 메인으로 이동하며 로그인 버튼에서 카카오 인증으로 연결
    window.location.href = "/";
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
            <Sparkles className="text-accent" size={24} />
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
