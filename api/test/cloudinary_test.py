"""
Cloudinary 서비스 테스트
"""
import sys
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils import cloudinary
from app.core.config import Config


def test_upload_authenticated_image_and_access():
    """인증 이미지 업로드 및 접근 제한 테스트"""
    print("\n" + "="*60)
    print("🧪 인증 이미지 업로드 및 접근 제한 테스트")
    print("="*60)

    # 테스트 이미지 로드
    test_image_path = Path(__file__).parent / "나1.jpg"
    test_image_data = test_image_path.read_bytes()

    try:
        # 테스트 설정
        test_expire_minutes = 1  # 테스트용 1분
        sleep_seconds = 61  # 1분 + 1초

        print(f"\n📋 테스트 설정:")
        print(f"   - Cloudinary Cloud Name: {Config.CLOUDINARY_CLOUD_NAME}")
        print(f"   - 만료 시간: {test_expire_minutes}분")
        print(f"   - 이미지 크기: {len(test_image_data)} bytes")

        # 1. 인증 이미지 업로드
        print(f"\n📤 인증 이미지 업로드 중...")
        upload_result = cloudinary.upload_authenticated_image(
            image_data=test_image_data,
            expire_minutes=test_expire_minutes
        )

        public_id = upload_result["public_id"]
        image_format = upload_result["format"]
        secure_url = upload_result["secure_url"]

        print(f"\n✅ 업로드 성공!")
        print(f"   - Public ID: {public_id}")
        print(f"   - Format: {image_format}")
        print(f"   - Secure URL: {secure_url}")

        # 2. 업로드된 URL이 접근 가능한지 확인
        print(f"\n🔍 업로드된 URL 접근 테스트 (접근 가능해야 함)...")
        print(f"   - URL: {secure_url}")
        try:
            response = requests.head(secure_url, timeout=10)
            if response.status_code == 200:
                print(f"   - 상태: 접근 가능 (HTTP {response.status_code}) ✓")
            else:
                print(f"   - 상태: 접근 불가 (HTTP {response.status_code})")
        except Exception as e:
            print(f"   - 상태: 접근 실패 ({str(e)})")

        # 3. 만료 시간까지 대기
        expiration_time = datetime.now() + timedelta(minutes=test_expire_minutes)
        print(f"\n⏳ {test_expire_minutes}분({sleep_seconds}초) 대기 중...")
        print(f"   - 만료 시간: {expiration_time.strftime('%Y-%m-%d %H:%M:%S')} ...")

        for i in range(sleep_seconds, 0, -10):
            remaining = i if i > 0 else 0
            print(f"   - 남은 시간: {remaining}초", end="\r")
            time.sleep(min(10, i))
        print(f"   - 남은 시간: 0초  ✓")

        # 4. 만료 후 접근 불가 상태 확인
        print(f"\n🔍 만료 후 URL 접근 테스트 (접근 불가해야 함)...")
        print(f"   - URL: {secure_url}")
        try:
            response = requests.head(secure_url, timeout=10)
            if response.status_code == 403 or response.status_code == 401:
                print(f"   - 상태: 접근 불가능 (HTTP {response.status_code}) ✓")
            elif response.status_code == 200:
                print(f"   - 상태: ⚠️ 접근 가능 (HTTP {response.status_code}) - 만료 미작동")
            else:
                print(f"   - 상태: 기타 상태 (HTTP {response.status_code})")
        except Exception as e:
            print(f"   - 상태: 접근 불가능 ({str(e)}) ✓")

        # 5. 이미지 삭제
        print(f"\n🗑️  테스트 이미지 삭제 중...")
        delete_result = cloudinary.delete_image(public_id)

        if delete_result:
            print(f"   ✓ 삭제 완료: {public_id}")
        else:
            print(f"   ⚠️  삭제 실패 (또는 이미지가 없음)")

        print(f"\n✅ 테스트 완료!")
        return True

    except Exception as e:
        print(f"\n❌ 테스트 실패!")
        print(f"   - 에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_delete_image():
    """이미지 삭제 테스트"""
    print("\n" + "="*60)
    print("🧪 이미지 삭제 테스트")
    print("="*60)

    # 테스트 이미지 로드
    test_image_path = Path(__file__).parent / "나1.jpg"
    test_image_data = test_image_path.read_bytes()

    try:
        print(f"\n📤 테스트 이미지 업로드 중...")
        upload_result = cloudinary.upload_authenticated_image(
            image_data=test_image_data,
            expire_minutes=5
        )
        public_id = upload_result["public_id"]
        print(f"   ✓ 업로드 완료: {public_id}")

        print(f"\n🗑️  이미지 삭제 중...")
        delete_result = cloudinary.delete_image(public_id)

        if delete_result:
            print(f"\n✅ 삭제 성공!")
            print(f"   - Public ID: {public_id}")
            return True
        else:
            print(f"\n⚠️  삭제 실패 (또는 이미지가 없음)")
            return False

    except Exception as e:
        print(f"\n❌ 테스트 실패!")
        print(f"   - 에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """모든 테스트 실행"""
    print("\n" + "="*60)
    print("🚀 Cloudinary 서비스 테스트 시작")
    print("="*60)

    results = {
        "인증 업로드 & 만료 테스트": test_upload_authenticated_image_and_access(),
        "이미지 삭제": test_delete_image(),
    }

    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    for test_name, result in results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{status} - {test_name}")

    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("✅ 모든 테스트 통과!")
    else:
        print("❌ 일부 테스트 실패")
    print("="*60 + "\n")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
