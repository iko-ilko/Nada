import { useEffect, useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export default function AnalysisDetail() {
  const navigate = useNavigate();
  const location = useLocation();
  const mountedRef = useRef(true);
  const [isLoading, setIsLoading] = useState(true);
  const [analysisData, setAnalysisData] = useState(null);
  const [references, setReferences] = useState([]);
  const [error, setError] = useState('');

  const { capturedImage, userState } = location.state || {};

  // Base64를 Blob으로 변환
  const base64ToBlob = (base64) => {
    const parts = base64.split(';base64,');
    const contentType = parts[0].split(':')[1];
    const raw = window.atob(parts[1]);
    const rawLength = raw.length;
    const uInt8Array = new Uint8Array(rawLength);

    for (let i = 0; i < rawLength; ++i) {
      uInt8Array[i] = raw.charCodeAt(i);
    }

    return new Blob([uInt8Array], { type: contentType });
  };

  const analyzeImage = async () => {
    if (!capturedImage) {
      setError('이미지가 없습니다. 다시 촬영해주세요.');
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError('');

      // FormData 생성
      const formData = new FormData();
      const imageBlob = base64ToBlob(capturedImage);
      formData.append('image_file', imageBlob, 'captured.jpg');
      formData.append('user_state', userState || '');

      const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'success') {
        setAnalysisData(data.analysis);
        setReferences(data.references || []);
      } else {
        setError(data.error || '분석 중 오류가 발생했습니다.');
      }
    } catch (err) {
      console.error('Analysis error:', err);
      setError('서버와 연결할 수 없습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Strict Mode의 이중 실행 방지
    if (!mountedRef.current) return;

    // 이미 분석 데이터가 없을 때만 API 호출
    if (!analysisData) {
      analyzeImage();
    }

    return () => {
      mountedRef.current = false;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // 카테고리명 매핑
  const categoryNames = {
    'Hair': '헤어',
    'Skin': '피부',
    'Contour': '윤곽'
  };

  return (
    <div className="font-display bg-background-light dark:bg-background-dark">
      <div className="mx-auto flex h-screen max-w-sm flex-col overflow-hidden">
        <main className="flex flex-grow flex-col overflow-y-auto px-6 pt-6">
          <div className="flex items-center">
            <button
              onClick={() => navigate('/')}
              className="mr-2 text-text-light-primary dark:text-text-dark-primary"
            >
              <span className="material-symbols-outlined">arrow_back_ios_new</span>
            </button>
            <h1 className="text-xl font-bold text-text-light-primary dark:text-text-dark-primary">
              분석 결과 상세
            </h1>
          </div>

          {/* 로딩 상태 */}
          {isLoading && (
            <div className="flex-grow flex items-center justify-center">
              <div className="text-center">
                <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent"></div>
                <p className="mt-4 text-text-light-secondary dark:text-text-dark-secondary">
                  분석 중입니다...
                </p>
              </div>
            </div>
          )}

          {/* 에러 상태 */}
          {error && !isLoading && (
            <div className="flex-grow flex items-center justify-center px-4">
              <div className="text-center">
                <div className="mb-4 text-6xl">😞</div>
                <h2 className="text-lg font-bold text-text-light-primary dark:text-text-dark-primary mb-2">
                  분석 실패
                </h2>
                <p className="text-sm text-text-light-secondary dark:text-text-dark-secondary mb-6">
                  {error}
                </p>
                <button
                  onClick={analyzeImage}
                  className="px-6 py-3 rounded-full bg-primary text-white font-bold hover:bg-opacity-90 transition-colors"
                >
                  다시 시도
                </button>
              </div>
            </div>
          )}

          {/* 성공 상태 - 분석 결과 표시 */}
          {!isLoading && !error && analysisData && (
            <>
              {/* 오늘의 한 마디 섹션 */}
              {analysisData.Summary && (
                <div className="mt-6 py-4 px-5 rounded-2xl bg-gradient-to-br from-primary/15 to-primary/6 border-l-4 border-l-primary border border-primary/20 shadow-sm dark:from-primary/20 dark:to-primary/8 dark:border-primary/30">
                  <div className="flex items-center gap-1 mb-2">
                    <span className="material-symbols-outlined text-primary text-sm flex-shrink-0">
                      lightbulb
                    </span>
                    <h2 className="text-xs font-extrabold text-primary dark:text-primary tracking-wide">
                      오늘의 한 마디
                    </h2>
                  </div>
                  <p className="text-sm text-text-light-primary dark:text-text-dark-primary italic leading-relaxed">
                    "{analysisData.Summary}"
                  </p>
                </div>
              )}

              <div className="mt-6 space-y-5">
                {Object.entries(analysisData)
                  .filter(([category]) => category !== 'Summary')
                  .map(([category, data]) => (
                  <div
                    key={category}
                    className="rounded-2xl bg-surface-light p-5 shadow-sm dark:bg-surface-dark"
                  >
                    <h2 className="text-lg font-bold text-text-light-primary dark:text-text-dark-primary">
                      {categoryNames[category] || category}
                    </h2>
                    <div className="mt-4 space-y-4">
                      <div>
                        <h3 className="font-semibold text-primary">현재 상태</h3>
                        <p className="mt-1 text-sm text-text-light-secondary dark:text-text-dark-secondary">
                          {data.status}
                        </p>
                      </div>
                      <div>
                        <h3 className="font-semibold text-primary">개선 방법</h3>
                        <ul className="mt-2 space-y-2">
                          {data.improvement_tips && data.improvement_tips.map((tip, index) => (
                            <li
                              key={index}
                              className="text-sm text-text-light-secondary dark:text-text-dark-secondary flex"
                            >
                              <span className="mr-2 text-primary">•</span>
                              <span>{tip}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* 참고자료 섹션 */}
              {references && references.length > 0 && (
                <div className="mt-8 pb-6">
                  <h2 className="text-lg font-bold text-text-light-primary dark:text-text-dark-primary mb-4 flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary">auto_stories</span>
                    <span>참고자료</span>
                  </h2>
                  <div className="space-y-2">
                    {references.map((reference, index) => {
                      // 파일 경로에서 파일명 추출
                      const fileName = reference.split('/').pop().replace('.pdf', '');
                      return (
                        <div
                          key={index}
                          className="flex items-start gap-3 bg-surface-light dark:bg-surface-dark p-3 rounded-lg"
                        >
                          <span className="text-primary text-sm font-medium shrink-0">
                            [{index + 1}]
                          </span>
                          <p className="text-sm text-text-light-secondary dark:text-text-dark-secondary flex-1">
                            {fileName}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
