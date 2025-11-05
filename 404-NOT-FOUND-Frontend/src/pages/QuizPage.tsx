import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight, FileText, MessageSquare, Pencil, Plus, X } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getJson, postJson } from "@/lib/api";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";

interface Problem {
  id: number;
  question: string;
  difficulty?: string;
  materialId?: number;
  materialTitle?: string;
  topic?: string;
}

interface SubmitResult {
  is_correct: boolean;
  score?: number;
  feedback?: string;
  correct_answer?: string;
  similarity_score?: number;
  rubric_scores?: Record<string, any>;
  test_results?: Array<Record<string, any>>;
  response_time_ms?: number;
}

interface ProblemCardProps {
  problem: Problem;
  onSubmit: (id: number, answer: string, setResult: (result: SubmitResult) => void) => Promise<void>;
}

const difficulties = [
  { label: "초급", value: "BEGINNER" },
  { label: "중급", value: "INTERMEDIATE" },
  { label: "고급", value: "ADVANCED" },
];

interface QAChat {
  id: number;
  title: string;
  materialId: number | null;
  materialTitle: string | null;
  createdAt?: string;
}

interface MaterialDto {
  id: number;
  title: string;
  fileType: string;
  parseStatus: "PENDING" | "COMPLETED" | "FAILED";
  pageCount?: number | null;
  createdAt?: string;
}

const buildChatLabel = (chat: QAChat) => {
  const rawTitle = chat.title?.trim();
  if (rawTitle) return rawTitle;
  if (chat.materialTitle) return chat.materialTitle;
  return `채팅 ${chat.id}`;
};

