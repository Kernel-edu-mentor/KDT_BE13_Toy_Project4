import { FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff, MessageCircle } from "lucide-react";
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

const KAKAO_REST_API_KEY = "8bb25bd73474a68ce3fed3233542b7b0";  
const KAKAO_REDIRECT_URI = "http://localhost:4000/auth/kakao/callback";

const Auth = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (!username || !password) {
      setError("아이디와 비밀번호를 모두 입력해주세요.");
      return;
    }

    // Validation 검증 (백엔드와 동일한 규칙)
    if (isLogin) {
      // 로그인 시 검증
      if (username.length < 3 || username.length > 50) {
        setError("아이디는 3자 이상 50자 이하여야 합니다.");
        return;
      }
      if (password.length < 8 || password.length > 100) {
        setError("비밀번호는 8자 이상 100자 이하여야 합니다.");
        return;
      }
    } else {
      // 회원가입 시 검증
      if (username.length < 3 || username.length > 50) {
        setError("아이디는 3자 이상 50자 이하여야 합니다.");
        return;
      }
      if (password.length < 8 || password.length > 100) {
        setError("비밀번호는 8자 이상 100자 이하여야 합니다.");
        return;
      }
    }

    try {
      setLoading(true);
      if (isLogin) {
        const response = await postJson<LoginResponse>(
          "/auth/login",
          {
            username,
            password,
          },
          {
            headers: {
              "Content-Type": "application/json",
            },
          }
        );
        sessionStorage.setItem("ai-mentor-user", JSON.stringify(response.user));
        sessionStorage.setItem("ai-mentor-session", response.sessionId);
        navigate("/dashboard");
      } else {
        await postJson<LoginResponse["user"]>(
          "/auth/register",
          {
            username,
            password,
          },
          {
            headers: {
              "Content-Type": "application/json",
            },
          }
        );
        setSuccessMessage("회원가입이 완료되었습니다. 로그인해주세요.");
        setIsLogin(true);
      }
    } catch (err) {
      let message = "요청 처리 중 문제가 발생했습니다.";
      if (err instanceof ApiError) {
        message = err.message;
        // Validation 에러 메시지 개선 (400 Bad Request)
        if (err.status === 400) {
          // 입력값 확인으로 더 정확한 메시지 제공
          if (message.includes("Validation") || message.includes("Error count")) {
            if (password.length < 8) {
              message = "비밀번호는 8자 이상이어야 합니다.";
            } else if (password.length > 100) {
              message = "비밀번호는 100자 이하여야 합니다.";
            } else if (username.length < 3) {
              message = "아이디는 3자 이상이어야 합니다.";
            } else if (username.length > 50) {
              message = "아이디는 50자 이하여야 합니다.";
            } else {
              message = "입력값을 확인해주세요.";
            }
          }
        }
      }
      setError(message);
    } finally {
      setLoading(false);
    }
  };

const handleKakaoLogin = () => {
  console.log("카카오 로그인 버튼 클릭됨");
  console.log("REST API KEY:", KAKAO_REST_API_KEY);
  console.log("Redirect URI:", KAKAO_REDIRECT_URI);

  // ✅ URL을 직접 조합 (인코딩 안 함)
  const kakaoAuthUrl = `https://kauth.kakao.com/oauth/authorize?response_type=code&client_id=${KAKAO_REST_API_KEY}&redirect_uri=${KAKAO_REDIRECT_URI}`;

  console.log("✅ 최종 URL:", kakaoAuthUrl);

  // ✅ 실제로 이동
  window.location.href = kakaoAuthUrl;
};

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-foreground">
            {isLogin ? "로그인" : "회원가입"}
          </h1>
          {successMessage && <p className="text-sm text-green-600">{successMessage}</p>}
          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-sm text-muted-foreground">
                아이디
              </Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="아이디를 입력하세요"
                className="h-12 rounded-xl"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm text-muted-foreground">
                비밀번호
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="비밀번호를 입력하세요"
                  className="h-12 rounded-xl pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full h-12 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 font-medium"
          >
            {loading ? "처리 중..." : isLogin ? "로그인" : "가입하기"}
          </Button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="bg-background px-4 text-muted-foreground">또는</span>
            </div>
          </div>

          <div className="space-y-3">
            <Button
              type="button"
              variant="outline"
              className="w-full h-12 rounded-full border-border hover:bg-secondary"
              onClick={handleKakaoLogin}
              disabled={loading}
            >
              <div className="w-5 h-5 mr-2 bg-[#FEE500] rounded flex items-center justify-center">
                <MessageCircle size={14} className="text-[#3C1E1E]" fill="currentColor" />
              </div>
              카카오로 계속하기
            </Button>
          </div>
        </form>

        <div className="text-center text-sm text-muted-foreground">
          <a href="#" className="hover:underline">이용약관</a>
          {" | "}
          <a href="#" className="hover:underline">개인정보 보호 정책</a>
        </div>

        <div className="text-center text-sm">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-muted-foreground hover:text-foreground"
          >
            {isLogin ? "계정이 없으신가요? 가입하기" : "이미 계정이 있으신가요? 로그인"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Auth;
