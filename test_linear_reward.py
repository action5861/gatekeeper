"""
선형 보상 시스템 테스트 스크립트
체류시간에 따른 보상 계산이 정확하게 작동하는지 검증합니다.
"""

def calculate_linear_reward(dwell_time: float, base_reward: float = 200.0) -> dict:
    """
    선형 보상 계산 함수 (settlement-service의 로직과 동일)
    
    Args:
        dwell_time: 체류시간 (초)
        base_reward: 기본 보상금액 (원)
    
    Returns:
        dict: 판정, 보상비율, 보상금액 등
    """
    # 판정 로직 (verification-service와 동일)
    if dwell_time >= 20.0:
        decision = "PASSED"
        ratio = 1.0
    elif dwell_time > 3.0:
        decision = "PARTIAL"
        # 선형 보상 계산: 3초(25%) ~ 20초(100%)
        ratio = 0.25 + 0.75 * (dwell_time - 3.0) / (20.0 - 3.0)
        ratio = max(0.0, min(1.0, ratio))  # 0~1로 클램프
    else:
        decision = "FAILED"
        ratio = 0.0
    
    payable_amount = base_reward * ratio
    
    return {
        "dwell_time": dwell_time,
        "decision": decision,
        "ratio": ratio,
        "ratio_percent": ratio * 100,
        "base_reward": base_reward,
        "payable_amount": payable_amount,
    }


def test_linear_reward_system():
    """선형 보상 시스템 전체 테스트"""
    print("=" * 60)
    print("[TEST] Linear Reward System Test Start")
    print("=" * 60)
    
    # 테스트 케이스 정의
    test_cases = [
        {"dwell": 0.0, "expected_decision": "FAILED", "expected_ratio": 0.0, "desc": "0초 - 보상 없음"},
        {"dwell": 2.0, "expected_decision": "FAILED", "expected_ratio": 0.0, "desc": "2초 - 보상 없음"},
        {"dwell": 3.0, "expected_decision": "FAILED", "expected_ratio": 0.0, "desc": "3초 - 보상 없음 (경계값)"},
        {"dwell": 3.5, "expected_decision": "PARTIAL", "expected_ratio": 0.272, "desc": "3.5초 - 부분보상 시작"},
        {"dwell": 5.0, "expected_decision": "PARTIAL", "expected_ratio": 0.338, "desc": "5초 - 부분보상"},
        {"dwell": 10.0, "expected_decision": "PARTIAL", "expected_ratio": 0.559, "desc": "10초 - 부분보상"},
        {"dwell": 15.0, "expected_decision": "PARTIAL", "expected_ratio": 0.779, "desc": "15초 - 부분보상"},
        {"dwell": 20.0, "expected_decision": "PASSED", "expected_ratio": 1.0, "desc": "20초 - 전액보상 (경계값)"},
        {"dwell": 25.0, "expected_decision": "PASSED", "expected_ratio": 1.0, "desc": "25초 - 전액보상"},
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    print(f"\n[TEST] Test Cases: {total_tests}\n")
    
    for i, test_case in enumerate(test_cases, 1):
        dwell = test_case["dwell"]
        expected_decision = test_case["expected_decision"]
        expected_ratio = test_case["expected_ratio"]
        desc = test_case["desc"]
        
        result = calculate_linear_reward(dwell)
        
        # 판정 체크
        decision_match = result["decision"] == expected_decision
        
        # 비율 체크 (소수점 3자리까지 비교)
        ratio_match = abs(result["ratio"] - expected_ratio) < 0.001
        
        test_passed = decision_match and ratio_match
        
        if test_passed:
            passed_tests += 1
            status = "[PASS]"
        else:
            status = "[FAIL]"
        
        print(f"{status} Test {i}: {desc}")
        print(f"   Dwell Time: {dwell:.1f}s")
        print(f"   Expected Decision: {expected_decision}, Actual: {result['decision']} {'[OK]' if decision_match else '[FAIL]'}")
        print(f"   Expected Ratio: {expected_ratio:.3f} ({expected_ratio*100:.1f}%), Actual: {result['ratio']:.3f} ({result['ratio_percent']:.1f}%) {'[OK]' if ratio_match else '[FAIL]'}")
        print(f"   Reward Amount: {result['payable_amount']:.2f} won")
        print()
    
    # 결과 요약
    print("=" * 60)
    print(f"[RESULT] Tests Passed: {passed_tests}/{total_tests}")
    print("=" * 60)
    
    if passed_tests == total_tests:
        print("[SUCCESS] All tests passed! Linear reward system is working correctly.")
        return True
    else:
        print(f"[WARNING] {total_tests - passed_tests} test(s) failed.")
        return False


def test_edge_cases():
    """경계값 및 특수 케이스 테스트"""
    print("\n" + "=" * 60)
    print("[TEST] Edge Cases")
    print("=" * 60)
    
    edge_cases = [
        {"dwell": 3.0001, "desc": "3초 초과 (최소값)"},
        {"dwell": 19.9999, "desc": "20초 미만 (최대값)"},
        {"dwell": -5.0, "desc": "음수 체류시간"},
        {"dwell": 1000.0, "desc": "매우 긴 체류시간"},
    ]
    
    for case in edge_cases:
        result = calculate_linear_reward(case["dwell"])
        print(f"\n{case['desc']}: {case['dwell']}초")
        print(f"  판정: {result['decision']}")
        print(f"  보상비율: {result['ratio_percent']:.2f}%")
        print(f"  보상금액: {result['payable_amount']:.2f}원")


def test_formula_accuracy():
    """선형 보상 공식의 정확성 검증"""
    print("\n" + "=" * 60)
    print("[TEST] Formula Accuracy Verification")
    print("=" * 60)
    
    # 주요 구간별 계산
    test_points = [
        (3.0, 0.0),   # 3초 = 0% (FAILED)
        (5.0, 0.338), # 5초 = 33.8%
        (10.0, 0.559), # 10초 = 55.9%
        (15.0, 0.779), # 15초 = 77.9%
        (20.0, 1.0),  # 20초 = 100%
    ]
    
    print("\nFormula: ratio = 0.25 + 0.75 * (dwell - 3) / (20 - 3)\n")
    
    for dwell, expected_ratio in test_points:
        result = calculate_linear_reward(dwell)
        calculated = 0.25 + 0.75 * (dwell - 3.0) / (20.0 - 3.0)
        
        if dwell <= 3.0:
            calculated = 0.0
        elif dwell >= 20.0:
            calculated = 1.0
        
        match = abs(result["ratio"] - calculated) < 0.0001
        
        print(f"Dwell Time: {dwell:.1f}s")
        print(f"  Formula: {calculated:.6f}")
        print(f"  Function: {result['ratio']:.6f}")
        print(f"  Match: {'[OK]' if match else '[FAIL]'}")
        print()


if __name__ == "__main__":
    import sys
    import io
    # Windows 인코딩 문제 해결
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("\n[TEST] Linear Reward System Test\n")
    
    # 기본 테스트
    basic_test_passed = test_linear_reward_system()
    
    # 경계값 테스트
    test_edge_cases()
    
    # 공식 정확성 검증
    test_formula_accuracy()
    
    # 최종 결과
    print("\n" + "=" * 60)
    if basic_test_passed:
        print("[SUCCESS] All tests passed!")
        print("Linear reward system is working correctly.")
    else:
        print("[FAIL] Some tests failed")
        print("Please check the code again.")
    print("=" * 60)

