import { useNavigate } from 'react-router-dom';

export default function AnalysisDetail() {
  const navigate = useNavigate();

  const analysisData = [
    {
      category: '헤어',
      currentState: '모발 끝이 건조하고 푸석해요.',
      improvement: '헤어 팩 사용 주기를 늘려주세요.'
    },
    {
      category: '피부',
      currentState: '피부톤이 불균일하고 트러블이 있어요.',
      improvement: '진정 앰플 사용을 추천해요.'
    },
    {
      category: '윤곽',
      currentState: '얼굴 라인이 전체적으로 처져있어요.',
      improvement: '페이스 요가를 꾸준히 해주세요.'
    }
  ];

  return (
    <div className="mx-auto flex h-screen max-w-sm flex-col overflow-hidden">
      <main className="flex flex-grow flex-col overflow-y-auto px-6 pt-6">
        <div className="flex items-center">
          <button
            onClick={() => navigate(-1)}
            className="mr-2 text-text-light-primary"
          >
            <span className="text-xl">←</span>
          </button>
          <h1 className="text-xl font-bold text-text-light-primary">
            분석 결과 상세
          </h1>
        </div>
        <div className="mt-6 space-y-5">
          {analysisData.map((item, index) => (
            <div
              key={index}
              className="rounded-2xl bg-surface-light p-5 shadow-sm"
            >
              <h2 className="text-lg font-bold text-text-light-primary">
                {item.category}
              </h2>
              <div className="mt-4 space-y-4">
                <div>
                  <h3 className="font-semibold text-primary">현재 상태</h3>
                  <p className="mt-1 text-sm text-text-light-secondary">
                    {item.currentState}
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold text-primary">개선 방법</h3>
                  <p className="mt-1 text-sm text-text-light-secondary">
                    {item.improvement}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-auto space-y-3 pb-4 pt-4">
          <button
            onClick={() => navigate('/references')}
            className="flex w-full items-center justify-center gap-2 rounded-full bg-primary py-4 font-bold text-white hover:bg-opacity-90 transition-colors"
          >
            <span className="text-xl">📚</span>
            <span>참고자료 버튼</span>
          </button>
        </div>
      </main>
    </div>
  );
}
