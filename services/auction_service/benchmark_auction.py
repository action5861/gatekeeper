#!/usr/bin/env python3
"""
Auction Service Performance Benchmark Script

This script tests the latency improvements of the auction-service by:
1. Warming up the DB connection pool
2. Measuring single request latency
3. Testing concurrent request handling with bounded concurrency
"""

import asyncio
import time
import os
import sys
from typing import List, Dict, Any, Optional
import httpx
import statistics
from datetime import datetime


# Configuration
BASE_URL = "http://localhost:8002"
ENDPOINT = "/start"
PAYLOAD = {"query": "아이폰 16 케이스", "valueScore": 70}
TARGET_LATENCY_MS = 2000  # Target: < 2000ms

# Authentication token (optional)
# Can be set via environment variable: BENCHMARK_AUTH_TOKEN
# Or pass as command line argument: python benchmark_auction.py <token>
AUTH_TOKEN: Optional[str] = os.getenv("BENCHMARK_AUTH_TOKEN") or (
    sys.argv[1] if len(sys.argv) > 1 else None
)


class BenchmarkResult:
    """Single request benchmark result"""

    def __init__(
        self,
        request_id: int,
        status_code: int,
        latency_ms: float,
        success: bool,
        error: Optional[str] = None,
        bid_count: int = 0,
    ):
        self.request_id = request_id
        self.status_code = status_code
        self.latency_ms = latency_ms
        self.success = success
        self.error = error
        self.bid_count = bid_count

    def __repr__(self) -> str:
        status_emoji = "✅" if self.success else "❌"
        return (
            f"Request #{self.request_id}: {status_emoji} "
            f"Status={self.status_code} | "
            f"Latency={self.latency_ms:.2f}ms | "
            f"Bids={self.bid_count}"
        )


async def send_request(
    client: httpx.AsyncClient, request_id: int, timeout: float = 30.0
) -> BenchmarkResult:
    """
    Send a single request to the auction service and measure latency.

    Args:
        client: httpx async client
        request_id: Unique identifier for this request
        timeout: Request timeout in seconds

    Returns:
        BenchmarkResult with timing and status information
    """
    start_time = time.time()
    try:
        # Prepare headers with optional authentication
        headers: Dict[str, str] = {}
        if AUTH_TOKEN:
            headers["Authorization"] = f"Bearer {AUTH_TOKEN}"

        response = await client.post(
            f"{BASE_URL}{ENDPOINT}",
            json=PAYLOAD,
            headers=headers,
            timeout=timeout,
        )
        latency_ms = (time.time() - start_time) * 1000

        # Validation
        success = response.status_code == 200
        bid_count = 0
        error = None

        if success:
            try:
                data = response.json()
                if "data" in data and "bids" in data["data"]:
                    bids = data["data"]["bids"]
                    if isinstance(bids, list):
                        bid_count = len(bids)
                    else:
                        error = "bids is not a list"
                        success = False
                else:
                    error = "Missing data.bids in response"
                    success = False
            except Exception as e:
                error = f"JSON parsing error: {str(e)}"
                success = False
        else:
            error = f"HTTP {response.status_code}: {response.text[:100]}"

        return BenchmarkResult(
            request_id=request_id,
            status_code=response.status_code,
            latency_ms=latency_ms,
            success=success,
            error=error,
            bid_count=bid_count,
        )

    except httpx.TimeoutException:
        latency_ms = (time.time() - start_time) * 1000
        return BenchmarkResult(
            request_id=request_id,
            status_code=0,
            latency_ms=latency_ms,
            success=False,
            error="Request timeout",
        )
    except httpx.ConnectError:
        latency_ms = (time.time() - start_time) * 1000
        return BenchmarkResult(
            request_id=request_id,
            status_code=0,
            latency_ms=latency_ms,
            success=False,
            error="Connection refused (server may be down)",
        )
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return BenchmarkResult(
            request_id=request_id,
            status_code=0,
            latency_ms=latency_ms,
            success=False,
            error=f"Unexpected error: {str(e)}",
        )


def calculate_percentile(data: List[float], percentile: float) -> float:
    """Calculate percentile value from a list of numbers"""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = (percentile / 100) * (len(sorted_data) - 1)
    lower = int(index)
    upper = lower + 1
    if upper >= len(sorted_data):
        return sorted_data[-1]
    weight = index - lower
    return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight


