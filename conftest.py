# 테스트 수집 시 프로젝트 루트를 sys.path 앞에 추가하여
# 'services.auction_service...' 임포트가 항상 동작하도록 한다.
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent  # 프로젝트 루트
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
