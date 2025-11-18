import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Occupation() {
  const navigate = useNavigate();
  const [occupation, setOccupation] = useState('');

  const suggestions = ['회사원', '학생', '프리랜서'];

  return (
    <div className="mx-auto flex h-full max-w-sm flex-col px-6 pt-16">
      <div className="flex flex-col items-center">
        <div className="relative mb-8 h-[7.5rem] w-[7.5rem]">
          <div className="absolute inset-0 rounded-full bg-[#E0F3D1]"></div>
          <img
            alt="다양한 직업을 나타내는 아이콘들"
            className="absolute inset-0"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuAI0DgLGmPnHme8NZOB6VrIEm1xnu25QtpcgdtOALPej5QDxPrZO0EHUQeldIO31y7fqpKVmmbkywRilcxSBf-kIqGUhTgHoV71APMq5xd-yquEdIg0UCHb2rRmoOUwRSVDu2_jpMHCk0fMjPwgQEyUTvw-UxU6FxA2fxqY-YlX4DnVyK0f56I-7useN_xxgSFeBqdm6rIoCpW_2Nosy7BT7LO1244Z4a3-lKDC7QSdOJ2zBDvQ4PYzGluQa7G2OXOs2p0Pqj7n1AY"
          />
        </div>
        <h1 className="text-2xl font-bold text-text-light-primary">
          직업을 알려주세요
        </h1>
        <p className="mt-2 text-center text-sm text-text-light-secondary">
          직업에 맞는 실용적인 개선 팁을 드려요
        </p>
      </div>
      <main className="mt-12 flex-grow">
        <div className="space-y-3">
          <input
            className="w-full rounded-xl border border-gray-300 bg-white px-4 py-3.5 text-sm placeholder-gray-400 focus:border-primary focus:ring-primary"
            placeholder="자유롭게 적어주세요!"
            type="text"
            value={occupation}
            onChange={(e) => setOccupation(e.target.value)}
          />
          <div className="grid grid-cols-3 gap-2">
            {suggestions.map((item) => (
              <button
                key={item}
                onClick={() => setOccupation(item)}
                className="rounded-full border border-gray-300 bg-white px-3 py-2 text-center text-sm text-text-light-secondary hover:bg-primary/10 transition-colors"
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      </main>
      <div className="pb-8 pt-4">
        <button
          onClick={() => navigate('/camera-permission')}
          className="w-full rounded-full bg-primary py-4 text-center font-bold text-white shadow-lg shadow-primary/30 hover:bg-opacity-90 transition-colors"
        >
          다음
        </button>
      </div>
    </div>
  );
}
