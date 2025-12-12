import { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

// --- HELPER ---
const formatText = (text) => {
  if (!text) return "";
  let cleanText = text.replace(/Quadrilateral\(([A-Z]+)\)/g, "$1");
  cleanText = cleanText.replace(/Angle\(([A-Z]+)\)/g, "góc $1");
  cleanText = cleanText.replace(/=>/g, "➜");
  return cleanText;
};

// --- ICONS ---
const LoadingIcon = () => (
  <svg
    className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
  >
    <circle
      className="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="4"
    ></circle>
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    ></path>
  </svg>
);
const RocketIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className="h-4 w-4"
    viewBox="0 0 20 20"
    fill="currentColor"
  >
    <path
      fillRule="evenodd"
      d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
      clipRule="evenodd"
    />
  </svg>
);
const SolutionIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className="h-5 w-5 text-emerald-600 dark:text-emerald-400"
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
    />
  </svg>
);
const WarningIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className="h-10 w-10 text-orange-400 mb-2"
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={1.5}
      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
    />
  </svg>
);
const ErrorIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className="h-5 w-5 text-red-600 dark:text-red-400"
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
    />
  </svg>
);
const SunIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className="h-5 w-5 text-yellow-500"
    viewBox="0 0 20 20"
    fill="currentColor"
  >
    <path
      fillRule="evenodd"
      d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"
      clipRule="evenodd"
    />
  </svg>
);
const MoonIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className="h-5 w-5 text-slate-400"
    viewBox="0 0 20 20"
    fill="currentColor"
  >
    <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
  </svg>
);
const EmptyStateIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className="h-12 w-12 mb-3 text-slate-300 dark:text-slate-600"
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={1}
      d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
    />
  </svg>
);

// --- MODAL COMPONENT (Thêm mới) ---
const InfoModal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-100 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 transition-all">
      <div
        className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl max-w-5xl w-full max-h-[85vh] overflow-y-auto border border-slate-200 dark:border-slate-700 animate-in fade-in zoom-in duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Modal */}
        <div className="flex justify-between items-center p-5 border-b border-slate-100 dark:border-slate-800 sticky top-0 bg-white dark:bg-slate-900 z-10">
          <h3 className="text-lg font-bold bg-linear-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            {title}
          </h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-red-500"
          >
            ✕
          </button>
        </div>
        {/* Content Modal */}
        <div className="p-6 text-slate-600 dark:text-slate-300 leading-relaxed text-sm">
          {children}
        </div>
      </div>
      {/* Click outside to close */}
      <div className="absolute inset-0 -z-10" onClick={onClose}></div>
    </div>
  );
};

