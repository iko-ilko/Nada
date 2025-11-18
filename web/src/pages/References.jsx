import { useLocation, useNavigate } from 'react-router-dom';

export default function References() {
  const location = useLocation();
  const navigate = useNavigate();
  const references = location.state?.references || [];

  // 파일 경로에서 파일명 추출
  const extractFileName = (filePath) => {
    if (!filePath) return '';
    const parts = filePath.split('/');
    return parts[parts.length - 1].replace('.pdf', '');
  };

  return (
    <div className="font-display">
      <div className="relative flex h-auto min-h-screen w-full flex-col bg-background-light dark:bg-background-dark text-text-light-primary dark:text-text-dark-primary">
        <header className="sticky top-0 z-10 flex h-16 items-center border-b border-gray-200 dark:border-gray-700 bg-background-light/80 dark:bg-background-dark/80 px-4 backdrop-blur-sm">
          <button
            onClick={() => navigate(-1)}
            className="mr-2 text-text-light-primary dark:text-text-dark-primary"
          >
            <span className="material-symbols-outlined">arrow_back</span>
          </button>
          <h1 className="text-xl font-bold leading-tight flex-1 text-center">참고자료</h1>
          <div className="w-10"></div>
        </header>
        <main className="flex flex-col flex-1 px-4 pt-6 max-w-sm mx-auto w-full">
          {references.length === 0 ? (
            <div className="flex-grow flex items-center justify-center py-20">
              <div className="text-center">
                <div className="mb-4 text-6xl">📚</div>
                <p className="text-text-light-secondary dark:text-text-dark-secondary">
                  참고자료가 없습니다
                </p>
              </div>
            </div>
          ) : (
            <div className="flex flex-col space-y-3 pb-6">
              {references.map((reference, index) => (
                <a
                  key={index}
                  className="flex items-center gap-4 bg-surface-light dark:bg-surface-dark p-4 min-h-14 justify-between rounded-lg hover:bg-primary/10 transition-colors duration-200 shadow-sm"
                  href="#"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className="flex items-center justify-center rounded-lg bg-primary/20 shrink-0 size-10 text-primary">
                      <span className="material-symbols-outlined">description</span>
                    </div>
                    <p className="text-base font-normal leading-normal flex-1">
                      {extractFileName(reference)}
                    </p>
                  </div>
                  <div className="shrink-0 text-text-light-secondary dark:text-text-dark-secondary">
                    <span className="material-symbols-outlined">chevron_right</span>
                  </div>
                </a>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
