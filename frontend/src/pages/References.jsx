import { useNavigate } from 'react-router-dom';

export default function References() {
  const navigate = useNavigate();

  const references = [
    { title: '심리적 안녕감에서 자기연민의 역할' },
    { title: '마음챙김이 감정 조절에 미치는 영향' },
    { title: '긍정심리학 개입: 메타분석' },
    { title: '회복탄력성 구축: 역경을 극복하기 위한 안내서' },
    { title: '감사함이 정신 건강에 미치는 영향' }
  ];

  return (
    <div className="relative flex h-auto min-h-screen w-full flex-col bg-background-light overflow-x-hidden text-text-light">
      <header className="sticky top-0 z-10 flex h-16 items-center border-b border-gray-200 bg-background-light/80 px-4 backdrop-blur-sm">
        <button
          onClick={() => navigate(-1)}
          className="mr-2 text-text-light-primary"
        >
          <span className="text-xl">←</span>
        </button>
        <h1 className="text-xl font-bold leading-tight flex-1 text-center">참고자료</h1>
        <div className="w-6"></div>
      </header>
      <main className="flex flex-col flex-1 px-4 pt-6">
        <div className="flex flex-col space-y-3">
          {references.map((ref, index) => (
            <a
              key={index}
              className="flex items-center gap-4 bg-white p-4 min-h-14 justify-between rounded-lg hover:bg-primary/10 transition-colors duration-200 cursor-pointer"
              href="#"
              onClick={(e) => {
                e.preventDefault();
                console.log('참고자료 클릭:', ref.title);
              }}
            >
              <div className="flex items-center gap-4 flex-1">
                <div className="flex items-center justify-center rounded-lg bg-primary/20 shrink-0 size-10 text-primary">
                  <span className="text-2xl">📄</span>
                </div>
                <p className="text-base font-normal leading-normal flex-1">
                  {ref.title}
                </p>
              </div>
              <div className="shrink-0 text-gray-400">
                <span className="text-xl">›</span>
              </div>
            </a>
          ))}
        </div>
      </main>
    </div>
  );
}
