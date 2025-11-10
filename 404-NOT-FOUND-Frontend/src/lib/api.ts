const API_BASE_PATH = "/api";

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { headers, ...rest } = init;
  const response = await fetch(`${API_BASE_PATH}${path}`, {
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(headers ?? {}),
    },
    ...rest,
  });

  if (!response.ok) {
    const message = await extractErrorMessage(response);
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }
  return (await response.text()) as T;
}

async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data === "string") return parseValidationError(data);
    if (data?.message) return parseValidationError(data.message);
    if (data?.detail) return parseValidationError(data.detail);
    // Spring Validation 에러 응답 형식 처리
    if (data?.errors) {
      const fieldErrors = data.errors as Array<{ field: string; message: string }>;
      if (fieldErrors.length > 0) {
        return parseValidationError(fieldErrors[0].message || JSON.stringify(fieldErrors[0]));
      }
    }
  } catch (error) {
    // ignore json parse errors
  }
  return response.statusText || "요청에 실패했습니다.";
}

function parseValidationError(errorMessage: string): string {
  if (!errorMessage) return "입력값을 확인해주세요.";
  
  // Spring Validation 기본 에러 메시지 파싱
  if (errorMessage.includes("password") || errorMessage.includes("Password")) {
    if (errorMessage.includes("Size") || errorMessage.includes("size")) {
      return "비밀번호는 8자 이상이어야 합니다.";
    }
    if (errorMessage.includes("NotBlank") || errorMessage.includes("null") || errorMessage.includes("empty")) {
      return "비밀번호를 입력해주세요.";
    }
    return "비밀번호가 올바르지 않습니다.";
  }
  
  if (errorMessage.includes("username") || errorMessage.includes("Username")) {
    if (errorMessage.includes("Size") || errorMessage.includes("size")) {
      return "아이디는 3자 이상 50자 이하여야 합니다.";
    }
    if (errorMessage.includes("NotBlank") || errorMessage.includes("null") || errorMessage.includes("empty")) {
      return "아이디를 입력해주세요.";
    }
    return "아이디가 올바르지 않습니다.";
  }
  
  // Validation failed 메시지 처리
  if (errorMessage.includes("Validation failed") || errorMessage.includes("Error count")) {
    return "입력값을 확인해주세요.";
  }
  
  return errorMessage;
}

export async function getJson<T>(path: string, init?: RequestInit) {
  return request<T>(path, {
    method: "GET",
    ...init,
  });
}

export async function postJson<T>(path: string, body: unknown, init?: RequestInit) {
  return request<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
}

export async function postForm<T>(path: string, formData: FormData, init?: RequestInit) {
  return request<T>(path, {
    method: "POST",
    body: formData,
    ...init,
  });
}

export async function logout() {
  try {
    await postJson('/auth/logout', {});
  } catch (error) {
    // 로그아웃 요청 실패해도 로컬 데이터는 정리
    console.error('Logout request failed:', error);
  } finally {
    // 로컬 세션 데이터 정리
    sessionStorage.removeItem('ai-mentor-user');
    sessionStorage.removeItem('ai-mentor-session');
  }
}

export { ApiError };
