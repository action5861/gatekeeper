import hmac
import os
from hashlib import sha256


def sign_click(bid_id: str, payout: int, bid_type: str) -> str:
    """
    클릭 URL에 대한 HMAC 서명을 생성합니다.

    Args:
        bid_id (str): 입찰 ID
        payout (int): 지급 금액
        bid_type (str): 입찰 타입 ('PLATFORM' 또는 'ADVERTISER')

    Returns:
        str: HMAC-SHA256 서명
    """
    secret = os.getenv("CLICK_HMAC_SECRET", "dev-click-secret").encode()
    msg = f"{bid_id}.{payout}.{bid_type}".encode()
    return hmac.new(secret, msg, sha256).hexdigest()
