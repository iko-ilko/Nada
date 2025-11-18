import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function PhotoResult() {
  const navigate = useNavigate();
  const [question, setQuestion] = useState('');
  const [photoUrl, setPhotoUrl] = useState(null);

  useEffect(() => {
    // localStorage에서 촬영한 사진 불러오기
    const savedPhoto = localStorage.getItem('capturedPhoto');
    if (savedPhoto) {
      setPhotoUrl(savedPhoto);
    }
  }, []);

  const handleSendQuestion = () => {
    if (question.trim()) {
      console.log('질문:', question);
      setQuestion('');
    }
  };

  return (
    <div className="mx-auto flex h-screen max-w-sm flex-col overflow-hidden">
      <main className="flex flex-1 flex-col px-6 pt-8 pb-4">
        <div className="flex-grow cursor-pointer" onClick={() => navigate('/analysis-detail')}>
          {photoUrl ? (
            <img
              alt="촬영된 사진"
              className="h-full w-full rounded-3xl object-cover"
              src={photoUrl}
            />
          ) : (
            <div className="h-full w-full rounded-3xl bg-gray-200 flex items-center justify-center">
              <p className="text-gray-500">사진을 불러오는 중...</p>
            </div>
          )}
        </div>
        <div className="py-4">
          <div className="relative flex items-center">
            <input
              className="w-full rounded-full border-slate-300 bg-surface-light py-3 pl-4 pr-12 text-sm text-text-light-primary placeholder:text-text-light-secondary focus:border-primary focus:ring-primary"
              placeholder="분석 결과에 대해 질문해주세요..."
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendQuestion()}
            />
            <button
              onClick={handleSendQuestion}
              className="absolute right-1.5 flex h-9 w-9 items-center justify-center rounded-full bg-primary text-white hover:bg-opacity-90 transition-colors"
            >
              <span className="text-xl">↑</span>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
