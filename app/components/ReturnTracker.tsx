// 사용자 복귀 감지 및 2차 SLA 평가 컴포넌트

'use client'

import { authenticatedFetch } from '@/lib/auth';
import { useEffect } from 'react';

export default function ReturnTracker() {
    useEffect(() => {
        const handleVisibilityChange = async () => {
            // 탭이 다시 활성화되었을 때만 실행
            if (document.visibilityState === 'visible') {
                console.log('👁️ [Return Tracker] Tab became visible');

                // localStorage에서 복귀 추적 데이터 확인
                const trackerDataStr = localStorage.getItem('ad_return_tracker');

                if (!trackerDataStr) {
                    // 추적할 데이터가 없음
                    return;
                }

                try {
                    const trackerData = JSON.parse(trackerDataStr);
                    const { trade_id, click_time } = trackerData;

                    if (!trade_id || !click_time) {
                        console.warn('⚠️ [Return Tracker] Invalid tracker data');
                        localStorage.removeItem('ad_return_tracker');
                        return;
                    }

                    // 체류 시간 계산 (초 단위)
                    const now = Date.now();
                    const dwell_time = (now - click_time) / 1000;

                    console.log(`🔙 [Return Tracker] User returned!`);
                    console.log(`   Trade ID: ${trade_id}`);
                    console.log(`   Dwell Time: ${dwell_time.toFixed(2)}s`);

                    // localStorage 데이터 즉시 삭제 (중복 방지)
                    localStorage.removeItem('ad_return_tracker');

                    // 2차 평가 API 호출
                    const response = await authenticatedFetch('/api/verify-return', {
                        method: 'POST',
                        body: JSON.stringify({
                            trade_id,
                            dwell_time
                        }),
                    });

                    const result = await response.json();
                    console.log(`✅ [Return Tracker] 2nd evaluation complete:`, result);

                    // 판정 결과에 따라 알림 표시
                    if (result.decision === 'PASSED') {
                        showSuccessNotification('🎉 전액 정산 완료! 광고주 사이트 체류 시간 충족');
                    } else if (result.decision === 'PARTIAL') {
                        const rewardRatio = result.dwell_time ? 
                            `${Math.round((0.25 + 0.75 * (result.dwell_time - 5) / (20 - 5)) * 100)}%` : '';
                        showInfoNotification(`⚠️ 부분 정산 완료 (${rewardRatio}). 20초 이상 체류하면 전액 정산됩니다.`);
                    } else if (result.decision === 'FAILED') {
                        showInfoNotification('❌ 체류 시간이 너무 짧습니다. 5초 이상 체류해야 보상을 받을 수 있습니다.');
                    }

                    // 대시보드 갱신 이벤트
                    window.dispatchEvent(new CustomEvent('stats-updated'));
                    window.dispatchEvent(new CustomEvent('reward-updated'));

                } catch (error) {
                    console.error('❌ [Return Tracker] Error processing return:', error);
                    // 에러가 나도 데이터는 삭제
                    localStorage.removeItem('ad_return_tracker');
                }
            }
        };

        // visibilitychange 이벤트 리스너 등록
        document.addEventListener('visibilitychange', handleVisibilityChange);

        // cleanup: 컴포넌트 언마운트 시 리스너 제거
        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
        };
    }, []);

    // 이 컴포넌트는 UI를 렌더링하지 않음 (로직만 실행)
    return null;
}

// 성공 알림 표시 함수
function showSuccessNotification(message: string) {
    // 간단한 알림 - 실제로는 toast 라이브러리 사용 가능
    const event = new CustomEvent('show-notification', {
        detail: { type: 'success', message }
    });
    window.dispatchEvent(event);
}

// 정보 알림 표시 함수
function showInfoNotification(message: string) {
    const event = new CustomEvent('show-notification', {
        detail: { type: 'info', message }
    });
    window.dispatchEvent(event);
}












