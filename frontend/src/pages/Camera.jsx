import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Camera() {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [capturedImage, setCapturedImage] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    startCamera();
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'user',
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err) {
      console.error('카메라 접근 오류:', err);
      setError('카메라에 접근할 수 없습니다. 권한을 확인해주세요.');
    }
  };

  const handleCapture = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      canvas.toBlob((blob) => {
        const imageUrl = URL.createObjectURL(blob);
        setCapturedImage(imageUrl);

        // 스트림 정지
        if (stream) {
          stream.getTracks().forEach(track => track.stop());
        }

        // 촬영된 이미지를 localStorage에 저장 (다음 페이지에서 사용)
        canvas.toDataURL('image/jpeg', 0.9);
        localStorage.setItem('capturedPhoto', canvas.toDataURL('image/jpeg', 0.9));

        // PhotoResult 페이지로 이동
        setTimeout(() => {
          navigate('/photo-result');
        }, 500);
      }, 'image/jpeg', 0.9);
    }
  };

  if (error) {
    return (
      <div className="mx-auto flex h-screen max-w-sm flex-col overflow-hidden bg-gray-900 text-white items-center justify-center p-6">
        <div className="text-center">
          <span className="text-6xl mb-4 block">⚠️</span>
          <p className="text-xl font-semibold mb-2">{error}</p>
          <button
            onClick={() => navigate(-1)}
            className="mt-6 px-6 py-3 bg-primary rounded-full text-white font-bold hover:bg-opacity-90 transition-colors"
          >
            돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto flex h-screen max-w-sm flex-col overflow-hidden bg-gray-900 text-white">
      <header className="flex h-24 shrink-0 items-center justify-center p-6 pt-10">
      </header>
      <main className="flex flex-grow flex-col items-center justify-between p-6">
        <div className="flex-grow"></div>
        <div className="relative mb-6 h-[400px] w-full max-w-xs">
          {/* 비디오 스트림 */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="h-full w-full rounded-2xl object-cover"
          />
          {/* 가이드 오버레이 */}
          <div className="absolute inset-0 h-full w-full rounded-2xl border-2 border-dashed border-white/50 pointer-events-none"></div>
          <div className="absolute bottom-0 left-0 w-full rounded-b-2xl bg-[#4A6341]/80 p-4 text-center backdrop-blur-sm">
            <p className="font-semibold">가이드 라인에 얼굴을 맞춰주세요.</p>
            <p className="text-sm text-white/80">자연스러운 표정으로 정면을 보세요.</p>
          </div>
          {/* 캡처용 숨겨진 캔버스 */}
          <canvas ref={canvasRef} className="hidden" />
        </div>
        <div className="flex w-full items-center justify-center space-x-6">
          <div className="w-24"></div>
          <button
            onClick={handleCapture}
            className="flex h-20 w-20 items-center justify-center rounded-full border-4 border-white/50 bg-transparent hover:border-white transition-colors"
          >
            <div className="h-16 w-16 rounded-full bg-primary"></div>
          </button>
          <div className="w-24"></div>
        </div>
      </main>
    </div>
  );
}
