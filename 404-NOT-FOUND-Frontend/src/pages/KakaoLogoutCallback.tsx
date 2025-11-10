import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

const KakaoLogoutCallback = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // 카카오 로그아웃 완료 후 메인 페이지로 이동
    navigate("/", { replace: true });
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-4">
        <p className="text-sm text-muted-foreground">로그아웃 중...</p>
      </div>
    </div>
  );
};

export default KakaoLogoutCallback;
