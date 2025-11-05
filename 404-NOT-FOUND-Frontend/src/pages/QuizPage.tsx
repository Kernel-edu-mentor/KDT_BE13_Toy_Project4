import { ChangeEvent, useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight, MessageSquare, Plus, X } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getJson } from "@/lib/api";

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

const initialChats = [
  { id: "react-study", label: "React 학습하기" },
  { id: "ts-questions", label: "TypeScript 질문" },
  { id: "algorithm-practice", label: "알고리즘 문제 풀이" },
];

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
      <h2 className="text-lg font-semibold">{problem.question}</h2>
      <textarea
        className="w-full border rounded-md p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        rows={4}
        placeholder="답변을 입력하세요"
        value={userAnswer}
        onChange={(e) => setUserAnswer(e.target.value)}
      />
      <button
        type="button"
        onClick={handleSubmit}
        disabled={submitting || !userAnswer.trim()}
        className="rounded-md bg-blue-600 text-white px-4 py-2 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {submitting ? "제출 중..." : "제출"}
      </button>
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
  const [chats, setChats] = useState(initialChats);
  const [selectedChatId, setSelectedChatId] = useState(initialChats[0]?.id ?? null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState<'qa' | 'quiz'>(location.pathname.includes("/quiz") ? "quiz" : "qa");
  const [topics, setTopics] = useState<string[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const pdfInputRef = useRef<HTMLInputElement | null>(null);

  const handleStartNewChat = () => {
    const newChat = { id: `chat-${Date.now()}`, label: `새 채팅 ${chats.length + 1}` };
    setChats((prev) => [newChat, ...prev]);
    setSelectedChatId(newChat.id);
    navigate("/dashboard");
  };

  const handleSelectChat = (chatId: string) => {
    setSelectedChatId(chatId);
    navigate("/dashboard");
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

  const handlePdfUpload = useCallback(
    async (event: ChangeEvent<HTMLInputElement>) => {
      const files = event.target.files;
      if (!files || files.length === 0) return;

      const formData = new FormData();
      Array.from(files).forEach((file) => formData.append("files", file));
      formData.append("difficulty", difficulty);

      try {
        setLoading(true);
        setError(null);
        const response = await fetch("/api/problems/upload", {
          method: "POST",
          body: formData,
        });
        if (!response.ok) {
          throw new Error("Failed to upload problems");
        }
        const data = await response.json();
        setProblems(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error(err);
        setError("PDF 업로드 중 오류가 발생했습니다.");
      } finally {
        setLoading(false);
        event.target.value = "";
      }
    },
    [difficulty],
  );

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
    <div className="flex min-h-[100dvh] bg-white overflow-hidden">
      <div className="relative hidden min-h-[100dvh] md:flex">
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
                className="mb-4 flex items-center gap-2 rounded-full border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-100"
              >
                <Plus size={16} />
                새 채팅
              </button>

              <ScrollArea className="flex-1 overflow-y-auto">
                <div className="space-y-1">
                  {chats.map((chat) => {
                    const isActive = chat.id === selectedChatId;
                    return (
                      <button
                        key={chat.id}
                        onClick={() => handleSelectChat(chat.id)}
                        className={`group flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors ${
                          isActive
                            ? "bg-black text-white"
                            : "bg-transparent text-gray-700 hover:bg-gray-100"
                        }`}
                      >
                        <MessageSquare
                          size={16}
                          className={`transition-colors ${
                            isActive ? "text-white" : "text-gray-500 group-hover:text-gray-700"
                          }`}
                        />
                        <span className="truncate">{chat.label}</span>
                      </button>
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

      <div className="relative flex min-h-[100dvh] flex-1 flex-col overflow-hidden">
        <header className="flex justify-end items-center gap-3 px-6 py-6">
          <button
            type="button"
            onClick={() => {
              setActiveTab("qa");
              if (location.pathname !== "/dashboard") {
                navigate("/dashboard");
              }
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
              if (location.pathname !== "/quiz") {
                navigate("/quiz");
              }
            }}
            className={`px-5 py-2 rounded-full text-sm font-medium transition ${
              activeTab === "quiz"
                ? "bg-black text-white hover:opacity-90"
                : "border border-gray-300 text-gray-700 hover:bg-gray-50"
            }`}
          >
            퀴즈 풀기
          </button>
        </header>

        <main className="flex-1 flex flex-col overflow-hidden px-4 pb-4 md:px-6">
          <div className="flex min-h-[100dvh] w-full mx-auto max-w-5xl flex-col overflow-hidden">
            <div className="flex flex-col min-h-[100dvh] rounded-3xl overflow-hidden bg-white">
              <div className="flex flex-col gap-3 px-6 pt-4 border-b border-gray-100 pb-4">
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => pdfInputRef.current?.click()}
                    className="flex h-10 w-10 items-center justify-center rounded-full border border-border text-foreground transition-colors hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    title="PDF 추가"
                  >
                    <Plus size={18} />
                  </button>
                  <input
                    ref={pdfInputRef}
                    type="file"
                    accept="application/pdf"
                    multiple
                    onChange={handlePdfUpload}
                    className="hidden"
                  />
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
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-gray-700">주제별 분류:</span>
                  <button
                    type="button"
                    onClick={() => setSelectedTopic(null)}
                    className={`px-3 py-1.5 text-xs font-medium rounded-full border transition ${
                      selectedTopic === null
                        ? "bg-black text-white border-black shadow-sm"
                        : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400"
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
                        className={`px-3 py-1.5 text-xs font-medium rounded-full border transition flex items-center gap-1.5 ${
                          selectedTopic === topic
                            ? "bg-black text-white border-black shadow-sm"
                            : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400"
                        }`}
                      >
                        {topic}
                        {selectedTopic === topic && (
                          <X
                            size={12}
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedTopic(null);
                            }}
                            className="hover:bg-gray-700 rounded-full p-0.5"
                          />
                        )}
                      </button>
                    ))
                  ) : (
                    <span className="text-xs text-gray-400 px-2">
                      아직 생성된 주제가 없습니다. 질문하기에서 문제를 생성해보세요.
                    </span>
                  )}
                </div>
              </div>

              <section className="flex-1 px-6 py-4 space-y-6">
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
