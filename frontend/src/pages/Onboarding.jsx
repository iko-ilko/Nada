import { useNavigate } from 'react-router-dom';

export default function Onboarding() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col h-screen max-w-sm mx-auto p-8 justify-between">
      <main className="flex-grow flex flex-col items-center justify-center text-center">
        <h2 className="text-4xl font-bold text-primary mb-2 mt-16">
          NADA = 나다
        </h2>
        <p className="text-base text-subtext-light mb-2">
          "있는 그대로의 나"
        </p>
        <p className="text-lg text-text-light mb-16">
          후천적 노력으로 만드는 완벽한 나
        </p>
        <ul className="space-y-6 text-left text-text-light w-full max-w-xs">
          <li className="flex items-center">
            <span className="text-2xl mr-4">📸</span>
            <span>AI 기반 외모 분석으로 개인 맞춤 뷰티</span>
          </li>
          <li className="flex items-center">
            <span className="text-2xl mr-4">✨</span>
            <span>정면/측면 촬영으로 정확한 얼굴 분석</span>
          </li>
          <li className="flex items-center">
            <span className="text-2xl mr-4">🎯</span>
            <span>개인별 맞춤 뷰티 루틴 및 개선 가이드</span>
          </li>
          <li className="flex items-center">
            <span className="text-2xl mr-4">🔑</span>
            <span>로그인 없이도 기본 분석 가능</span>
          </li>
        </ul>
      </main>
      <footer className="w-full pb-4">
        <button
          onClick={() => navigate('/occupation')}
          className="w-full bg-primary text-white font-bold py-4 px-6 rounded-full text-lg shadow-lg hover:bg-opacity-90 transition-colors"
        >
          시작하기
        </button>
      </footer>
    </div>
  );
}
