import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function CameraPermission() {
  const navigate = useNavigate();
  const [isRequesting, setIsRequesting] = useState(false);

  const handleAllow = async () => {
    setIsRequesting(true);
    try {
      // 카메라 권한 요청
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      // 권한 승인 후 스트림 정지 (Camera 페이지에서 다시 시작)
      stream.getTracks().forEach(track => track.stop());
      // 카메라 페이지로 이동
      navigate('/camera');
    } catch (error) {
      console.error('카메라 권한 거부:', error);
      alert('카메라 접근 권한이 거부되었습니다. 브라우저 설정에서 카메라 권한을 허용해주세요.');
      setIsRequesting(false);
    }
  };

  const handleLater = () => {
    navigate('/');
  };

  return (
    <div className="mx-auto flex h-screen max-w-sm flex-col">
      <main className="flex flex-1 flex-col justify-center p-8 text-center">
        <div className="flex flex-col items-center">
          <div className="flex h-32 w-32 items-center justify-center rounded-full bg-primary/10">
            <span className="text-7xl text-primary">📷</span>
          </div>
          <h1 className="mt-8 text-2xl font-bold">카메라 접근 허용</h1>
          <p className="mt-4 text-text-light-secondary">
            진행 상황 분석을 위해 카메라 접근 권한이 필요합니다. 사진은 비공개로 분석에만 사용됩니다.
          </p>
        </div>
      </main>
      <footer className="p-8 pt-0">
        <div className="space-y-4">
          <button
            onClick={handleAllow}
            disabled={isRequesting}
            className="w-full rounded-full bg-primary py-4 font-bold text-white hover:bg-opacity-90 transition-colors disabled:opacity-50"
          >
            {isRequesting ? '권한 요청 중...' : '접근 허용'}
          </button>
          <button
            onClick={handleLater}
            className="w-full rounded-full py-4 font-bold text-text-light-secondary hover:bg-gray-100 transition-colors"
          >
            나중에
          </button>
        </div>
      </footer>
    </div>
  );
}