const ProblemCard = ({ problem, onSubmit }: ProblemCardProps) => {
  const [userAnswer, setUserAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<SubmitResult | null>(null);

  const handleSubmit = async () => {
    if (!userAnswer.trim()) return;

    try {
      setSubmitting(true);
      await onSubmit(problem.id, userAnswer, setResult);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="border rounded-2xl p-5 shadow-sm space-y-3 bg-white">
      <h2 className="text-base font-semibold">{problem.question}</h2>
      <textarea
        className="w-full border rounded-md p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        rows={4}
        placeholder="답변을 입력하세요"
        value={userAnswer}
        onChange={(e) => setUserAnswer(e.target.value)}
      />
      <div className="flex justify-end">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={submitting || !userAnswer.trim()}
          className="rounded-xl bg-black text-white px-5 py-2 text-sm font-medium transition hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? "제출 중..." : "제출"}
        </button>
      </div>
      {result && (
        <div className="text-sm space-y-2 p-4 rounded-lg bg-gray-50">
          <div className="flex items-center gap-2">
            <p className={`font-semibold ${result.is_correct ? "text-green-600" : "text-red-600"}`}>
              {result.is_correct ? "✓ 정답입니다!" : "✗ 오답입니다."}
            </p>
            {result.score !== undefined && (
              <span className="text-gray-600">({result.score}/100점)</span>
            )}
          </div>
          
          {result.feedback && (
            <p className="text-gray-700 whitespace-pre-wrap">{result.feedback}</p>
          )}
          
          {!result.is_correct && result.correct_answer && (
            <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200">
              <p className="text-xs text-gray-600 mb-1">정답:</p>
              <p className="text-gray-800">{result.correct_answer}</p>
            </div>
          )}
          
          {result.similarity_score !== undefined && result.similarity_score !== null && (
            <p className="text-xs text-gray-500">
              의미 유사도: {(result.similarity_score * 100).toFixed(1)}%
            </p>
          )}
          
          {result.rubric_scores && (
            <div className="mt-2 pt-2 border-t border-gray-200">
              <p className="text-xs font-semibold text-gray-600 mb-1">루브릭 점수:</p>
              <div className="grid grid-cols-2 gap-1 text-xs">
                {Object.entries(result.rubric_scores).map(([key, value]: [string, any]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-600">{key}:</span>
                    <span className="text-gray-800">{value?.score || value}/2</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const QuizPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [problems, setProblems] = useState<Problem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState(difficulties[0].value);
  const [chats, setChats] = useState<QAChat[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState<'qa' | 'quiz'>(location.pathname.includes("/quiz") ? "quiz" : "qa");
  const [topics, setTopics] = useState<string[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const chatNameInputRef = useRef<HTMLInputElement | null>(null);
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editingChatName, setEditingChatName] = useState<string>("");
  const [chatsLoading, setChatsLoading] = useState(false);
  const [materials, setMaterials] = useState<MaterialDto[]>([]);
  const [materialsLoading, setMaterialsLoading] = useState(false);
  const [showMaterialSelector, setShowMaterialSelector] = useState(false);
  const [materialId, setMaterialId] = useState<string | null>(() => sessionStorage.getItem("ai-mentor-material-id"));
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [qaError, setQaError] = useState<string | null>(null);

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

  useEffect(() => {
    fetchMaterials();
  }, []);

  useEffect(() => {
    let isMounted = true;

    const loadChats = async () => {
      const chatList = await fetchChats();
      if (!isMounted) return;

      if (chatList.length === 0) {
        setSelectedChatId(null);
        return;
      }

      setSelectedChatId((prev) => {
        if (prev && chatList.some((chat) => String(chat.id) === prev)) {
          return prev;
        }
        return String(chatList[0].id);
      });
    };

    loadChats();

    return () => {
      isMounted = false;
    };
  }, [fetchChats]);

  const handleStartNewChat = () => {
    const createChat = async () => {
      try {
        if (!materialId) {
          setUploadMessage("먼저 학습 자료를 선택해주세요.");
          return;
        }

        const chat = await postJson<QAChat>("/qa/chats", {
          title: `새 채팅 ${chats.length + 1}`,
          materialId: Number(materialId),
        });
        setSelectedChatId(String(chat.id));
        await fetchChats();
        navigate("/dashboard");
      } catch (error) {
        console.error("새 채팅 생성 실패:", error);
        setQaError("새 채팅을 생성하지 못했습니다.");
      }
    };

    void createChat();
  };

  const handleSelectChat = (chatId: string) => {
    setSelectedChatId(chatId);
    navigate("/dashboard");
  };

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
  };

  const handleStartEditChat = (chatId: string, currentLabel: string) => {
    setEditingChatId(chatId);
    setEditingChatName(currentLabel);
    setTimeout(() => {
      chatNameInputRef.current?.focus();
      chatNameInputRef.current?.select();
    }, 0);
  };

  const handleCancelEditChat = () => {
    setEditingChatId(null);
    setEditingChatName("");
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

      setSelectedChatId((prevSelected) => {
        if (prevSelected !== chatId) {
          return prevSelected;
        }

        const remaining = chats.filter((chat) => String(chat.id) !== chatId);
        if (remaining.length === 0) {
          return null;
        }
        return String(remaining[0].id);
      });

      await fetchChats();
    } catch (error) {
      console.error("채팅 삭제 실패:", error);
      setQaError(error instanceof Error ? error.message : "채팅을 삭제하지 못했습니다.");
    }
  };

  useEffect(() => {
    setActiveTab(location.pathname.includes("/quiz") ? "quiz" : "qa");
  }, [location.pathname]);

  const fetchTopics = async () => {
    try {
      const topicsList = await getJson<string[]>("/problems/topics");
      setTopics(topicsList);
    } catch (error) {
      console.error("주제 목록 조회 실패:", error);
    }
  };

  useEffect(() => {
    fetchTopics();
  }, []);

  const loadProblems = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      let url = `/api/problems/list?difficulty=${encodeURIComponent(difficulty)}`;
      if (selectedTopic) {
        url += `&topic=${encodeURIComponent(selectedTopic)}`;
      }
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error("Failed to fetch problems");
      }
      const data = await response.json();
      setProblems(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
      setError("문제를 불러오는 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }, [difficulty, selectedTopic]);

  const handleSubmitAnswer = useCallback(
    async (id: number, answer: string, setResult: (result: SubmitResult) => void) => {
      try {
        const response = await fetch(`/api/problems/answer/${id}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ answer }),
        });
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`답안 제출 실패: ${errorText}`);
        }
        const data = await response.json();
        setResult(data);
      } catch (err) {
        console.error("답안 제출 에러:", err);
        setResult({ 
          is_correct: false, 
          feedback: "답안을 제출하는 중 문제가 발생했습니다. 다시 시도해주세요." 
        });
      }
    },
    [],
  );

  useEffect(() => {
    loadProblems();
  }, [loadProblems]);

  return (
    <div className="flex flex-1 min-h-[calc(100vh-4rem)] bg-white overflow-hidden">
      <div className="relative hidden min-h-full md:flex">
        <aside
          className={`flex min-h-0 flex-col border-r border-gray-200 bg-[#f7f7f8] py-8 transition-all duration-300 ${
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
                      return (
                        <div
                          key={chat.id}
                          className={`group flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors bg-transparent hover:bg-gray-100 ${
                            isActive && !isEditing ? "text-blue-600" : "text-gray-700"
                          }`}
                        >
                          <MessageSquare
                            size={16}
                            className={`transition-colors flex-shrink-0 ${
                              isActive && !isEditing ? "text-blue-600" : "text-gray-500 group-hover:text-gray-700"
                            }`}
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

      <div className="relative flex flex-1 flex-col overflow-hidden">
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

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => {
                setActiveTab("qa");
                if (location.pathname !== "/dashboard") {
                  navigate("/dashboard");
                }
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
                if (location.pathname !== "/quiz") {
                  navigate("/quiz");
                }
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

        <main className="flex-1 flex flex-col overflow-hidden px-4 pb-4 md:px-6">
          {(uploadMessage || qaError) && (
            <div className="px-2 md:px-0 mb-3">
              {uploadMessage && <p className="text-sm text-blue-600">{uploadMessage}</p>}
              {qaError && <p className="text-xs text-red-500">{qaError}</p>}
            </div>
          )}
          <div className="flex min-h-full w-full mx-auto max-w-5xl flex-col overflow-hidden">
            <div className="flex flex-col min-h-full rounded-3xl overflow-hidden bg-white">
              <div className="flex flex-col gap-3 px-6 pt-4 pb-4">
                <div className="flex items-center gap-3">
                  <Tabs
                    value={difficulty}
                    onValueChange={(value) => setDifficulty(value)}
                    className="flex h-10 items-center"
                  >
                    <TabsList className="flex h-10 items-center gap-1 rounded-full bg-muted/60 p-1">
                      {difficulties.map((d) => (
                        <TabsTrigger
                          key={d.value}
                          value={d.value}
                          className="rounded-full px-4 py-2 text-sm data-[state=active]:bg-white data-[state=active]:text-foreground data-[state=active]:shadow-sm"
                        >
                          {d.label}
                        </TabsTrigger>
                      ))}
                    </TabsList>
                  </Tabs>
                </div>
                <div className="flex items-center gap-3 flex-wrap">
                  <button
                    type="button"
                    onClick={() => setSelectedTopic(null)}
                    className={`px-3 py-1.5 text-sm font-medium rounded-full transition ${
                      selectedTopic === null
                        ? "text-blue-600"
                        : "text-gray-800 hover:text-blue-600"
                    }`}
                  >
                    전체
                  </button>
                  {topics.length > 0 ? (
                    topics.map((topic) => (
                      <button
                        key={topic}
                        type="button"
                        onClick={() => setSelectedTopic(topic)}
                        className={`px-3 py-1.5 text-sm font-medium rounded-full transition ${
                          selectedTopic === topic
                            ? "text-blue-600"
                            : "text-gray-800 hover:text-blue-600"
                        }`}
                      >
                        {topic}
                      </button>
                    ))
                  ) : (
                    <span className="text-xs text-gray-400 px-2">
                      아직 생성된 주제가 없습니다. 질문하기에서 문제를 생성해보세요.
                    </span>
                  )}
                </div>
              </div>

              <section className="flex-1 px-6 pt-4 pb-24 space-y-6">
                {error && (
                  <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                    {error}
                  </div>
                )}

                {loading && problems.length === 0 ? (
                  <div className="flex h-full items-center justify-center text-gray-400">
                    문제를 불러오는 중입니다...
                  </div>
                ) : problems.length === 0 ? (
                  <div className="flex h-full items-center justify-center text-gray-500">
                    아직 생성된 문제가 없습니다.
                  </div>
                ) : (
                  problems.map((problem) => (
                    <ProblemCard key={problem.id} problem={problem} onSubmit={handleSubmitAnswer} />
                  ))
                )}
              </section>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default QuizPage;
