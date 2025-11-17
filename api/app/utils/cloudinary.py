"""
Cloudinary 이미지 업로드 유틸리티
"""
import cloudinary
import cloudinary.uploader
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import Dict, Any
from app.core.config import Config

# Cloudinary 설정 (모듈 로드 시 한 번만 초기화)
cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET,
    secure=True
)


def upload_authenticated_image(
    image_data: bytes,
    expire_minutes: int = 5
) -> Dict[str, Any]:
    """
    이미지를 Cloudinary에 authenticated로 업로드합니다.
    폴더 구조: CLOUDINARY_IMAGE_PATH/{uuid}_{YYYY-MM-DD}

    Args:
        image_data: 이미지 바이트 데이터
        expire_minutes: 접근 허용 기간 (분)

    Returns:
        Dict: {
            "public_id": str,
            "format": str,
            "secure_url": str
        }
    """
    try:
        # 파일명 생성
        file_id = str(uuid4())[:8]
        date_str = datetime.now().strftime("%Y-%m-%d")
        public_id = f"{file_id}_{date_str}"

        # 접근 허용 기간 설정
        now = datetime.now(timezone.utc)
        expire_time = now + timedelta(minutes=expire_minutes)

        # 업로드 옵션 설정
        upload_options = {
            "public_id": public_id,
            "resource_type": "image",
            "type": "authenticated",
            "invalidate": True,
            "use_filename": False,
            "unique_filename": False,
            "sign_url": True,
            "asset_folder": Config.CLOUDINARY_IMAGE_PATH,
            "access_control": [
                {
                    "access_type": "anonymous",
                    "start": now.isoformat(),
                    "end": expire_time.isoformat()
                }
            ],
        }

        # Cloudinary에 업로드
        result = cloudinary.uploader.upload(
            image_data,
            **upload_options
        )

        print(f"✅ 인증 이미지 업로드 완료: {result['public_id']}")

        return {
            "public_id": result["public_id"],
            "format": result["format"],
            "secure_url": result["secure_url"],
        }

    except Exception as e:
        print(f"❌ Cloudinary 인증 업로드 실패: {str(e)}")
        raise RuntimeError(f"Cloudinary 인증 업로드 실패: {str(e)}")


def delete_image(public_id: str) -> bool:
    """
    Cloudinary에서 이미지를 삭제합니다.

    Args:
        public_id: Cloudinary public ID

    Returns:
        bool: 삭제 성공 여부
    """
    try:
        result = cloudinary.uploader.destroy(
            public_id=public_id,
            type="authenticated",
            invalidate=True
        )

        success = result.get("result") == "ok"

        if success:
            print(f"✅ 이미지 삭제 완료: {public_id}")
        else:
            print(f"⚠️  이미지 삭제 실패: {public_id}")
            print(f"   - Cloudinary 응답: {result}")

        return success

    except Exception as e:
        print(f"❌ Cloudinary 삭제 실패: {str(e)}")
        return False