def print_summary(results: List[BenchmarkResult], phase_name: str) -> None:
    """Print a formatted summary table of benchmark results"""
    print(f"\n{'='*70}")
    print(f"🚀 {phase_name}")
    print(f"{'='*70}")

    if not results:
        print("❌ No results to display")
        return

    # Print individual results
    print(
        f"\n{'Request ID':<12} {'Status':<8} {'Latency (ms)':<15} {'Bids':<8} {'Notes'}"
    )
    print("-" * 70)
    for result in results:
        status_str = f"{result.status_code}" if result.status_code > 0 else "ERROR"
        status_emoji = "✅" if result.success else "❌"
        notes = result.error if result.error else ""
        print(
            f"#{result.request_id:<11} "
            f"{status_emoji} {status_str:<5} "
            f"{result.latency_ms:>12.2f}ms "
            f"{result.bid_count:>7} "
            f"{notes}"
        )

    # Calculate statistics
    successful_results = [r for r in results if r.success]
    if successful_results:
        latencies = [r.latency_ms for r in successful_results]
        avg_latency = statistics.mean(latencies)
        p95_latency = calculate_percentile(latencies, 95)
        p99_latency = calculate_percentile(latencies, 99)
        min_latency = min(latencies)
        max_latency = max(latencies)

        print(f"\n{'='*70}")
        print("📊 Statistics (Successful Requests Only)")
        print(f"{'='*70}")
        print(f"  Total Requests:     {len(results)}")
        print(f"  Successful:        {len(successful_results)} ✅")
        print(f"  Failed:            {len(results) - len(successful_results)} ❌")
        print(f"  Average Latency:   {avg_latency:.2f}ms")
        print(f"  P95 Latency:       {p95_latency:.2f}ms")
        print(f"  P99 Latency:       {p99_latency:.2f}ms")
        print(f"  Min Latency:       {min_latency:.2f}ms")
        print(f"  Max Latency:       {max_latency:.2f}ms")

        # Check target latency
        if avg_latency < TARGET_LATENCY_MS:
            print(
                f"\n  ✅ Average latency ({avg_latency:.2f}ms) meets target (< {TARGET_LATENCY_MS}ms)"
            )
        else:
            print(
                f"\n  ❌ Average latency ({avg_latency:.2f}ms) exceeds target (< {TARGET_LATENCY_MS}ms)"
            )

        if p95_latency < TARGET_LATENCY_MS * 1.5:
            print(f"  ✅ P95 latency ({p95_latency:.2f}ms) is reasonable")
        else:
            print(f"  ⚠️  P95 latency ({p95_latency:.2f}ms) is high")
    else:
        print(f"\n❌ No successful requests to calculate statistics")


async def phase1_warmup(client: httpx.AsyncClient) -> None:
    """Phase 1: Warm-up - Send 1 request to wake up DB connection pool"""
    print("\n" + "=" * 70)
    print("🔥 Phase 1: Warm-up (DB Connection Pool)")
    print("=" * 70)
    print("Sending 1 warm-up request (timing ignored)...")

    result = await send_request(client, request_id=0)
    if result.success:
        print(f"✅ Warm-up successful: {result.latency_ms:.2f}ms")
    else:
        print(f"⚠️  Warm-up failed: {result.error}")
        print("   Continuing anyway...")


async def phase2_single_latency(client: httpx.AsyncClient) -> BenchmarkResult:
    """Phase 2: Single Latency Test - Measure exact execution time"""
    print("\n" + "=" * 70)
    print("⏱️  Phase 2: Single Latency Test")
    print("=" * 70)
    print("Sending 1 request and measuring latency...")

    result = await send_request(client, request_id=1)

    print_summary([result], "Single Latency Test")

    if result.success:
        if result.latency_ms < TARGET_LATENCY_MS:
            print(
                f"\n✅ SUCCESS: Latency ({result.latency_ms:.2f}ms) meets target (< {TARGET_LATENCY_MS}ms)"
            )
        else:
            print(
                f"\n❌ FAIL: Latency ({result.latency_ms:.2f}ms) exceeds target (< {TARGET_LATENCY_MS}ms)"
            )
    else:
        print(f"\n❌ FAIL: Request failed - {result.error}")

    return result


