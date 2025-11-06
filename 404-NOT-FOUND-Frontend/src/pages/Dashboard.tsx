import { ChangeEvent, useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Copy, FileText, MessageSquare, Paperclip, Pencil, Plus, ThumbsDown, ThumbsUp, Sparkles } from "lucide-react";
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

interface QASessionSummary {
  id: number;
  materialId: number | null;
  materialTitle: string | null;
  question: string;
  answer: string;
  responseTimeMs?: number | null;
  sources?: QAResponse["sources"];
  createdAt?: string;
}

interface QAChat {
  id: number;
  title: string;
  materialId: number | null;
  materialTitle: string | null;
  createdAt?: string;
}

const buildChatLabel = (chat: QAChat) => {
  const rawTitle = chat.title?.trim();
  if (rawTitle) return rawTitle;
  if (chat.materialTitle) return chat.materialTitle;
  return `채팅 ${chat.id}`;
};

const convertSessionsToMessages = (sessions: QASessionSummary[]): Message[] => {
  return sessions.flatMap((session) => {
    const history: Message[] = [];
    if (session.question) {
      history.push({
        id: `session-${session.id}-question`,
        role: "user",
        content: session.question,
      });
    }
    if (session.answer) {
      history.push({
        id: `session-${session.id}-answer`,
        role: "assistant",
        content: session.answer,
      });
    }
    return history;
  });
};

