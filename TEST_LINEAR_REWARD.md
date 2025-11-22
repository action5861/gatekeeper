# 선형 보상 시스템 테스트 가이드

## 🧪 프론트엔드에서 테스트하는 방법

### 방법 1: 브라우저 개발자 도구 사용 (가장 쉬움)

1. **광고 클릭 (정상 플로우)**
   - 홈페이지에서 광고를 클릭합니다
   - 새 탭이 열리면 그대로 두세요

2. **개발자 도구 열기**
   - `F12` 또는 `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)
   - Console 탭 선택

3. **localStorage 수정**
   - Console에서 다음 코드 실행:
   ```javascript
   // 현재 저장된 데이터 확인
   const data = JSON.parse(localStorage.getItem('ad_return_tracker'));
   console.log('현재 데이터:', data);
   
   // 특정 체류시간으로 테스트하려면 click_time 수정
   // 예: 10초 체류 테스트 (10초 전으로 설정)
   const testDwellSeconds = 10; // 원하는 체류시간(초)
   const modifiedData = {
     trade_id: data.trade_id,
     click_time: Date.now() - (testDwellSeconds * 1000)
   };
   localStorage.setItem('ad_return_tracker', JSON.stringify(modifiedData));
   console.log(`${testDwellSeconds}초 체류로 설정 완료!`);
   ```

4. **탭 전환으로 테스트**
   - 다른 탭으로 이동했다가 다시 돌아오면
   - ReturnTracker가 자동으로 체류시간을 계산하고 API 호출
   - Console에서 결과 확인

### 방법 2: 다양한 체류시간 테스트

**각 케이스별 테스트:**

```javascript
// 테스트 케이스 실행 함수
function testDwellTime(dwellSeconds) {
  const data = JSON.parse(localStorage.getItem('ad_return_tracker'));
  if (!data) {
    console.error('❌ ad_return_tracker 데이터가 없습니다. 먼저 광고를 클릭하세요.');
    return;
  }
  
  const modifiedData = {
    trade_id: data.trade_id,
    click_time: Date.now() - (dwellSeconds * 1000)
  };
  localStorage.setItem('ad_return_tracker', JSON.stringify(modifiedData));
  console.log(`✅ ${dwellSeconds}초 체류시간으로 설정 완료!`);
  console.log('다른 탭으로 이동했다가 돌아오면 자동으로 평가됩니다.');
}

// 테스트 케이스 실행
// testDwellTime(2);    // FAILED (0%)
// testDwellTime(3.5);  // PARTIAL (약 27%)
// testDwellTime(5);    // PARTIAL (약 34%)
// testDwellTime(10);   // PARTIAL (약 56%)
// testDwellTime(15);   // PARTIAL (약 78%)
// testDwellTime(20);   // PASSED (100%)
// testDwellTime(25);   // PASSED (100%)
```

### 방법 3: 수동 API 호출로 직접 테스트

```javascript
// Console에서 직접 API 호출
async function testVerifyReturn(tradeId, dwellSeconds) {
  const token = localStorage.getItem('token'); // 또는 실제 인증 토큰
  const response = await fetch('/api/verify-return', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}` // 실제 인증 방식에 맞게 수정
    },
    body: JSON.stringify({
      trade_id: tradeId,
      dwell_time: dwellSeconds
    })
  });
  
  const result = await response.json();
  console.log('결과:', result);
  return result;
}

// 사용 예시
// testVerifyReturn('your_trade_id', 12.5);
```

## 📊 예상 결과

| 체류시간 | 판정 | 보상비율 | 200원 기준 |
|---------|------|----------|-----------|
| **2초** | FAILED | **0%** | 0원 |
| **3.5초** | PARTIAL | **27.9%** | 약 56원 |
| **5초** | PARTIAL | **33.8%** | 약 68원 |
| **10초** | PARTIAL | **55.9%** | 약 112원 |
| **15초** | PARTIAL | **77.9%** | 약 156원 |
| **20초** | PASSED | **100%** | 200원 |
| **25초** | PASSED | **100%** | 200원 |

## 🔍 확인 포인트

1. **Console 로그 확인**
   - `🔙 [Return Tracker] User returned!`
   - `Dwell Time: XX.XXs`
   - `✅ [Return Tracker] 2nd evaluation complete:`

2. **서버 로그 확인** (백엔드 실행 중)
   - Verification Service 로그에서 체류시간 확인
   - Settlement Service 로그에서 보상비율 계산 확인

3. **브라우저 Network 탭**
   - `/api/verify-return` API 호출 확인
   - Request Body에 `dwell_time` 확인
   - Response에 `decision`, `dwell_time` 확인

## ⚠️ 주의사항

- `localStorage` 수정 후 반드시 탭 전환해야 ReturnTracker가 작동합니다
- 실제 광고 클릭 후에만 `trade_id`가 생성됩니다
- 백엔드 서비스가 실행 중이어야 API 호출이 성공합니다