async def phase3_concurrency_stress(client: httpx.AsyncClient) -> List[BenchmarkResult]:
    """Phase 3: Concurrency Stress Test - Send 5 simultaneous requests"""
    print("\n" + "=" * 70)
    print("⚡ Phase 3: Concurrency Stress Test")
    print("=" * 70)
    print("Sending 5 requests simultaneously using asyncio.gather...")
    print("This verifies Semaphore and DB locking logic work correctly.")

    # Create 5 concurrent requests
    tasks = [send_request(client, request_id=i + 1) for i in range(5)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle exceptions
    benchmark_results: List[BenchmarkResult] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            benchmark_results.append(
                BenchmarkResult(
                    request_id=i + 1,
                    status_code=0,
                    latency_ms=0.0,
                    success=False,
                    error=f"Exception: {str(result)}",
                )
            )
        elif isinstance(result, BenchmarkResult):
            benchmark_results.append(result)
        else:
            # Fallback for unexpected types
            benchmark_results.append(
                BenchmarkResult(
                    request_id=i + 1,
                    status_code=0,
                    latency_ms=0.0,
                    success=False,
                    error=f"Unexpected result type: {type(result)}",
                )
            )

    print_summary(benchmark_results, "Concurrency Stress Test")

    # Check if all requests succeeded
    successful = [r for r in benchmark_results if r.success]
    if len(successful) == len(benchmark_results):
        print(
            f"\n✅ SUCCESS: All {len(benchmark_results)} concurrent requests succeeded"
        )
    else:
        print(
            f"\n⚠️  WARNING: {len(benchmark_results) - len(successful)} out of {len(benchmark_results)} requests failed"
        )

    return benchmark_results


async def main() -> None:
    """Main benchmark execution"""
    print("=" * 70)
    print("🚀 Auction Service Performance Benchmark")
    print("=" * 70)
    print(f"Target: {BASE_URL}{ENDPOINT}")
    print(f"Payload: {PAYLOAD}")
    print(f"Target Latency: < {TARGET_LATENCY_MS}ms")
    if AUTH_TOKEN:
        print(f"🔐 Using authentication token: {AUTH_TOKEN[:20]}...")
    else:
        print("⚠️  No authentication token provided")
        print("   Set BENCHMARK_AUTH_TOKEN env var or pass token as argument")
        print("   Example: python benchmark_auction.py <your_jwt_token>")
        print("   Or: export BENCHMARK_AUTH_TOKEN=<your_jwt_token>")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Create httpx async client with reasonable timeout
    async with httpx.AsyncClient() as client:
        try:
            # Phase 1: Warm-up
            await phase1_warmup(client)
            await asyncio.sleep(0.5)  # Brief pause after warm-up

            # Phase 2: Single Latency Test
            single_result = await phase2_single_latency(client)
            await asyncio.sleep(0.5)  # Brief pause between phases

            # Phase 3: Concurrency Stress Test
            concurrency_results = await phase3_concurrency_stress(client)

            # Final Summary
            print("\n" + "=" * 70)
            print("📋 Final Summary")
            print("=" * 70)
            all_results = [single_result] + concurrency_results
            successful_results = [r for r in all_results if r.success]

            if successful_results:
                latencies = [r.latency_ms for r in successful_results]
                avg_latency = statistics.mean(latencies)
                p95_latency = calculate_percentile(latencies, 95)

                print(f"\n  Total Requests:     {len(all_results)}")
                print(f"  Successful:        {len(successful_results)} ✅")
                print(
                    f"  Failed:            {len(all_results) - len(successful_results)} ❌"
                )
                print(f"  Average Latency:   {avg_latency:.2f}ms")
                print(f"  P95 Latency:       {p95_latency:.2f}ms")

                if avg_latency < TARGET_LATENCY_MS and len(successful_results) == len(
                    all_results
                ):
                    print(f"\n  🎉 OVERALL: SUCCESS - All tests passed!")
                else:
                    print(f"\n  ⚠️  OVERALL: Some issues detected")

            print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 70)

        except KeyboardInterrupt:
            print("\n\n⚠️  Benchmark interrupted by user")
        except Exception as e:
            print(f"\n\n❌ Fatal error: {str(e)}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
