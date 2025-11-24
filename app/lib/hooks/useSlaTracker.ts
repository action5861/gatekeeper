import { useCallback, useEffect, useRef, useState } from 'react';

interface SlaMetrics {
    v_atf: number;                     // Above The Fold 가시성 (부정 방지용)
    clicked: boolean;                  // 광고 클릭 여부 (핵심!)
    t_dwell_on_ad_site: number;        // 광고주 사이트 체류 시간 (가장 중요!)
}

interface UseSlaTrackerOptions<T extends HTMLElement = HTMLElement> {
    tradeId: string | null;
    elementRef: React.RefObject<T | null>;
    onComplete?: (metrics: SlaMetrics) => void;
    onAdClick?: () => void; // 광고 클릭 콜백 (외부에서 호출)
}

// 외부에서 호출할 수 있는 클릭 핸들러 타입
export interface SlaTrackerHandle {
    notifyAdClick: () => void;
}

export function useSlaTracker<T extends HTMLElement = HTMLElement>({ tradeId, elementRef, onComplete, onAdClick }: UseSlaTrackerOptions<T>) {
    const [isTracking, setIsTracking] = useState(false);

    // onComplete를 ref로 저장하여 의존성 배열 문제 해결
    const onCompleteRef = useRef(onComplete);

    // onComplete가 변경되면 ref 업데이트 (의존성 배열에는 포함하지 않음)
    useEffect(() => {
        onCompleteRef.current = onComplete;
    }, [onComplete]);

    const metricsRef = useRef<{
        wasAboveTheFold: boolean;      // 화면에 보였는지 (부정 방지)
        clicked: boolean;              // 광고 클릭 여부
    }>({
        wasAboveTheFold: false,
        clicked: false,
    });

    // 이미 처리된 tradeId 추적 (중복 실행 방지)
    const processedTradeIdRef = useRef<string | null>(null);

    // 광고 클릭 핸들러를 외부에 노출
    const notifyAdClick = useCallback(() => {
        metricsRef.current.clicked = true;
        console.log(`🖱️ Ad clicked!`);

        if (onAdClick) {
            onAdClick();
        }
    }, [onAdClick]);

    useEffect(() => {
        console.log(`🔍 [SLA Tracker] useEffect triggered. tradeId: ${tradeId}, elementRef.current: ${elementRef.current ? 'exists' : 'null'}`);

        if (!tradeId) {
            console.log(`⚠️ [SLA Tracker] No tradeId, skipping tracking`);
            return;
        }

        if (!elementRef.current) {
            console.log(`⚠️ [SLA Tracker] No element ref, skipping tracking`);
            return;
        }

        // 이미 처리된 tradeId면 스킵
        if (processedTradeIdRef.current === tradeId) {
            console.log(`⚠️ [SLA Tracker] Trade ${tradeId} already being tracked, skipping duplicate`);
            return;
        }

        processedTradeIdRef.current = tradeId;

        console.log(`📊 [SLA Tracker] SLA Tracking started for trade_id: ${tradeId}`);
        setIsTracking(true);

        const element = elementRef.current as HTMLElement;
        const metrics = metricsRef.current;

        // 전송 플래그 (중복 방지)
        let hasSent = false;

        // 🎯 단순화된 SLA 전송 함수
        const sendSlaMetrics = () => {
            if (hasSent) {
                console.log(`⚠️ [SLA Tracker] Already sent for trade_id: ${tradeId}, skipping duplicate`);
                return;
            }
            hasSent = true;

            // 단순한 SLA 지표 계산
            const slaMetrics: SlaMetrics = {
                v_atf: metrics.wasAboveTheFold ? 1.0 : 0.0,    // 부정 방지용
                clicked: metrics.clicked,                      // 핵심!
                t_dwell_on_ad_site: 0,                         // redirect에서 별도로 측정
            };

            console.log(`📊 SLA Metrics calculated for trade_id ${tradeId}:`, slaMetrics);
            console.log(`   🖱️ Clicked: ${slaMetrics.clicked}, v_atf: ${slaMetrics.v_atf}`);

            // 콜백 호출 (ref를 통해 최신 함수 호출)
            if (onCompleteRef.current) {
                onCompleteRef.current(slaMetrics);
            }
        };

        // Above The Fold 체크 (초기 위치가 뷰포트 안에 있는지)
        const initialRect = element.getBoundingClientRect();
        metrics.wasAboveTheFold = initialRect.top < window.innerHeight && initialRect.top >= 0;

        console.log(`👁️ Above The Fold: ${metrics.wasAboveTheFold}`);

        // 일정 시간(3초) 후 자동 전송 - 빠르게 검증
        const autoSendTimer = setTimeout(() => {
            console.log(`⏰ Auto-sending SLA metrics after 3s for trade_id: ${tradeId}`);
            sendSlaMetrics();
            setIsTracking(false);
        }, 3000); // 3초 (체류 시간은 redirect에서 측정하므로 빠르게)

        // Cleanup 함수
        return () => {
            console.log(`📊 SLA Tracking stopped for trade_id: ${tradeId}`);
            clearTimeout(autoSendTimer);
            setIsTracking(false);

            // tradeId가 변경될 때 processedTradeIdRef 초기화
            processedTradeIdRef.current = null;
        };
    }, [tradeId]); // onComplete와 elementRef 제거 - ref로 관리

    return { isTracking, notifyAdClick };
}

