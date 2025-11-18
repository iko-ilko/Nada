import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export default function PhotoResult() {
  const navigate = useNavigate();
  const location = useLocation();
  const [question, setQuestion] = useState('');
  const capturedImage = location.state?.capturedImage;

  const handleSubmit = () => {
    navigate('/analysis-detail', {
      state: {
        capturedImage,
        userState: question.trim()
      }
    });
  };

  const handleImageClick = () => {
    navigate('/analysis-detail', {
      state: {
        capturedImage,
        userState: ''
      }
    });
  };

  return (
    <div className="font-display bg-background-light dark:bg-background-dark">
      <div className="mx-auto flex h-screen max-w-sm flex-col overflow-hidden">
        <main className="flex flex-1 flex-col px-6 pt-8 pb-4">
          <div className="flex-grow cursor-pointer" onClick={handleImageClick}>
            {capturedImage ? (
              <img
                src={capturedImage}
                alt="Captured"
                className="h-full w-full rounded-3xl object-cover"
              />
            ) : (
              <div className="h-full w-full rounded-3xl bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center">
                <span className="text-6xl">📸</span>
              </div>
            )}
          </div>
          <div className="py-4">
            <div className="relative flex items-center">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
                className="w-full rounded-full border-slate-300 bg-surface-light py-3 pl-4 pr-12 text-sm text-text-light-primary placeholder:text-text-light-secondary focus:border-primary focus:ring-primary dark:border-zinc-700 dark:bg-surface-dark dark:text-text-dark-primary dark:placeholder:text-text-dark-secondary"
                placeholder="분석 결과에 대해 질문해주세요..."
              />
              <button
                onClick={handleSubmit}
                className="absolute right-1.5 flex h-9 w-9 items-center justify-center rounded-full bg-primary text-white hover:bg-opacity-90 transition-colors"
              >
                <span className="material-symbols-outlined">arrow_upward</span>
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