// --- MAIN COMPONENT ---
function App() {
  const DEFAULT_TEXT = `Cho tam giác ABC cân tại A. Đường cao AH. Kẻ HE vuông góc với AB tại E, HF vuông góc với AC tại F. Chứng minh tứ giác AEHF nội tiếp.`;

  const [inputText, setInputText] = useState(DEFAULT_TEXT);
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [darkMode, setDarkMode] = useState(false);
  const [showGuide, setShowGuide] = useState(false);
  const [showTheory, setShowTheory] = useState(false);
  const [guideStep, setGuideStep] = useState(0);

  useEffect(() => {
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      setDarkMode(true);
    }
  }, []);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  const handleSolve = async () => {
    if (!inputText.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setActiveTab(0);
    try {
      const response = await axios.post("http://127.0.0.1:8000/solve", {
        text: inputText,
      });
      setResult(response.data);
    } catch {
      setError("Không kết nối được Server (Port 8000).");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className={`min-h-screen transition-colors duration-300 font-sans flex flex-col ${
        darkMode ? "bg-slate-950 text-slate-100" : "bg-slate-50 text-slate-800"
      }`}
    >
      {/* NAVBAR: Compact */}
      <nav
        className={`border-b h-14 flex items-center px-6 sticky top-0 z-50 backdrop-blur-md ${
          darkMode
            ? "bg-slate-900/80 border-slate-800"
            : "bg-white/80 border-slate-200"
        }`}
      >
        <div className="flex items-center gap-2 mr-auto">
          <div className="bg-blue-600 p-1.5 rounded-lg shadow-sm">
            <span className="text-sm text-white">📐</span>
          </div>
          <h1 className="text-lg font-bold tracking-tight bg-linear-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent dark:from-blue-400 dark:to-indigo-400">
            GeoSolver AI
          </h1>
        </div>
        <div className="hidden md:flex items-center gap-1 mx-4">
          <button
            onClick={() => setShowGuide(true)}
            className="px-3 py-1.5 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
          >
            📖 Hướng dẫn
          </button>
          <button
            onClick={() => setShowTheory(true)}
            className="px-3 py-1.5 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
          >
            🧠 Lý thuyết
          </button>
        </div>
        <button
          onClick={() => setDarkMode(!darkMode)}
          className={`p-1.5 rounded-md border ${
            darkMode
              ? "bg-slate-800 border-slate-700 hover:bg-slate-700"
              : "bg-white border-slate-200 hover:bg-slate-100"
          }`}
        >
          {darkMode ? <SunIcon /> : <MoonIcon />}
        </button>
      </nav>

      {/* MAIN CONTENT: Full Height Dashboard */}
      <main className="flex-1 p-4 md:p-6 overflow-hidden flex flex-col md:flex-row gap-6 max-w-[1600px] mx-auto w-full">
        {/* === LEFT COLUMN: INPUT === */}
        <div className="w-full md:w-1/3 lg:w-1/4 flex flex-col gap-4">
          <div
            className={`flex-1 rounded-2xl shadow-sm border flex flex-col p-4 ${
              darkMode
                ? "bg-slate-900 border-slate-800"
                : "bg-white border-slate-200"
            }`}
          >
            <div className="flex justify-between items-center mb-3">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Đề bài
              </label>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setInputText(DEFAULT_TEXT)}
                  className="text-xs cursor-pointer text-blue-500 hover:underline"
                >
                  Mẫu
                </button>
                <div className="h-3 w-px bg-slate-300 dark:bg-slate-700"></div>
                <button
                  onClick={() => setInputText("")}
                  className="text-xs cursor-pointer text-red-500 hover:underline"
                >
                  Xóa
                </button>
              </div>
            </div>

            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className={`flex-1 w-full p-3 text-sm rounded-xl border resize-none focus:ring-2 focus:border-transparent outline-none leading-relaxed custom-scrollbar ${
                darkMode
                  ? "bg-slate-950 border-slate-800 text-slate-200 focus:ring-blue-500"
                  : "bg-slate-50 border-slate-200 text-slate-700 focus:bg-white focus:ring-blue-500"
              }`}
              placeholder="Nhập đề bài tại đây..."
              spellCheck={false}
              autoComplete="off"
              autoCorrect="off"
            />

            <button
              onClick={handleSolve}
              disabled={loading || !inputText.trim()}
              className={`mt-4 py-3 px-4 rounded-xl cursor-pointer font-bold text-white shadow-md transition-all active:scale-[0.98] flex justify-center items-center gap-2 text-sm
                ${
                  loading || !inputText.trim()
                    ? "bg-slate-400 dark:bg-slate-700 cursor-not-allowed opacity-70"
                    : "bg-blue-600 hover:bg-blue-700 shadow-blue-500/30"
                }`}
            >
              {loading ? <LoadingIcon /> : <RocketIcon />}
              <span>{loading ? "Đang phân tích..." : "Giải ngay"}</span>
            </button>

            {error && (
              <div className="mt-3 text-xs text-red-500 bg-red-50 dark:bg-red-900/20 p-2 rounded border border-red-100 dark:border-red-900/50">
                {error}
              </div>
            )}
          </div>

          <div
            className={`rounded-xl border p-4 text-xs ${
              darkMode
                ? "bg-indigo-900/10 border-indigo-900/30 text-indigo-300"
                : "bg-indigo-50 border-indigo-100 text-indigo-800"
            }`}
          >
            <p className="font-bold mb-1">💡 Gợi ý nhập liệu:</p>
            <ul className="list-disc list-inside opacity-80 space-y-1">
              <li>Cho tam giác ABC đều.</li>
              <li>Biết góc A bằng 60.</li>
              <li>Chứng minh tứ giác ABCD nội tiếp.</li>
            </ul>
          </div>
        </div>

        {/* === RIGHT COLUMN: OUTPUT (Split View) === */}
        <div
          className={`flex-1 rounded-2xl shadow-sm border overflow-hidden flex flex-col ${
            darkMode
              ? "bg-slate-900 border-slate-800"
              : "bg-white border-slate-200"
          }`}
        >
          {/* Header Kết quả */}
          <div
            className={`h-12 px-5 border-b flex items-center justify-between ${
              darkMode
                ? "border-slate-800 bg-slate-900"
                : "border-slate-100 bg-white"
            }`}
          >
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Kết quả phân tích
            </span>
            {result && result.status && (
              <span
                className={`px-2 py-0.5 text-[10px] font-bold rounded-full uppercase tracking-wide border ${
                  result.status === "success"
                    ? "bg-green-100 text-green-700 border-green-200"
                    : result.status === "contradiction"
                    ? "bg-red-100 text-red-700 border-red-200"
                    : "bg-orange-100 text-orange-700 border-orange-200"
                }`}
              >
                {result.status === "success"
                  ? "Thành công"
                  : result.status === "contradiction"
                  ? "Mâu thuẫn"
                  : "Cảnh báo"}
              </span>
            )}
          </div>

          {result ? (
            <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
              {/* --- PHẦN 1: HÌNH ẢNH (Bên trái hoặc Trên) --- */}
              <div
                className={`lg:w-5/12 flex flex-col border-b lg:border-b-0 lg:border-r ${
                  darkMode
                    ? "border-slate-800 bg-slate-950/50"
                    : "border-slate-100 bg-slate-50"
                }`}
              >
                <div className="flex-1 flex items-center justify-center px-6 pb-3 relative group">
                  {result.image ? (
                    <>
                      <div className="bg-white p-2 rounded-lg shadow-sm border border-slate-200 max-w-full max-h-full flex items-center justify-center">
                        <img
                          src={result.image}
                          alt="Plot"
                          className="max-w-full max-h-[400px] lg:max-h-[600px] object-contain"
                        />
                      </div>
                      <a
                        href={result.image}
                        download="hinh-ve.png"
                        className="absolute bottom-4 right-4 bg-white/90 text-slate-700 p-2 rounded-lg shadow-sm opacity-0 group-hover:opacity-100 transition-all hover:text-blue-600 border"
                        title="Tải ảnh"
                      >
                        ⬇️
                      </a>
                    </>
                  ) : (
                    <div className="text-center text-slate-400 text-sm">
                      <EmptyStateIcon />
                      <p>Không có hình minh họa</p>
                    </div>
                  )}
                </div>
                <div className="p-2 border-t text-[15px] font-bold font-mono text-center text-slate-400 dark:border-slate-800">
                  {/* {result.debug_facts} */}
                  Hình ảnh minh họa
                </div>
              </div>

              {/* --- PHẦN 2: LỜI GIẢI (Bên phải hoặc Dưới) --- */}
              <div className="lg:w-7/12 flex flex-col bg-transparent h-full overflow-hidden">
                <div className="flex-1 overflow-y-auto p-5 custom-scrollbar">
                  <h4
                    className={`font-bold text-lg mb-4 flex items-center gap-2 ${
                      darkMode ? "text-slate-100" : "text-slate-800"
                    }`}
                  >
                    <SolutionIcon />
                    {result.status === "contradiction"
                      ? "Phân tích lỗi sai"
                      : "Lời giải chi tiết"}
                  </h4>

                  {/* Render Lời giải */}
                  <div className="space-y-4">
                    {/* CASE 1: MÂU THUẪN (Contradiction) */}
                    {result.status === "contradiction" && (
                      <div
                        className={`p-4 rounded-lg border-l-4 text-sm ${
                          darkMode
                            ? "bg-red-900/20 border-red-500 text-red-200"
                            : "bg-red-50 border-red-500 text-slate-800"
                        }`}
                      >
                        <div className="font-bold mb-2 flex items-center gap-2 text-red-600 dark:text-red-400">
                          <ErrorIcon /> Phát hiện mâu thuẫn:
                        </div>
                        {result.solutions.map((sol, i) => (
                          <p key={i} className="mb-1">
                            {formatText(sol)}
                          </p>
                        ))}
                      </div>
                    )}

                    {/* CASE 2: CẢNH BÁO (Warning) - Có Text trả về */}
                    {result.status === "warning" && (
                      <div
                        className={`p-4 rounded-lg border-l-4 text-sm leading-relaxed whitespace-pre-line shadow-sm ${
                          darkMode
                            ? "bg-yellow-900/10 border-yellow-500 text-yellow-100"
                            : "bg-yellow-50 border-yellow-500 text-slate-800"
                        }`}
                      >
                        <div className="font-bold mb-2 flex items-center gap-2 text-yellow-600 dark:text-yellow-500">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-5 w-5"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                          >
                            <path
                              fillRule="evenodd"
                              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                              clipRule="evenodd"
                            />
                          </svg>
                          Cảnh báo hệ thống:
                        </div>
                        {result.solutions.map((sol, index) => (
                          <div key={index} className="mb-2">
                            {formatText(sol)}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* CASE 3: THÀNH CÔNG (Success) - Đã sửa thành Tabs */}
                    {(result.status === "success" ||
                      (!result.status && result.solutions.length > 0)) && (
                      <div className="flex flex-col">
                        {/* TAB HEADER: Chỉ hiện nếu có nhiều hơn 1 lời giải */}
                        {result.solutions.length > 1 && (
                          <div className="flex border-b border-slate-200 dark:border-slate-700 mb-4 overflow-x-auto no-scrollbar">
                            {result.solutions.map((_, index) => (
                              <button
                                key={index}
                                onClick={() => setActiveTab(index)}
                                className={`px-4 py-2 text-sm font-bold transition-colors cursor-pointer whitespace-nowrap border-b-2 ${
                                  activeTab === index
                                    ? "border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400"
                                    : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                                }`}
                              >
                                Cách {index + 1}
                              </button>
                            ))}
                          </div>
                        )}

                        {/* CONTENT: Hiển thị lời giải đang chọn */}
                        <div
                          className={`p-4 rounded-lg border-l-4 text-sm leading-relaxed whitespace-pre-line shadow-sm transition-all duration-300 ${
                            darkMode
                              ? "bg-emerald-900/10 border-emerald-500 text-emerald-100"
                              : "bg-emerald-50 border-emerald-500 text-slate-800"
                          }`}
                        >
                          {formatText(result.solutions[activeTab])}
                        </div>

                        {/* Hiển thị thêm thông tin số lượng cách giải (nếu cần) */}
                        {result.solutions.length > 1 && (
                          <div className="text-xs text-right mt-2 text-slate-400 italic">
                            Đang xem cách {activeTab + 1} trên tổng số{" "}
                            {result.solutions.length} cách giải
                          </div>
                        )}
                      </div>
                    )}

                    {/* CASE 4: RỖNG (Fallback) */}
                    {result.status !== "contradiction" &&
                      result.status !== "warning" &&
                      result.status !== "success" &&
                      result.solutions.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-10 text-center">
                          <WarningIcon />
                          <h5 className="font-bold mt-2 text-slate-600 dark:text-slate-300">
                            Chưa tìm ra lời giải
                          </h5>
                          <p className="text-sm text-slate-400 mt-1 max-w-xs">
                            Hệ thống không tìm thấy đường đi logic nào phù hợp
                            với dữ kiện đã cho.
                          </p>
                        </div>
                      )}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            // EMPTY STATE CHO VÙNG KẾT QUẢ
            <div className="flex-1 flex flex-col items-center justify-center text-center p-10 opacity-60">
              <EmptyStateIcon />
              <p className="text-slate-400 text-sm">
                Kết quả phân tích và hình vẽ sẽ hiển thị ở đây
              </p>
            </div>
          )}
        </div>
      </main>
      {/* <InfoModal
        isOpen={showGuide}
        onClose={() => setShowGuide(false)}
        title="📖 Hướng dẫn sử dụng GeoSolver AI"
      >
        <div className="space-y-4">
          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border border-blue-100 dark:border-blue-800">
            <p className="font-bold text-blue-700 dark:text-blue-300 mb-1">
              Bước 1: Nhập đề bài
            </p>
            <p>
              Nhập đề toán hình học phẳng vào khung bên trái. Hãy viết rõ ràng
              bằng tiếng Việt, tách câu bằng dấu chấm để hệ thống dễ hiểu. Tránh
              dùng từ viết tắt hoặc ngôn ngữ mơ hồ.
            </p>
            <p className="text-xs mt-2 opacity-80">
              Ví dụ đầy đủ: "Cho tam giác ABC cân tại A với đường cao AH. Kẻ HE
              vuông góc với AB tại E, HF vuông góc với AC tại F. Chứng minh rằng
              tứ giác AEHF là tứ giác nội tiếp."
            </p>
          </div>
          <div className="bg-indigo-50 dark:bg-indigo-900/20 p-4 rounded-lg border border-indigo-100 dark:border-indigo-800">
            <p className="font-bold text-indigo-700 dark:text-indigo-300 mb-1">
              Bước 2: Phân tích đề bài
            </p>
            <p>
              Nhấn nút <strong>"Giải ngay"</strong>. Hệ thống sẽ sử dụng AI để:
            </p>
            <ul className="list-disc list-inside mt-1 ml-2 space-y-1 opacity-90">
              <li>Đọc hiểu và trích xuất các yếu tố hình học từ đề bài.</li>
              <li>Sử dụng engine suy luận logic để tìm lời giải.</li>
              <li>Tạo hình minh họa dựa trên tọa độ chính xác.</li>
              <li>
                Xử lý các trường hợp đặc biệt như mâu thuẫn hoặc cảnh báo.
              </li>
            </ul>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg border border-green-100 dark:border-green-800">
            <p className="font-bold text-green-700 dark:text-green-300 mb-1">
              Bước 3: Xem và tương tác với kết quả
            </p>
            <p>
              Kết quả sẽ hiển thị bên phải, bao gồm hình vẽ (có thể tải về) và
              lời giải chi tiết. Nếu có nhiều cách giải, sử dụng tab để chuyển
              đổi. Nếu phát hiện mâu thuẫn, hệ thống sẽ chỉ ra lý do.
            </p>
            <p className="text-xs mt-2 opacity-80">
              Lưu ý: Nếu kết quả không như mong đợi, thử chỉnh sửa đề bài cho rõ
              ràng hơn hoặc kiểm tra kết nối server.
            </p>
          </div>
          <p className="italic text-xs text-center pt-2">
            Lưu ý: Hệ thống hiện tại tối ưu cho bài toán liên quan đến tứ giác
            nội tiếp, nhưng có thể mở rộng trong tương lai.
          </p>
        </div>
      </InfoModal> */}

      <InfoModal
        isOpen={showGuide}
        onClose={() => setShowGuide(false)}
        title="Hướng dẫn sử dụng GeoSolver AI"
        className="max-w-5xl"
      >
        <div className="relative">
          {/* Tabs chọn bước */}
          <div className="flex flex-wrap justify-center gap-3 mb-8">
            {[1, 2, 3].map((step) => (
              <button
                key={step}
                onClick={() => setGuideStep(step - 1)}
                className={`px-6 py-3 rounded-xl font-bold text-sm transition-all ${
                  guideStep === step - 1
                    ? "bg-linear-to-r from-blue-600 to-indigo-600 text-white shadow-lg scale-105"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
                }`}
              >
                Bước {step}
              </button>
            ))}
          </div>

          {/* Carousel chính */}
          <div className="grid md:grid-cols-2 gap-8 items-center">
            {/* Ảnh minh họa */}
            <div className="relative order-2 md:order-1">
              <div className="bg-linear-to-br from-blue-50 to-indigo-100 dark:from-slate-800 dark:to-slate-900 rounded-3xl p-5 shadow-2xl">
                <img
                  src={`/step${guideStep + 1}.png`}
                  alt={`Bước ${guideStep + 1}`}
                  className="w-full rounded-2xl shadow-xl border-4 border-white dark:border-slate-700"
                />
              </div>

              {/* Nút chuyển thủ công */}
              <button
                onClick={() =>
                  setGuideStep((prev) => (prev === 0 ? 2 : prev - 1))
                }
                className="absolute left-2 top-1/2 -translate-y-1/2 bg-white/90 dark:bg-slate-900/90 backdrop-blur p-3 rounded-full shadow-lg hover:scale-110 transition"
              >
                Previous
              </button>
              <button
                onClick={() =>
                  setGuideStep((prev) => (prev === 2 ? 0 : prev + 1))
                }
                className="absolute right-2 top-1/2 -translate-y-1/2 bg-white/90 dark:bg-slate-900/90 backdrop-blur p-3 rounded-full shadow-lg hover:scale-110 transition"
              >
                Next
              </button>
            </div>

            {/* Nội dung mô tả */}
            <div className="order-1 md:order-2 space-y-5">
              {guideStep === 0 && (
                <>
                  <h3 className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    Bước 1: Nhập đề bài
                  </h3>
                  <p className="text-lg leading-relaxed">
                    Viết đề toán bằng <strong>tiếng Việt tự nhiên</strong>, tách
                    câu bằng dấu chấm.
                    <br />
                    Hệ thống sẽ tự động hiểu: tam giác, đường cao, vuông góc,
                    nội tiếp,...
                  </p>
                  <div className="bg-blue-50 dark:bg-blue-900/30 p-4 rounded-xl text-sm">
                    <span className="font-semibold">Ví dụ:</span>
                    <br />
                    Cho tam giác ABC cân tại A. Đường cao AH. Kẻ HE ⊥ AB, HF ⊥
                    AC. Chứng minh AEHF nội tiếp.
                  </div>
                </>
              )}

              {guideStep === 1 && (
                <>
                  <h3 className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                    Bước 2: Nhấn "Giải ngay"
                  </h3>
                  <p className="text-lg leading-relaxed">AI sẽ:</p>
                  <ul className="space-y-2 text-lg">
                    <li className="flex items-center gap-3">Đọc hiểu đề bài</li>
                    <li className="flex items-center gap-3">
                      Tìm lời giải logic
                    </li>
                    <li className="flex items-center gap-3">
                      Vẽ hình chính xác theo tọa độ
                    </li>
                    <li className="flex items-center gap-3">
                      Phát hiện mâu thuẫn (nếu có)
                    </li>
                  </ul>
                </>
              )}

              {guideStep === 2 && (
                <>
                  <h3 className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                    Bước 3: Xem kết quả
                  </h3>
                  <p className="text-lg leading-relaxed">Bên phải sẽ hiện:</p>
                  <ul className="space-y-2 text-lg">
                    <li className="flex items-center gap-3">
                      Hình vẽ có thể tải về
                    </li>
                    <li className="flex items-center gap-3">
                      Lời giải chi tiết (có thể có nhiều cách)
                    </li>
                    <li className="flex items-center gap-3">
                      Cảnh báo nếu đề sai hoặc thiếu điều kiện
                    </li>
                  </ul>
                </>
              )}

              {/* Dots chỉ thị */}
              <div className="flex justify-center gap-2 pt-6">
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    onClick={() => setGuideStep(i)}
                    className={`w-3 h-3 rounded-full cursor-pointer transition-all ${
                      guideStep === i
                        ? "bg-blue-600 w-10"
                        : "bg-slate-300 dark:bg-slate-600"
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </InfoModal>

      {/* --- MODAL LÝ THUYẾT --- */}
      <InfoModal
        isOpen={showTheory}
        onClose={() => setShowTheory(false)}
        title="Các phương pháp chứng minh tứ giác nội tiếp"
        className="max-w-6xl" // Đảm bảo bạn đã update InfoModal nhận prop className như hướng dẫn trước
      >
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2">
          {/* ==================== CÁCH 1 ==================== */}
          <div className="group flex flex-col h-full border rounded-2xl p-5 hover:shadow-xl transition-shadow dark:border-slate-700 bg-white dark:bg-slate-800">
            {/* Phần nội dung chữ (Dùng flex-1 để chiếm chỗ trống, đẩy ảnh xuống) */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <span className="bg-linear-to-r from-blue-500 to-cyan-500 text-white font-bold px-3 py-1 rounded-lg text-xs shadow-sm">
                  CÁCH 1
                </span>
                <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">
                  Tổng hai góc đối bằng 180°
                </h3>
              </div>
              <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-300 mb-4">
                Đây là định lý cơ bản nhất: Một tứ giác nội tiếp khi và chỉ khi
                tổng hai góc đối diện bằng 180°. Đây cũng là cách được dùng
                nhiều nhất trong các bài thi.
              </p>
            </div>

            {/* Phần ảnh (Sẽ luôn nằm ở đáy và cố định chiều cao) */}
            <div className="w-full h-48 bg-slate-50 dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-700 overflow-hidden flex items-center justify-center">
              <img
                src="/cyclic-sum-180.jpg" // Đảm bảo đường dẫn đúng
                alt="Tổng hai góc đối = 180°"
                className="max-w-full max-h-full p-2 object-contain transition-transform duration-500 group-hover:scale-105"
              />
            </div>
          </div>

          {/* ==================== CÁCH 2 ==================== */}
          <div className="group flex flex-col h-full border rounded-2xl p-5 hover:shadow-xl transition-shadow dark:border-slate-700 bg-white dark:bg-slate-800">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <span className="bg-linear-to-r from-emerald-500 to-teal-500 text-white font-bold px-3 py-1 rounded-lg text-xs shadow-sm">
                  CÁCH 2
                </span>
                <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">
                  Hai góc kề nhìn cùng một cạnh
                </h3>
              </div>
              <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-300 mb-4">
                Nếu hai góc kề nhau cùng nhìn một cạnh dưới góc bằng nhau (bài
                toán quỹ tích cung chứa góc) thì bốn đỉnh cùng nằm trên một
                đường tròn.
              </p>
            </div>
            <div className="w-full h-48 bg-slate-50 dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-700 overflow-hidden flex items-center justify-center">
              <img
                src="/cyclic-same-arc.png"
                alt="Góc nội tiếp cùng cung"
                className="max-w-full max-h-full p-2 object-contain transition-transform duration-500 group-hover:scale-105"
              />
            </div>
          </div>

          {/* ==================== CÁCH 3 ==================== */}
          <div className="group flex flex-col h-full border rounded-2xl p-5 hover:shadow-xl transition-shadow dark:border-slate-700 bg-white dark:bg-slate-800">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <span className="bg-linear-to-r from-orange-500 to-amber-500 text-white font-bold px-3 py-1 rounded-lg text-xs shadow-sm">
                  CÁCH 3
                </span>
                <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">
                  Góc ngoài bằng góc trong đối diện
                </h3>
              </div>
              <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-300 mb-4">
                Góc ngoài tại một đỉnh bằng góc trong tại đỉnh đối diện. Thực
                chất đây là hệ quả trực tiếp của cách 1 (Tổng hai góc đối =
                180°).
              </p>
            </div>
            <div className="w-full h-48 bg-slate-50 dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-700 overflow-hidden flex items-center justify-center">
              <img
                src="/cyclic-exterior.png"
                alt="Góc ngoài = góc trong đối diện"
                className="max-w-full max-h-full p-2 object-contain transition-transform duration-500 group-hover:scale-105"
              />
            </div>
          </div>

          {/* ==================== CÁCH 4 ==================== */}
          <div className="group flex flex-col h-full border rounded-2xl p-5 hover:shadow-xl transition-shadow dark:border-slate-700 bg-white dark:bg-slate-800">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <span className="bg-linear-to-r from-purple-500 to-pink-500 text-white font-bold px-3 py-1 rounded-lg text-xs shadow-sm">
                  CÁCH 4
                </span>
                <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">
                  Bốn đỉnh cách đều một điểm
                </h3>
              </div>
              <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-300 mb-4">
                Định nghĩa gốc: Bốn điểm A, B, C, D cùng nằm trên một đường tròn
                khi và chỉ khi tồn tại điểm O (tâm) sao cho OA = OB = OC = OD =
                R.
              </p>
            </div>
            <div className="w-full h-48 bg-slate-50 dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-700 overflow-hidden flex items-center justify-center">
              <img
                src="/cyclic-center.jpg"
                alt="Tâm đường tròn ngoại tiếp"
                className="max-w-full max-h-full p-2 object-contain transition-transform duration-500 group-hover:scale-105"
              />
            </div>
          </div>
        </div>
      </InfoModal>
    </div>
  );
}

export default App;