const Dashboard = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [chats, setChats] = useState<QAChat[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(() =>
    sessionStorage.getItem("qa-last-chat-id")
  );
  const [activeTab, setActiveTab] = useState<"qa" | "quiz">("qa");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [messageFeedback, setMessageFeedback] = useState<Record<string, "like" | "dislike" | null>>({});
  const [chatHistories, setChatHistories] = useState<Record<string, Message[]>>({});
  const [chatsLoading, setChatsLoading] = useState(false);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [materialId, setMaterialId] = useState<string | null>(() => sessionStorage.getItem("ai-mentor-material-id"));
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [qaError, setQaError] = useState<string | null>(null);
  const [materials, setMaterials] = useState<MaterialDto[]>([]);
  const [materialsLoading, setMaterialsLoading] = useState(false);
  const [showMaterialSelector, setShowMaterialSelector] = useState(false);
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editingChatName, setEditingChatName] = useState<string>("");
  const [generatingFromQA, setGeneratingFromQA] = useState<string | null>(null); // QA 기반 문제 생성 중인 메시지 ID
  const [showDifficultyDialog, setShowDifficultyDialog] = useState(false); // 난이도 선택 Dialog 표시 여부
  const [selectedDifficultyForQA, setSelectedDifficultyForQA] = useState<"BEGINNER" | "INTERMEDIATE" | "ADVANCED">("BEGINNER"); // 선택한 난이도
  const [selectedAnswerMessageId, setSelectedAnswerMessageId] = useState<string | null>(null); // 선택한 답변 메시지 ID
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const chatNameInputRef = useRef<HTMLInputElement | null>(null);
  const lastMessageRef = useRef<HTMLDivElement | null>(null);

  const hasMessages = messages.length > 0;

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

  const fetchChats = useCallback(async () => {
    try {
      setChatsLoading(true);
      const query = materialId ? `?materialId=${materialId}` : "";
      const chatList = await getJson<QAChat[]>(`/qa/chats${query}`);
      setChats(chatList);
      return chatList;
    } catch (error) {
      console.error("QA 채팅 목록 조회 실패:", error);
      return [];
    } finally {
      setChatsLoading(false);
    }
  }, [materialId]);

  const loadChatSessions = useCallback(async (chatId: string) => {
    try {
      setSessionsLoading(true);
      const sessionList = await getJson<QASessionSummary[]>(`/qa/chats/${chatId}/sessions`);
      const history = convertSessionsToMessages(sessionList);
      setChatHistories((prev) => ({
        ...prev,
        [chatId]: history,
      }));
      setMessages(history);
    } catch (error) {
      console.error("채팅 히스토리 조회 실패:", error);
      setQaError("채팅 기록을 불러오지 못했습니다.");
    } finally {
      setSessionsLoading(false);
    }
  }, []);

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
    setSelectedChatId(null);
    sessionStorage.removeItem("qa-last-chat-id");
    setChatHistories({});
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
  }, [materials, materialId, uploadMessage]);

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

    let chatId = selectedChatId;

    if (!chatId) {
      try {
        const chat = await postJson<QAChat>("/qa/chats", {
          title: `새 채팅 ${chats.length + 1}`,
          materialId: Number(materialId),
        });
        chatId = String(chat.id);
        setSelectedChatId(chatId);
        sessionStorage.setItem("qa-last-chat-id", chatId);
        await fetchChats();
        setMessages([]);
        setChatHistories((prev) => ({
          ...prev,
          [chatId]: [],
        }));
      } catch (error) {
        console.error("새 채팅 생성 실패:", error);
        setQaError("새 채팅을 생성하지 못했습니다. 잠시 후 다시 시도해주세요.");
        return;
      }
    }

    if (!chatId) {
      setQaError("채팅을 생성하지 못했습니다.");
      return;
    }

    const chatKey = chatId;
    sessionStorage.setItem("qa-last-chat-id", chatKey);

    const question = inputValue.trim();
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
    };

    setMessages((prev) => {
      const baseMessages = chatHistories[chatKey] ?? prev;
      const updated = [...baseMessages, userMessage];
      setChatHistories((histories) => ({
        ...histories,
        [chatKey]: updated,
      }));
      requestAnimationFrame(() => {
        lastMessageRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
      return updated;
    });
    setInputValue("");
    setIsSending(true);
    setQaError(null);

    try {
      const response = await postJson<QAResponse>("/qa/ask", {
        material_id: Number(materialId),
        question,
        chat_id: Number(chatId),
      });

      const answerMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer,
      };
      setMessages((prev) => {
        const updated = [...prev, answerMessage];
        setChatHistories((histories) => ({
          ...histories,
          [chatKey]: updated,
        }));
        requestAnimationFrame(() => {
          lastMessageRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
        return updated;
      });

      void fetchChats();
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "답변 생성 중 문제가 발생했습니다.";
      setQaError(message);
      setMessages((prev) => {
        const errorMessage: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `오류: ${message}`,
        };
        const updated = [...prev, errorMessage];
        setChatHistories((histories) => ({
          ...histories,
          [chatId]: updated,
        }));
        return updated;
      });
    } finally {
      setIsSending(false);
    }
  };

  useEffect(() => {
    lastMessageRef.current?.scrollIntoView({ behavior: "auto", block: "start" });
  }, [messages, selectedChatId]);

  const handleOpenDifficultyDialog = (answerMessageId: string) => {
    setSelectedAnswerMessageId(answerMessageId);
    setShowDifficultyDialog(true);
  };

  const handleGenerateProblemsFromQA = async () => {
    if (!selectedAnswerMessageId || !materialId) {
      setQaError("자료를 선택해주세요.");
      return;
    }

    // 질문과 답변 찾기
    const answerMessage = messages.find((m) => m.id === selectedAnswerMessageId);
    if (!answerMessage || answerMessage.role !== "assistant") {
      setQaError("답변 메시지를 찾을 수 없습니다.");
      return;
    }

    // 이전 사용자 메시지가 질문
    const answerIndex = messages.findIndex((m) => m.id === selectedAnswerMessageId);
    const questionMessage = answerIndex > 0 ? messages[answerIndex - 1] : null;
    if (!questionMessage || questionMessage.role !== "user") {
      setQaError("질문을 찾을 수 없습니다.");
      return;
    }

    try {
      setGeneratingFromQA(selectedAnswerMessageId);
      setShowDifficultyDialog(false);
      setQaError(null);

      const response = await postJson("/problems/generated", {
        materialId: Number(materialId),
        difficulty: selectedDifficultyForQA,
        problemCount: 5,
        question: questionMessage.content,
        answer: answerMessage.content,
        topic: questionMessage.content, // 질문 내용을 주제로 사용
      });

      // 문제 생성 성공 시 퀴즈 페이지로 이동
      navigate("/quiz");
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "문제 생성 중 오류가 발생했습니다.";
      setQaError(message);
      console.error("QA 기반 문제 생성 에러:", error);
    } finally {
      setGeneratingFromQA(null);
      setSelectedAnswerMessageId(null);
    }
  };

  const handleStartNewChat = async () => {
    if (!materialId) {
      setUploadMessage("먼저 학습 자료를 선택해주세요.");
      return;
    }

    const defaultTitle = `새 채팅 ${chats.length + 1}`;

    try {
      const chat = await postJson<QAChat>("/qa/chats", {
        title: defaultTitle,
        materialId: Number(materialId),
      });
      const chatId = String(chat.id);
      await fetchChats();
      setSelectedChatId(chatId);
      sessionStorage.setItem("qa-last-chat-id", chatId);
      setMessages([]);
      setInputValue("");
      setChatHistories((prev) => ({
        ...prev,
        [chatId]: [],
      }));
    } catch (error) {
      console.error("새 채팅 생성 실패:", error);
      setQaError("새 채팅을 생성하지 못했습니다.");
    }
  };

  const handleSelectChat = (chatId: string) => {
    if (editingChatId !== chatId) {
      setSelectedChatId(chatId);
      sessionStorage.setItem("qa-last-chat-id", chatId);
      const cachedMessages = chatHistories[chatId];
      if (cachedMessages) {
        setMessages(cachedMessages);
      } else {
        setMessages([]);
      }
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

  const handleDeleteChat = async (chatId: string, label: string) => {
    const confirmDelete = window.confirm(`'${label}' 채팅을 삭제하시겠습니까?`);
    if (!confirmDelete) {
      return;
    }

    try {
      const response = await fetch(`/api/qa/chats/${chatId}`, {
        method: "DELETE",
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || "채팅 삭제에 실패했습니다.");
      }

      setChats((prevChats) => {
        const updatedChats = prevChats.filter((chat) => String(chat.id) !== chatId);

        setSelectedChatId((prevSelected) => {
          if (prevSelected !== chatId) {
            return prevSelected;
          }

          if (updatedChats.length === 0) {
            setMessages([]);
            sessionStorage.removeItem("qa-last-chat-id");
            return null;
          }

          const nextId = String(updatedChats[0].id);
          sessionStorage.setItem("qa-last-chat-id", nextId);
          const cached = chatHistories[nextId];
          if (cached) {
            setMessages(cached);
          } else {
            setMessages([]);
            void loadChatSessions(nextId);
          }
          return nextId;
        });

        return updatedChats;
      });

      setChatHistories((prev) => {
        const { [chatId]: _, ...rest } = prev;
        return rest;
      });
      await fetchChats();
    } catch (error) {
      console.error("채팅 삭제 실패:", error);
      setQaError(error instanceof Error ? error.message : "채팅을 삭제하지 못했습니다.");
    }
  };

  const handleSaveChatName = (chatId: string) => {
    if (!editingChatName.trim()) {
      const chat = chats.find((c) => String(c.id) === chatId);
      if (chat) {
        setEditingChatName(buildChatLabel(chat));
      }
      setEditingChatId(null);
      return;
    }

    const updatedTitle = editingChatName.trim();

    const updateChatTitle = async () => {
      try {
        await postJson<QAChat>(`/qa/chats/${chatId}`, { title: updatedTitle }, { method: "PATCH" });
        await fetchChats();
      } catch (error) {
        console.error("채팅 제목 변경 실패:", error);
        setQaError("채팅 이름을 변경하지 못했습니다.");
      } finally {
        setEditingChatId(null);
        setEditingChatName("");
      }
    };

    updateChatTitle();
  };

  const handleCancelEditChat = () => {
    setEditingChatId(null);
    setEditingChatName("");
  };

  useEffect(() => {
    let isMounted = true;

    const loadChats = async () => {
      const chatList = await fetchChats();
      if (!isMounted) return;

      if (chatList.length === 0) {
        setSelectedChatId(null);
        sessionStorage.removeItem("qa-last-chat-id");
        setMessages([]);
        return;
      }

      setSelectedChatId((prev) => {
        if (prev && chatList.some((chat) => String(chat.id) === prev)) {
          sessionStorage.setItem("qa-last-chat-id", prev);
          return prev;
        }
        const latestId = String(chatList[0].id);
        sessionStorage.setItem("qa-last-chat-id", latestId);
        return latestId;
      });
    };

    loadChats();

    return () => {
      isMounted = false;
    };
  }, [fetchChats]);

  useEffect(() => {
    if (!selectedChatId) return;

    const cached = chatHistories[selectedChatId];
    if (cached) {
      setMessages(cached);
      return;
    }

    loadChatSessions(selectedChatId);
  }, [selectedChatId, chatHistories, loadChatSessions]);

  return (
    <div className="flex flex-1 min-h-[calc(100vh-4rem)] bg-white overflow-hidden">
      <div className="relative hidden min-h-full md:flex">
        <aside
          className={`flex min-h-full flex-col border-r border-gray-200 bg-[#f7f7f8] py-8 transition-all duration-300 ${
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
                className="mb-4 flex items-center gap-2 rounded-xl border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-100"
              >
                <Plus size={16} />
                새 채팅
              </button>

              <ScrollArea className="flex-1 overflow-y-auto">
                <div className="space-y-1">
                  {chatsLoading ? (
                    <div className="px-3 py-2 text-sm text-gray-500">채팅 목록을 불러오는 중...</div>
                  ) : chats.length === 0 ? (
                    <div className="px-3 py-2 text-sm text-gray-500">아직 생성된 채팅이 없습니다.</div>
                  ) : (
                    chats.map((chat) => {
                      const chatId = String(chat.id);
                      const isActive = chatId === selectedChatId;
                      const isEditing = editingChatId === chatId;
                      const label = buildChatLabel(chat);
                      const containerClasses = `bg-transparent hover:bg-gray-100 ${
                        isActive && !isEditing ? "text-blue-600" : "text-gray-700"
                      }`;
                      const iconClasses = isActive && !isEditing
                        ? "text-blue-600"
                        : "text-gray-500 group-hover:text-gray-700";
                      return (
                        <div
                          key={chat.id}
                          className={`group flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors ${containerClasses}`}
                        >
                          <MessageSquare
                            size={16}
                            className={`transition-colors flex-shrink-0 ${iconClasses}`}
                          />
                          {isEditing ? (
                            <Input
                              ref={chatNameInputRef}
                              value={editingChatName}
                              onChange={(e) => setEditingChatName(e.target.value)}
                              onBlur={() => handleSaveChatName(chatId)}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                  e.preventDefault();
                                  handleSaveChatName(chatId);
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
                                onClick={() => handleSelectChat(chatId)}
                                className="flex-1 text-left truncate"
                              >
                                <span className="truncate">{label}</span>
                              </button>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <button
                                    type="button"
                                    onClick={(e) => e.stopPropagation()}
                                    className={`flex-shrink-0 opacity-0 group-hover:opacity-100 transition-colors p-1 ${
                                      isActive ? "text-blue-600 hover:text-blue-700" : "text-gray-500 group-hover:text-gray-700"
                                    }`}
                                    aria-label="채팅 설정"
                                  >
                                    <Pencil size={16} />
                                  </button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end" className="w-32">
                                  <DropdownMenuItem
                                    className="text-black hover:bg-gray-100 focus:bg-gray-100 data-[highlighted]:text-black"
                                    onClick={() => handleStartEditChat(chatId, label)}
                                  >
                                    이름 변경
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    className="text-red-600 focus:text-red-600 hover:bg-gray-100 focus:bg-gray-100"
                                    onClick={() => handleDeleteChat(chatId, label)}
                                  >
                                    삭제
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
              </ScrollArea>
            </>
          )}
        </aside>

        
      </div>

      <div className="relative flex flex-1 flex-col">
        <input ref={fileInputRef} type="file" onChange={handleFileChange} className="hidden" />

        <header className="flex items-center justify-between gap-6 px-6 pb-6 pt-8">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setSidebarCollapsed((prev) => !prev)}
              className="flex h-8 w-8 items-center justify-center rounded-full border border-gray-300 bg-white text-gray-600 shadow-sm transition hover:bg-gray-100"
              aria-label={sidebarCollapsed ? "사이드바 열기" : "사이드바 접기"}
            >
              {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
            </button>

            <div className="relative">
              <button
                type="button"
                onClick={() => setShowMaterialSelector(!showMaterialSelector)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl border border-gray-300 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
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
          </div>
          <div className="flex gap-3 mt-2">
            <button
              type="button"
              onClick={() => {
                setActiveTab("qa");
                navigate("/dashboard");
              }}
              className={`px-5 py-2 rounded-xl text-sm font-medium transition ${
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
              className={`px-5 py-2 rounded-xl text-sm font-medium transition ${
                activeTab === "quiz"
                  ? "bg-black text-white hover:opacity-90"
                  : "border border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
            >
              퀴즈 풀기
            </button>
          </div>
        </header>

        <main className="relative flex flex-1 flex-col px-4 md:px-6 pb-0">
          {hasMessages ? (
            <ScrollArea className="flex-1 px-1">
              <div className="max-w-4xl mx-auto w-full space-y-4 py-4 pb-32">
                {messages.map((message, index) => {
                  const isUser = message.role === "user";
                  const feedback = messageFeedback[message.id];
                  const isLast = index === messages.length - 1;
                  return (
                    <div
                      key={message.id}
                      ref={isLast ? lastMessageRef : undefined}
                      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
                    >
                      <div className="flex max-w-[80%] flex-col">
                        <div
                          className={`rounded-xl px-6 py-4 text-sm leading-relaxed ${
                            isUser ? "bg-black text-white" : "bg-white/80 text-gray-800"
                          }`}
                        >
                          {message.content}
                        </div>
                        {message.role === "assistant" && (
                          <div className="mt-1 space-y-2">
                            <div className="flex items-center justify-between pt-2 text-xs text-gray-500">
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
                              className={`flex items-center gap-1 transition hover:text-blue-600 ${
                                feedback === "like" ? "text-blue-600" : "text-gray-500"
                              }`}
                            >
                              <ThumbsUp size={14} />
                              <span>좋아요</span>
                            </button>

                            <button
                              type="button"
                              onClick={() => handleDislike(message.id)}
                              className={`flex items-center gap-1 transition hover:text-black ${
                                feedback === "dislike" ? "text-black" : "text-gray-500"
                              }`}
                            >
                              <ThumbsDown size={14} />
                              <span>싫어요</span>
                            </button>
                              </div>
                              <div>
                                <button
                                  type="button"
                                  onClick={() => handleOpenDifficultyDialog(message.id)}
                                  disabled={generatingFromQA === message.id}
                                  className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  <Sparkles size={14} />
                                  {generatingFromQA === message.id ? "문제 생성 중..." : "문제 생성"}
                                </button>
                              </div>
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
              <div className="w-full max-w-xl text-center space-y-4 -translate-y-6">
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
                {sessionsLoading && <p className="text-xs text-gray-500">채팅 기록을 불러오는 중...</p>}
                <p className="text-sm text-gray-500 mt-2">
                  AI와 함께하는 스마트한 학습. 질문하고, 배우고, 퀴즈로 테스트하세요.
                </p>
              </div>
            </div>
          )}

          {hasMessages && (
            <div className="sticky bottom-0 left-0 right-0 bg-white/90 backdrop-blur px-4 py-4">
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
              {uploadMessage && (
                <p className="mt-2 text-xs text-gray-500 text-center">
                  {uploadMessage}
                </p>
              )}
              {qaError && <p className="text-xs text-red-500 text-center">{qaError}</p>}
            </div>
          )}
        </main>
      </div>

      {/* 난이도 선택 Dialog */}
      <Dialog open={showDifficultyDialog} onOpenChange={setShowDifficultyDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>문제 난이도 선택</DialogTitle>
            <DialogDescription>
              생성할 문제의 난이도를 선택해주세요.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-4">
            <button
              type="button"
              onClick={() => setSelectedDifficultyForQA("BEGINNER")}
              className={`w-full px-4 py-3 rounded-lg border-2 transition ${
                selectedDifficultyForQA === "BEGINNER"
                  ? "border-blue-500 bg-blue-50 text-blue-700"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <div className="text-left">
                <div className="font-semibold">초급</div>
                <div className="text-sm text-gray-600">기본 개념 이해 문제</div>
              </div>
            </button>
            <button
              type="button"
              onClick={() => setSelectedDifficultyForQA("INTERMEDIATE")}
              className={`w-full px-4 py-3 rounded-lg border-2 transition ${
                selectedDifficultyForQA === "INTERMEDIATE"
                  ? "border-blue-500 bg-blue-50 text-blue-700"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <div className="text-left">
                <div className="font-semibold">중급</div>
                <div className="text-sm text-gray-600">기본 응용 문제</div>
              </div>
            </button>
            <button
              type="button"
              onClick={() => setSelectedDifficultyForQA("ADVANCED")}
              className={`w-full px-4 py-3 rounded-lg border-2 transition ${
                selectedDifficultyForQA === "ADVANCED"
                  ? "border-blue-500 bg-blue-50 text-blue-700"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <div className="text-left">
                <div className="font-semibold">고급</div>
                <div className="text-sm text-gray-600">실무 응용 문제</div>
              </div>
            </button>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowDifficultyDialog(false)}
            >
              취소
            </Button>
            <Button
              type="button"
              onClick={handleGenerateProblemsFromQA}
              disabled={generatingFromQA !== null}
            >
              문제 생성하기
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Dashboard;
