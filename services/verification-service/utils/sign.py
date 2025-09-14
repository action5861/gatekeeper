import hmac
import os
from hashlib import sha256


def verify_sig(bid_id: str, payout: int, bid_type: str, sig: str) -> bool:
    """
    클릭 URL의 HMAC 서명을 검증합니다.

    Args:
        bid_id (str): 입찰 ID
        payout (int): 지급 금액
        bid_type (str): 입찰 타입 ('PLATFORM' 또는 'ADVERTISER')
        sig (str): 검증할 서명

    Returns:
        bool: 서명이 유효한지 여부
    """
    secret = os.getenv("CLICK_HMAC_SECRET", "dev-click-secret").encode()
    msg = f"{bid_id}.{payout}.{bid_type}".encode()
    expected = hmac.new(secret, msg, sha256).hexdigest()
    return hmac.compare_digest(expected, sig)
