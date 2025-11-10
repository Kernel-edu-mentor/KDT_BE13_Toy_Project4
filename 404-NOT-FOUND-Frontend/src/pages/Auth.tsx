import { Button } from "@/components/ui/button";

const KAKAO_REST_API_KEY = import.meta.env.VITE_KAKAO_REST_API_KEY;
const KAKAO_REDIRECT_URI = import.meta.env.VITE_KAKAO_REDIRECT_URI;

const KakaoIcon = () => (
  <span aria-hidden className="flex h-7 w-7 items-center justify-center rounded-full bg-yellow-400">
    <svg
      viewBox="0 0 24 24"
      className="h-4 w-4 text-[#3C1E1E]"
      fill="currentColor"
    >
      <path d="M12 4C7.029 4 3 7.214 3 11.18c0 2.632 1.778 4.939 4.467 6.21-.175.619-.612 2.17-.702 2.514-.11.43.158.424.332.308.136-.09 2.152-1.47 3.023-2.064.624.09 1.267.133 1.88.133 4.97 0 9-3.213 9-7.18C20 7.214 16.97 4 12 4Z" />
    </svg>
  </span>
);

const Auth = () => {
  const handleKakaoLogin = () => {
    const kakaoAuthUrl = `https://kauth.kakao.com/oauth/authorize?response_type=code&client_id=${KAKAO_REST_API_KEY}&redirect_uri=${KAKAO_REDIRECT_URI}`;
    window.location.href = kakaoAuthUrl;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-6 py-12">
      <Button
        onClick={handleKakaoLogin}
        className="w-full max-w-md h-12 rounded-full bg-yellow-400 text-gray-900 hover:bg-yellow-500 font-semibold flex items-center justify-center gap-2"
      >
        <KakaoIcon />
        카카오 로그인하기
      </Button>
    </div>
  );
};

export default Auth;
