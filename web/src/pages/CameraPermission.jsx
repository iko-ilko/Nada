import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function CameraPermission() {
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const requestCameraAccess = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user' }
      });
      // 권한을 받았으면 스트림을 즉시 중지하고 카메라 페이지로 이동
      stream.getTracks().forEach(track => track.stop());
      navigate('/camera', { state: { hasPermission: true } });
    } catch (err) {
      console.error('Camera access error:', err);
      if (err.name === 'NotAllowedError') {
        setError('카메라 접근이 거부되었습니다. 브라우저 설정에서 카메라 권한을 허용해주세요.');
      } else if (err.name === 'NotFoundError') {
        setError('카메라를 찾을 수 없습니다.');
      } else {
        setError('카메라 접근 중 오류가 발생했습니다.');
      }
    }
  };

  const skipPermission = () => {
    navigate('/camera', { state: { hasPermission: false } });
  };

  return (
    <div className="font-display bg-background-light dark:bg-background-dark text-text-light-primary dark:text-text-dark-primary">
      <div className="mx-auto flex h-screen max-w-sm flex-col">
        <main className="flex flex-1 flex-col justify-center p-8 text-center">
          <div className="flex flex-col items-center">
            <div className="flex h-32 w-32 items-center justify-center rounded-full bg-primary/10 dark:bg-primary/20">
              <span className="material-symbols-outlined text-7xl text-primary">photo_camera</span>
            </div>
            <h1 className="mt-8 text-2xl font-bold">카메라 접근 허용</h1>
            <p className="mt-4 text-text-light-secondary dark:text-text-dark-secondary">
              진행 상황 분석을 위해 카메라 접근 권한이 필요합니다. 사진은 비공개로 분석에만 사용됩니다.
            </p>
            {error && (
              <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              </div>
            )}
          </div>
        </main>
        <footer className="p-8 pt-0">
          <div className="space-y-4">
            <button
              onClick={requestCameraAccess}
              className="w-full rounded-full bg-primary py-4 font-bold text-white hover:bg-opacity-90 transition-colors"
            >
              접근 허용
            </button>
            <button
              onClick={skipPermission}
              className="w-full rounded-full py-4 font-bold text-text-light-secondary dark:text-text-dark-secondary hover:text-text-light-primary dark:hover:text-text-dark-primary transition-colors"
            >
              나중에
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}
