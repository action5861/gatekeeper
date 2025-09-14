// src/hooks/useDebounce.ts
import { useEffect, useState } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);

    useEffect(() => {
        // delay 이후에 value를 업데이트하는 타이머 설정
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);

        // cleanup 함수: 이전 타이머를 제거하여 마지막 타이머만 실행되도록 함
        return () => {
            clearTimeout(handler);
        };
    }, [value, delay]); // value나 delay가 변경될 때만 재실행

    return debouncedValue;
}
