import { useEffect, useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export default function Camera() {
  const navigate = useNavigate();
  const location = useLocation();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [error, setError] = useState('');
  const [capturedImage, setCapturedImage] = useState(null);

  useEffect(() => {
    const initCamera = async () => {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'user',
            width: { ideal: 1280 },
            height: { ideal: 720 }
          }
        });

        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
        setStream(mediaStream);
      } catch (err) {
        console.error('Camera initialization error:', err);
        if (err.name === 'NotAllowedError') {
          setError('카메라 접근이 거부되었습니다. 브라우저 설정에서 카메라 권한을 허용해주세요.');
        } else if (err.name === 'NotFoundError') {
          setError('카메라를 찾을 수 없습니다.');
        } else {
          setError('카메라 초기화 중 오류가 발생했습니다.');
        }
      }
    };

    initCamera();

    // Cleanup
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const context = canvas.getContext('2d');
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      const imageData = canvas.toDataURL('image/jpeg');
      setCapturedImage(imageData);

      // Stop the stream
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }

      // Navigate to photo result with captured image
      navigate('/photo-result', { state: { capturedImage: imageData } });
    }
  };

  return (
    <div className="font-display bg-gray-900">
      <div className="mx-auto flex h-screen max-w-sm flex-col overflow-hidden bg-gray-900 text-white">
        <header className="flex h-24 shrink-0 items-center justify-center p-6 pt-10">
          <button
            onClick={() => {
              if (stream) {
                stream.getTracks().forEach(track => track.stop());
              }
              navigate(-1);
            }}
            className="absolute left-6 text-white"
          >
            <span className="material-symbols-outlined">arrow_back</span>
          </button>
        </header>
        <main className="flex flex-grow flex-col items-center justify-between p-6">
          <div className="flex-grow"></div>
          <div className="relative mb-6 h-[400px] w-full max-w-xs">
            {error ? (
              <div className="h-full w-full rounded-2xl bg-red-900/50 flex items-center justify-center p-4">
                <p className="text-sm text-white text-center">{error}</p>
              </div>
            ) : (
              <>
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="h-full w-full rounded-2xl object-cover"
                />
                <div className="absolute inset-0 rounded-2xl border-2 border-dashed border-white/50 pointer-events-none"></div>
                <div className="absolute bottom-0 left-0 w-full rounded-b-2xl bg-[#4A6341]/80 p-4 text-center backdrop-blur-sm">
                  <p className="font-semibold">가이드 라인에 얼굴을 맞춰주세요.</p>
                  <p className="text-sm text-white/80">자연스러운 표정으로 정면을 보세요.</p>
                </div>
              </>
            )}
          </div>
          <div className="flex w-full items-center justify-center space-x-6">
            <div className="w-24"></div>
            <button
              onClick={capturePhoto}
              disabled={!!error}
              className="flex h-20 w-20 items-center justify-center rounded-full border-4 border-white/50 bg-transparent hover:border-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="h-16 w-16 rounded-full bg-primary"></div>
            </button>
            <div className="w-24"></div>
          </div>
        </main>
        <canvas ref={canvasRef} className="hidden" />
      </div>
    </div>
  );
}
