import { ChangeEvent, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ChevronLeft, ChevronRight, Copy, FileText, MessageSquare, MoreVertical, Paperclip, Plus, ThumbsDown, ThumbsUp } from "lucide-react";
import { ApiError, getJson, postForm, postJson } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface MaterialDto {
  id: number;
  title: string;
  fileType: string;
  parseStatus: "PENDING" | "COMPLETED" | "FAILED";
  pageCount?: number | null;
  createdAt?: string;
}

interface QAResponse {
  answer: string;
  sources: Array<{
    page: number;
    excerpt: string;
  }>;
  response_time_ms: number;
}

const initialChats = [
  { id: "intro", label: "새 채팅 1" },
  { id: "study", label: "React 학습하기" },
  { id: "algorithm", label: "알고리즘 질문" },
];

// 채팅 목록 불러오기 함수 (컴포넌트 외부)
const loadChatList = (): Array<{ id: string; label: string }> => {
  try {
    const chatsStr = sessionStorage.getItem("qa-chat-list");
    if (chatsStr) {
      return JSON.parse(chatsStr) as Array<{ id: string; label: string }>;
    }
  } catch (error) {
    console.error("채팅 목록 불러오기 실패:", error);
  }
  return initialChats;
};

const Dashboard = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [chats, setChats] = useState<Array<{ id: string; label: string }>>(() => loadChatList());
  const [selectedChatId, setSelectedChatId] = useState<string | null>(() => {
    const savedChats = loadChatList();
    const savedSelectedId = sessionStorage.getItem("qa-selected-chat-id");
    return savedSelectedId || savedChats[0]?.id || null;
  });
  const [activeTab, setActiveTab] = useState<"qa" | "quiz">("qa");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [messageFeedback, setMessageFeedback] = useState<Record<string, "like" | "dislike" | null>>({});
  const [materialId, setMaterialId] = useState<string | null>(() => sessionStorage.getItem("ai-mentor-material-id"));
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [qaError, setQaError] = useState<string | null>(null);
  const [materials, setMaterials] = useState<MaterialDto[]>([]);
  const [materialsLoading, setMaterialsLoading] = useState(false);
  const [showMaterialSelector, setShowMaterialSelector] = useState(false);
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editingChatName, setEditingChatName] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const chatNameInputRef = useRef<HTMLInputElement | null>(null);

  const hasMessages = messages.length > 0;

  // QA 히스토리 저장 함수
  const saveQAHistory = (chatId: string, messages: Message[]) => {
    try {
      const historyKey = `qa-history-${chatId}`;
      sessionStorage.setItem(historyKey, JSON.stringify(messages));
    } catch (error) {
      console.error("QA 히스토리 저장 실패:", error);
    }
  };

  // QA 히스토리 불러오기 함수
  const loadQAHistory = (chatId: string): Message[] => {
    try {
      const historyKey = `qa-history-${chatId}`;
      const historyStr = sessionStorage.getItem(historyKey);
      if (historyStr) {
        return JSON.parse(historyStr) as Message[];
      }
    } catch (error) {
      console.error("QA 히스토리 불러오기 실패:", error);
    }
    return [];
  };

  // 채팅 목록 저장 함수
  const saveChatList = (chats: Array<{ id: string; label: string }>) => {
    try {
      sessionStorage.setItem("qa-chat-list", JSON.stringify(chats));
    } catch (error) {
      console.error("채팅 목록 저장 실패:", error);
    }
  };

  // Material 목록 조회
  const fetchMaterials = async () => {
    try {
      setMaterialsLoading(true);
      const materialsList = await getJson<MaterialDto[]>("/materials");
      setMaterials(materialsList);
    } catch (error) {
      console.error("Material 목록 조회 실패:", error);
    } finally {
      setMaterialsLoading(false);
    }
  };

  useEffect(() => {
    fetchMaterials();
  }, []);

  // 분석 중인 자료가 있으면 주기적으로 상태 확인
  useEffect(() => {
    const hasPendingMaterials = materials.some((m) => m.parseStatus === "PENDING");
    if (!hasPendingMaterials) return;

    const intervalId = setInterval(() => {
      fetchMaterials();
    }, 3000); // 3초마다 확인

    return () => clearInterval(intervalId);
  }, [materials]);

  // Material 선택 핸들러
  const handleSelectMaterial = (selectedMaterial: MaterialDto) => {
    if (selectedMaterial.parseStatus !== "COMPLETED") {
      if (selectedMaterial.parseStatus === "PENDING") {
        setUploadMessage("자료가 아직 분석 중입니다. 분석이 완료되면 자동으로 선택됩니다.");
        setMaterialId(null);
        setShowMaterialSelector(false);
      } else {
        setUploadMessage("자료 분석에 실패했습니다. 새로 업로드해주세요.");
      }
      return;
    }
    const newMaterialId = String(selectedMaterial.id);
    sessionStorage.setItem("ai-mentor-material-id", newMaterialId);
    setMaterialId(newMaterialId);
    setShowMaterialSelector(false);
    setUploadMessage(`"${selectedMaterial.title}" 자료가 선택되었습니다.`);
    setMessages([]);
  };

  // 선택한 materialId의 자료가 분석 완료되면 자동으로 선택
  useEffect(() => {
    if (!materialId) return;

    const material = materials.find((m) => String(m.id) === materialId);
    if (material && material.parseStatus === "COMPLETED") {
      if (uploadMessage?.includes("분석이 진행 중")) {
        setUploadMessage(`"${material.title}" 자료 분석이 완료되었습니다. 이제 질문할 수 있습니다!`);
      }
    }
  }, [materials, materialId]);

  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", file.name.replace(/\.[^.]+$/, ""));

    setUploadMessage("학습 자료 업로드 중입니다...");
    try {
      const material = await postForm<MaterialDto>("/materials/upload", formData);
      if (material?.id) {
        const newMaterialId = String(material.id);
        sessionStorage.setItem("ai-mentor-material-id", newMaterialId);
        setMaterialId(newMaterialId);
        setUploadMessage("자료 업로드가 완료되었습니다. 분석이 진행 중입니다. 잠시만 기다려주세요...");
        fetchMaterials();
      } else {
        setUploadMessage("업로드는 완료되었지만 자료 정보를 확인하지 못했습니다.");
      }
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "자료 업로드에 실패했습니다.";
      setUploadMessage(message);
    } finally {
      event.target.value = "";
    }
  };

  const handleCopy = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      console.log("복사 완료:", content);
    } catch (err) {
      console.error("복사 실패:", err);
    }
  };

  const handleLike = (id: string) =>
    setMessageFeedback((prev) => ({
      ...prev,
      [id]: prev[id] === "like" ? null : "like",
    }));

  const handleDislike = (id: string) =>
    setMessageFeedback((prev) => ({
      ...prev,
      [id]: prev[id] === "dislike" ? null : "dislike",
    }));

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isSending) return;

    if (!materialId) {
      setUploadMessage("먼저 학습 자료를 업로드해주세요.");
      return;
    }

    const question = inputValue.trim();
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
    };

    setMessages((prev) => {
      const updatedMessages = [...prev, userMessage];
      if (selectedChatId) {
        saveQAHistory(selectedChatId, updatedMessages);
      }
      return updatedMessages;
    });
    setInputValue("");
    setIsSending(true);
    setQaError(null);

    try {
      const response = await postJson<QAResponse>("/qa/ask", {
        material_id: Number(materialId),
        question,
      });

      const answerMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer,
      };
      setMessages((prev) => {
        const updatedMessages = [...prev, answerMessage];
        if (selectedChatId) {
          saveQAHistory(selectedChatId, updatedMessages);
        }
        return updatedMessages;
      });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "답변 생성 중 문제가 발생했습니다.";
      setQaError(message);
      setMessages((prev) => {
        const errorMessage: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `오류: ${message}`,
        };
        const updatedMessages = [...prev, errorMessage];
        if (selectedChatId) {
          saveQAHistory(selectedChatId, updatedMessages);
        }
        return updatedMessages;
      });
    } finally {
      setIsSending(false);
    }
  };

  const handleStartNewChat = () => {
    const newChat = {
      id: `chat-${Date.now()}`,
      label: `새 채팅 ${chats.length + 1}`,
    };
    const updatedChats = [newChat, ...chats];
    setChats(updatedChats);
    saveChatList(updatedChats);
    setSelectedChatId(newChat.id);
    sessionStorage.setItem("qa-selected-chat-id", newChat.id);
    setMessages([]);
    setInputValue("");
  };

  const handleSelectChat = (chatId: string) => {
    if (editingChatId !== chatId) {
      setSelectedChatId(chatId);
      sessionStorage.setItem("qa-selected-chat-id", chatId);
      const history = loadQAHistory(chatId);
      setMessages(history);
      setInputValue("");
    }
  };

  const handleStartEditChat = (chatId: string, currentLabel: string) => {
    setEditingChatId(chatId);
    setEditingChatName(currentLabel);
    setTimeout(() => {
      chatNameInputRef.current?.focus();
      chatNameInputRef.current?.select();
    }, 0);
  };

  const handleSaveChatName = (chatId: string) => {
    if (!editingChatName.trim()) {
      const chat = chats.find((c) => c.id === chatId);
      if (chat) {
        setEditingChatName(chat.label);
      }
      setEditingChatId(null);
      return;
    }

    const updatedChats = chats.map((chat) =>
      chat.id === chatId ? { ...chat, label: editingChatName.trim() } : chat
    );
    setChats(updatedChats);
    saveChatList(updatedChats);
    setEditingChatId(null);
    setEditingChatName("");
  };

  const handleCancelEditChat = () => {
    setEditingChatId(null);
    setEditingChatName("");
  };

  // 컴포넌트 마운트 시 저장된 채팅 목록과 선택된 채팅 불러오기
  useEffect(() => {
    const savedChats = loadChatList();
    if (savedChats.length > 0) {
      setChats(savedChats);
    }
    
    const savedSelectedId = sessionStorage.getItem("qa-selected-chat-id");
    if (savedSelectedId) {
      setSelectedChatId(savedSelectedId);
      const history = loadQAHistory(savedSelectedId);
      if (history.length > 0) {
        setMessages(history);
      }
    } else if (savedChats.length > 0) {
      const firstChatId = savedChats[0].id;
      setSelectedChatId(firstChatId);
      sessionStorage.setItem("qa-selected-chat-id", firstChatId);
      const history = loadQAHistory(firstChatId);
      if (history.length > 0) {
        setMessages(history);
      }
    }
  }, []);

  // selectedChatId 변경 시 히스토리 불러오기
  useEffect(() => {
    if (selectedChatId) {
      const history = loadQAHistory(selectedChatId);
      setMessages(history);
    }
  }, [selectedChatId]);

  return (
    <div className="flex min-h-[100dvh] bg-white overflow-hidden">
      <div className="relative hidden min-h-[100dvh] md:flex">
        <aside
          className={`flex min-h-[100dvh] flex-col border-r border-gray-200 bg-[#f7f7f8] py-8 transition-all duration-300 ${
            sidebarCollapsed
              ? "w-0 px-0 opacity-0 pointer-events-none"
              : "w-72 px-6 opacity-100"
          }`}
        >
          {!sidebarCollapsed && (
            <>
              <button
                type="button"
                onClick={handleStartNewChat}
                className="mb-4 flex items-center gap-2 rounded-full border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-100"
              >
                <Plus size={16} />
                새 채팅
              </button>

              <ScrollArea className="flex-1 overflow-y-auto">
                <div className="space-y-1">
                  {chats.map((chat) => {
                    const isActive = chat.id === selectedChatId;
                    const isEditing = editingChatId === chat.id;
                    return (
                      <div
                        key={chat.id}
                        className={`group flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors ${
                          isActive && !isEditing
                            ? "bg-black text-white"
                            : "bg-transparent text-gray-700 hover:bg-gray-100"
                        }`}
                      >
                        <MessageSquare
                          size={16}
                          className={`transition-colors flex-shrink-0 ${
                            isActive && !isEditing ? "text-white" : "text-gray-500 group-hover:text-gray-700"
                          }`}
                        />
                        {isEditing ? (
                          <Input
                            ref={chatNameInputRef}
                            value={editingChatName}
                            onChange={(e) => setEditingChatName(e.target.value)}
                            onBlur={() => handleSaveChatName(chat.id)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                e.preventDefault();
                                handleSaveChatName(chat.id);
                              } else if (e.key === "Escape") {
                                e.preventDefault();
                                handleCancelEditChat();
                              }
                            }}
                            onClick={(e) => e.stopPropagation()}
                            className="h-7 px-2 text-sm bg-white border-gray-300 focus-visible:ring-2 focus-visible:ring-blue-500 flex-1"
                          />
                        ) : (
                          <>
                            <button
                              type="button"
                              onClick={() => handleSelectChat(chat.id)}
                              className="flex-1 text-left truncate"
                            >
                              <span className="truncate">{chat.label}</span>
                            </button>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <button
                                  type="button"
                                  onClick={(e) => e.stopPropagation()}
                                  className={`flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-gray-200 ${
                                    isActive ? "text-white hover:bg-gray-800" : "text-gray-500"
                                  }`}
                                >
                                  <MoreVertical size={16} />
                                </button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end" className="w-32">
                                <DropdownMenuItem onClick={() => handleStartEditChat(chat.id, chat.label)}>
                                  이름 변경
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </>
                        )}
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            </>
          )}
        </aside>

        <div className="flex min-h-[100dvh] flex-col items-start justify-start bg-white px-2 py-8">
          <button
            type="button"
            onClick={() => setSidebarCollapsed((prev) => !prev)}
            className="flex h-8 w-8 items-center justify-center rounded-full border border-gray-300 bg-white text-gray-600 shadow-sm transition hover:bg-gray-100"
            aria-label={sidebarCollapsed ? "사이드바 열기" : "사이드바 접기"}
          >
            {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>
      </div>

      <div className="relative flex min-h-[100dvh] flex-1 flex-col">
        <input ref={fileInputRef} type="file" onChange={handleFileChange} className="hidden" />

        <header className="flex justify-between items-center gap-3 px-6 py-6">
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowMaterialSelector(!showMaterialSelector)}
              className="flex items-center gap-2 px-4 py-2 rounded-full border border-gray-300 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
            >
              <FileText size={16} />
              <span>
                {materialId
                  ? materials.find((m) => String(m.id) === materialId)?.title || `자료 #${materialId}`
                  : "자료 선택"}
              </span>
            </button>
            {showMaterialSelector && (
              <div className="absolute top-full left-0 mt-2 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-10 max-h-96 overflow-y-auto">
                {materialsLoading ? (
                  <div className="p-4 text-center text-sm text-gray-500">로딩 중...</div>
                ) : materials.length === 0 ? (
                  <div className="p-4 text-center text-sm text-gray-500">업로드된 자료가 없습니다.</div>
                ) : (
                  <div className="py-2">
                    {materials.map((material) => {
                      const isSelected = String(material.id) === materialId;
                      return (
                        <button
                          key={material.id}
                          type="button"
                          onClick={() => handleSelectMaterial(material)}
                          className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition ${
                            isSelected ? "bg-blue-50 border-l-4 border-blue-500" : ""
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 truncate">{material.title}</p>
                              <div className="flex items-center gap-2 mt-1">
                                <span
                                  className={`text-xs px-2 py-0.5 rounded-full ${
                                    material.parseStatus === "COMPLETED"
                                      ? "bg-green-100 text-green-700"
                                      : material.parseStatus === "PENDING"
                                      ? "bg-yellow-100 text-yellow-700"
                                      : "bg-red-100 text-red-700"
                                  }`}
                                >
                                  {material.parseStatus === "COMPLETED"
                                    ? "완료"
                                    : material.parseStatus === "PENDING"
                                    ? "분석 중"
                                    : "실패"}
                                </span>
                                {material.pageCount && (
                                  <span className="text-xs text-gray-500">{material.pageCount}페이지</span>
                                )}
                              </div>
                            </div>
                            {isSelected && <span className="text-blue-500 text-xs">✓</span>}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => {
                setActiveTab("qa");
                navigate("/dashboard");
              }}
              className={`px-5 py-2 rounded-full text-sm font-medium transition ${
                activeTab === "qa"
                  ? "bg-black text-white hover:opacity-90"
                  : "border border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
            >
              질문하기
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveTab("quiz");
                navigate("/quiz");
              }}
              className={`px-5 py-2 rounded-full text-sm font-medium transition ${
                activeTab === "quiz"
                  ? "bg-black text-white hover:opacity-90"
                  : "border border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
            >
              퀴즈 풀기
            </button>
          </div>
        </header>

        <main className="relative flex-1 flex flex-col px-4 md:px-6 pb-0">
          {hasMessages ? (
            <ScrollArea className="flex-1 px-1">
              <div className="max-w-4xl mx-auto w-full space-y-4 py-4 pb-32">
                {messages.map((message) => {
                  const isUser = message.role === "user";
                  const feedback = messageFeedback[message.id];
                  return (
                    <div
                      key={message.id}
                      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
                    >
                      <div className="flex max-w-[80%] flex-col">
                        <div
                          className={`rounded-2xl px-5 py-3 text-sm shadow-sm ${
                            isUser ? "bg-black text-white" : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {message.content}
                        </div>
                        {message.role === "assistant" && (
                          <div className="mt-3 flex items-center justify-between border-t border-gray-100 pt-2 text-xs text-gray-500">
                            <div className="flex gap-4">
                              <button
                                type="button"
                                onClick={() => handleCopy(message.content)}
                                className="flex items-center gap-1 transition hover:text-gray-700"
                              >
                                <Copy size={14} />
                                <span>복사</span>
                              </button>

                              <button
                                type="button"
                                onClick={() => handleLike(message.id)}
                                className={`flex items-center gap-1 transition hover:text-green-600 ${
                                  feedback === "like" ? "text-green-600" : ""
                                }`}
                              >
                                <ThumbsUp size={14} />
                                <span>좋아요</span>
                              </button>

                              <button
                                type="button"
                                onClick={() => handleDislike(message.id)}
                                className={`flex items-center gap-1 transition hover:text-red-600 ${
                                  feedback === "dislike" ? "text-red-600" : ""
                                }`}
                              >
                                <ThumbsDown size={14} />
                                <span>싫어요</span>
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>
          ) : (
            <div className="flex flex-1 items-center justify-center px-4">
              <div className="w-full max-w-xl text-center space-y-4">
                <h2 className="text-2xl font-semibold text-gray-800">학습을 시작할 준비가 되셨나요?</h2>
                <div className="relative">
                  <button
                    type="button"
                    onClick={handleFileButtonClick}
                    className="absolute left-3 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-transparent text-gray-500 transition hover:text-gray-700"
                    aria-label="파일 업로드"
                  >
                    <Paperclip size={16} />
                  </button>
                  <Input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                    placeholder="무엇이든 물어보세요"
                    className="h-12 rounded-full border border-gray-300 pl-14 pr-6 text-base text-gray-700 shadow-inner focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                  />
                </div>
                {uploadMessage && <p className="text-sm text-blue-600">{uploadMessage}</p>}
                {qaError && <p className="text-xs text-red-500">{qaError}</p>}
                <p className="text-sm text-gray-500 mt-2">
                  AI와 함께하는 스마트한 학습. 질문하고, 배우고, 퀴즈로 테스트하세요.
                </p>
              </div>
            </div>
          )}

          {hasMessages && (
            <div className="sticky bottom-0 left-0 right-0 bg-white px-4 py-4">
              <div className="relative max-w-3xl mx-auto">
                <button
                  type="button"
                  onClick={handleFileButtonClick}
                  className="absolute left-3 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-transparent text-gray-500 transition hover:text-gray-700"
                  aria-label="파일 업로드"
                >
                  <Paperclip size={16} />
                </button>
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  placeholder="무엇이든 물어보세요"
                  className="h-12 rounded-full border border-gray-300 pl-14 pr-6 text-base text-gray-700 shadow-inner focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                  disabled={isSending}
                />
              </div>
              {uploadMessage && <p className="mt-2 text-sm text-blue-600">{uploadMessage}</p>}
              {qaError && <p className="text-xs text-red-500">{qaError}</p>}
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default Dashboard;
