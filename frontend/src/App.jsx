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

const InfoModal = ({ isOpen, onClose, title, children, className = "" }) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      
      {/* Overlay: Giữ nguyên */}
      <div className="absolute inset-0" onClick={onClose} />

      {/* Modal Container */}
      <div
        className={`relative z-10 bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-h-[90vh] flex flex-col border border-slate-200 dark:border-slate-700 ${
          className || "max-w-5xl"
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header cố định */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-100 dark:border-slate-800 shrink-0">
          <h3 className="text-xl font-bold bg-linear-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            {title}
          </h3>
          <button
            onClick={onClose}
            className="p-2 bg-slate-100 cursor-pointer dark:bg-slate-800 hover:bg-red-100 dark:hover:bg-red-900/30 text-slate-500 hover:text-red-500 rounded-full transition-all"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Phần cuộn nội dung */}
        <div className="flex-1 min-h-0 overflow-y-auto px-6 py-4">
          {children}
        </div>
      </div>
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
  const [showGuide, setShowGuide] = useState(false);
  const [showTheory, setShowTheory] = useState(false);
  const [guideStep, setGuideStep] = useState(0);

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
      className={`min-h-screen transition-colors duration-300 font-sans flex flex-col bg-slate-950 text-slate-100`}
    >
      {/* NAVBAR: Compact */}
      <nav
        className={`border-b h-14 flex items-center px-6 sticky top-0 z-50 backdrop-blur-md bg-slate-900/80 border-slate-800`}
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
            className="px-3 py-1.5 cursor-pointer text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
          >
            Hướng dẫn
          </button>
          <button
            onClick={() => setShowTheory(true)}
            className="px-3 py-1.5 cursor-pointer text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
          >
            Lý thuyết
          </button>
        </div>

      </nav>

      {/* MAIN CONTENT: Full Height Dashboard */}
      <main className="flex-1 p-4 md:p-6 overflow-hidden flex flex-col md:flex-row gap-6 max-w-[1600px] mx-auto w-full">
        {/* === LEFT COLUMN: INPUT === */}
        <div className="w-full md:w-1/3 lg:w-1/4 flex flex-col gap-4">
          <div
            className={`flex-1 rounded-2xl shadow-sm border flex flex-col p-4 bg-slate-900 border-slate-800`}
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
              className={`flex-1 w-full p-3 text-sm rounded-xl border resize-none focus:ring-2 focus:border-transparent outline-none leading-relaxed bg-slate-950 border-slate-800 text-slate-200 focus:ring-blue-500`}
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
            className={`rounded-xl border p-4 text-xs bg-indigo-900/10 border-indigo-900/30 text-indigo-300`}
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
          className={`flex-1 rounded-2xl shadow-sm border overflow-hidden flex flex-col bg-slate-900 border-slate-800`}
        >
          {/* Header Kết quả */}
          <div
            className={`h-12 px-5 border-b flex items-center justify-between border-slate-800 bg-slate-900`}
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
                className={`lg:w-5/12 flex flex-col border-b lg:border-b-0 lg:border-r border-slate-800 bg-slate-950/50`}
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
                <div className="flex-1 overflow-y-auto p-5">
                  <h4
                    className={`font-bold text-lg mb-4 flex items-center gap-2 text-slate-100
                    `}
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
                        className={`p-4 rounded-lg border-l-4 text-sm bg-red-900/20 border-red-500 text-red-200`}
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
                        className={`p-4 rounded-lg border-l-4 text-sm leading-relaxed whitespace-pre-line shadow-sm bg-yellow-900/10 border-yellow-500 text-yellow-100}`}
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
                          className={`p-4 rounded-lg border-l-4 text-sm leading-relaxed whitespace-pre-line shadow-sm transition-all duration-300 bg-emerald-900/10 border-emerald-500 text-emerald-100`}
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
      {/* --- MODAL HƯỚNG DẪN --- */}
      <InfoModal
        isOpen={showGuide}
        onClose={() => setShowGuide(false)}
        title="Hướng dẫn sử dụng GeoSolver AI"
        className="max-w-4xl" 
      >
        <div className="flex flex-col">
          <div className="flex justify-center mb-6">
            <div className="flex gap-4 md:gap-16">
              {["Bước 1", "Bước 2", "Bước 3"].map((label, index) => (
                <button
                  key={index}
                  onClick={() => setGuideStep(index)}
                  className={`flex flex-col items-center gap-2 group transition-all cursor-pointer duration-300 ${
                    guideStep === index ? "opacity-100" : "opacity-50 hover:opacity-100"
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm shadow-sm transition-all border-2 ${
                      guideStep === index
                        ? "bg-blue-600 border-blue-600 text-white scale-110"
                        : "bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-600 text-slate-500"
                    }`}
                  >
                    {index + 1}
                  </div>
                  <span className={`text-[10px] font-bold uppercase tracking-wider ${
                    guideStep === index ? "text-blue-600 dark:text-blue-400" : "text-slate-500"
                  }`}>
                    {label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Main Content Area - ĐÃ THU NHỎ KÍCH THƯỚC */}
          <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-1 border border-slate-100 dark:border-slate-700 shadow-inner">
            <div className="grid md:grid-cols-2 gap-6 items-center min-h-80 p-4">
              
              {/* Cột 1: Hình ảnh minh họa (Giảm chiều cao xuống còn 240px) */}
              <div className="relative h-[200px] md:h-60 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 flex items-center justify-center overflow-hidden group">
                <img
                  src={`/step${guideStep + 1}.png`} 
                  alt={`Minh họa bước ${guideStep + 1}`}
                  className="max-w-full max-h-full object-contain p-2 transition-transform duration-500 group-hover:scale-105"
                  onError={(e) => {
                    e.target.style.display = 'none'; 
                    e.target.nextSibling.style.display = 'flex'; 
                  }}
                />
                {/* Fallback khi chưa có ảnh */}
                <div className="hidden absolute inset-0 flex-col items-center justify-center text-slate-300 dark:text-slate-600 bg-slate-50 dark:bg-slate-900">
                  <span className="text-3xl">🖼️</span>
                  <span className="text-xs mt-2 font-medium">Ảnh bước {guideStep + 1}</span>
                </div>
              </div>

              {/* Cột 2: Nội dung chữ (Giảm spacing và font size) */}
              <div className="flex flex-col justify-center space-y-4 h-full">
                
                {guideStep === 0 && (
                  <div className="animate-in slide-in-from-right-4 fade-in duration-300">
                    <h3 className="text-xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                      Bước 1: Nhập đề toán
                    </h3>
                    <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed mb-3">
                      Nhập đề bài hình học phẳng vào ô văn bản. Hãy sử dụng <strong>tiếng Việt có dấu</strong>.
                    </p>
                    <div className="bg-white dark:bg-slate-900 p-3 rounded-lg border border-blue-100 dark:border-blue-900/50 shadow-sm">
                      <div className="text-[10px] font-bold text-slate-400 uppercase mb-1">Ví dụ:</div>
                      <p className="font-mono text-xs text-slate-700 dark:text-slate-300">
                        "Cho tam giác ABC đều. Đường cao AH. Chứng minh..."
                      </p>
                    </div>
                  </div>
                )}

                {guideStep === 1 && (
                  <div className="animate-in slide-in-from-right-4 fade-in duration-300">
                    <h3 className="text-xl font-bold text-indigo-600 dark:text-indigo-400 mb-2">
                      Bước 2: Phân tích & Giải
                    </h3>
                    <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed mb-3">
                      Bấm nút <strong>"Giải ngay"</strong>. AI sẽ thực hiện:
                    </p>
                    <ul className="space-y-2">
                      {[
                        "Trích xuất dữ kiện",
                        "Suy luận logic",
                        "Tính toán tọa độ",
                        "Kiểm tra đề bài"
                      ].map((item, i) => (
                        <li key={i} className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-200">
                          <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-300 p-0.5 rounded-full">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
                          </span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {guideStep === 2 && (
                  <div className="animate-in slide-in-from-right-4 fade-in duration-300">
                    <h3 className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mb-2">
                      Bước 3: Nhận kết quả
                    </h3>
                    <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                      Kết quả bao gồm hai phần trực quan:
                    </p>
                    <div className="grid grid-cols-2 gap-3 mt-3">
                      <div className="bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-700 text-center">
                        <div className="text-xl mb-1">📐</div>
                        <div className="font-bold text-sm text-slate-700 dark:text-slate-200">Hình vẽ</div>
                      </div>
                      <div className="bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-700 text-center">
                        <div className="text-xl mb-1">📝</div>
                        <div className="font-bold text-sm text-slate-700 dark:text-slate-200">Lời giải</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Navigation Buttons (Bottom) */}
                <div className="flex gap-3 pt-2 mt-auto">
                  <button
                    onClick={() => setGuideStep((prev) => Math.max(0, prev - 1))}
                    disabled={guideStep === 0}
                    className={`px-4 py-2 cursor-pointer text-sm rounded-lg font-medium transition-all ${
                      guideStep === 0
                        ? "bg-slate-100 text-slate-400 cursor-not-allowed dark:bg-slate-800 dark:text-slate-600"
                        : "bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 shadow-sm dark:bg-slate-700 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-600"
                    }`}
                  >
                    Quay lại
                  </button>
                  <button
                    onClick={() => {
                        if (guideStep === 2) setShowGuide(false);
                        else setGuideStep((prev) => Math.min(2, prev + 1));
                    }}
                    className="flex-1 cursor-pointer bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 text-sm rounded-lg font-medium shadow-md shadow-blue-500/20 transition-all active:scale-95"
                  >
                    {guideStep === 2 ? "Bắt đầu sử dụng" : "Tiếp theo"}
                  </button>
                </div>
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
        className="max-w-6xl"
      >
        <div className="grid gap-6 md:grid-cols-2">
          {[
            {
              id: 1,
              color: "from-blue-500 to-cyan-500",
              title: "Tổng hai góc đối bằng 180°",
              desc: "Tứ giác có tổng hai góc đối diện bằng 180° là tứ giác nội tiếp. Đây là dấu hiệu nhận biết phổ biến nhất.",
              img: "/cyclic-sum-180.jpg",
              icon: "🔵"
            },
            {
              id: 2,
              color: "from-emerald-500 to-teal-500",
              title: "Hai đỉnh kề cùng nhìn một cạnh",
              desc: "Nếu hai đỉnh kề nhau cùng nhìn cạnh chứa hai đỉnh còn lại dưới một góc alpha bằng nhau thì tứ giác đó nội tiếp.",
              img: "/cyclic-same-arc.png",
              icon: "🟢"
            },
            {
              id: 3,
              color: "from-orange-500 to-amber-500",
              title: "Góc ngoài tại một đỉnh",
              desc: "Góc ngoài tại một đỉnh bằng góc trong tại đỉnh đối diện. Đây là hệ quả trực tiếp của tính chất tổng hai góc đối.",
              img: "/cyclic-exterior.png",
              icon: "🟠"
            },
            {
              id: 4,
              color: "from-purple-500 to-pink-500",
              title: "Bốn đỉnh cách đều một điểm",
              desc: "Nếu tồn tại một điểm O sao cho OA = OB = OC = OD thì bốn điểm A, B, C, D nằm trên đường tròn tâm O.",
              img: "/cyclic-center.jpg",
              icon: "🟣"
            }
          ].map((item) => (
            <div 
              key={item.id} 
              className="group flex flex-col h-full bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 hover:shadow-xl hover:border-blue-300 dark:hover:border-blue-700 transition-all duration-300 overflow-hidden"
            >
              {/* Header Card */}
              <div className="p-6 pb-2 flex-1">
                <div className="flex items-center justify-between mb-4">
                  <span className={`bg-linear-to-r ${item.color} text-white text-xs font-bold px-3 py-1 rounded-full shadow-sm`}>
                    PHƯƠNG PHÁP {item.id}
                  </span>
                  <span className="text-2xl opacity-80 group-hover:scale-110 transition-transform">{item.icon}</span>
                </div>
                <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  {item.title}
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                  {item.desc}
                </p>
              </div>

              {/* Image Container */}
              <div className="mt-auto p-6 pt-2">
                <div className="w-full h-48 bg-slate-50 dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-700 overflow-hidden flex items-center justify-center relative">
                  <img
                    src={item.img}
                    alt={item.title}
                    className="max-w-full max-h-full p-2 object-contain transition-transform duration-500 group-hover:scale-105 z-10"
                    onError={(e) => e.target.style.opacity = 0}
                  />
                  <div className="absolute inset-0 opacity-5 bg-[radial-linear(#444cf7_1px,transparent_1px)] bg-size:[16px_16px]"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </InfoModal>
    </div>
  );
}

export default App;
