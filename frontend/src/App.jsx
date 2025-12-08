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

// --- MAIN COMPONENT ---
function App() {
  const DEFAULT_TEXT = `Cho tứ giác ABCD. Biết tam giác ABC là tam giác đều. Biết tam giác DBC là tam giác đều. Chứng minh tứ giác ABCD nội tiếp.`;

  const [inputText, setInputText] = useState(DEFAULT_TEXT);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [darkMode, setDarkMode] = useState(false);

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
                    {/* Case: Mâu thuẫn */}
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

                    {/* Case: Thành công */}
                    {(result.status === "success" ||
                      (!result.status && result.solutions.length > 0)) &&
                      result.solutions.map((sol, index) => (
                        <div
                          key={index}
                          className={`p-4 rounded-lg border-l-4 text-sm leading-relaxed whitespace-pre-line shadow-sm ${
                            darkMode
                              ? "bg-emerald-900/10 border-emerald-500 text-emerald-100"
                              : "bg-emerald-50 border-emerald-500 text-slate-800"
                          }`}
                        >
                          {formatText(sol)}
                        </div>
                      ))}

                    {/* Case: Cảnh báo */}
                    {result.status !== "contradiction" &&
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
    </div>
  );
}

export default App;
