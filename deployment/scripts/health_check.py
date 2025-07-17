#!/usr/bin/env python3
"""
Health check script for Multi-Agent System API.
Can be used for monitoring and deployment health checks.
"""
import sys
import time
import requests
import json
from typing import Dict, Any


def check_api_health(base_url: str = "http://localhost:8000", timeout: int = 30) -> Dict[str, Any]:
    """Check API health and return status information."""
    try:
        # Health check endpoint
        response = requests.get(f"{base_url}/health", timeout=timeout)
        
        if response.status_code == 200:
            health_data = response.json()
            return {
                "status": "healthy",
                "api_status": health_data.get("status", "unknown"),
                "components": health_data.get("components", {}),
                "response_time": response.elapsed.total_seconds()
            }
        else:
            return {
                "status": "unhealthy",
                "error": f"HTTP {response.status_code}",
                "response_time": response.elapsed.total_seconds()
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "unhealthy",
            "error": "Request timeout"
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "unhealthy",
            "error": "Connection failed"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def check_api_functionality(base_url: str = "http://localhost:8000", timeout: int = 60) -> Dict[str, Any]:
    """Test basic API functionality."""
    try:
        # Test process endpoint with simple input
        test_payload = {
            "input": "What is 2 + 2?",
            "use_parallel": False,
            "confidence_threshold": 0.3
        }
        
        response = requests.post(
            f"{base_url}/process",
            json=test_payload,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "status": "functional",
                "processing_mode": result.get("processing_mode"),
                "primary_intent": result.get("primary_intent"),
                "success": result.get("success", False),
                "response_time": response.elapsed.total_seconds()
            }
        else:
            return {
                "status": "non_functional",
                "error": f"HTTP {response.status_code}",
                "response_time": response.elapsed.total_seconds()
            }
            
    except Exception as e:
        return {
            "status": "non_functional",
            "error": str(e)
        }


def main():
    """Main health check function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Agent System Health Check")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--functional", action="store_true", help="Run functionality test")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    print(f"🔍 Checking Multi-Agent System API at {args.url}")
    
    # Basic health check
    health_result = check_api_health(args.url, args.timeout)
    
    results = {
        "timestamp": time.time(),
        "url": args.url,
        "health_check": health_result
    }
    
    # Functionality test if requested
    if args.functional:
        if args.verbose:
            print("🧪 Running functionality test...")
        func_result = check_api_functionality(args.url, args.timeout * 2)
        results["functionality_test"] = func_result
    
    # Output results
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        # Human-readable output
        print(f"\n📊 Health Check Results:")
        print(f"Status: {health_result['status'].upper()}")
        
        if health_result['status'] == 'healthy':
            print("✅ API is healthy")
            if 'response_time' in health_result:
                print(f"⏱️  Response time: {health_result['response_time']:.3f}s")
            
            if 'components' in health_result:
                print("🔧 Components:")
                for component, status in health_result['components'].items():
                    print(f"   {component}: {status}")
        else:
            print(f"❌ API is unhealthy: {health_result.get('error', 'Unknown error')}")
        
        if args.functional and 'functionality_test' in results:
            func_result = results['functionality_test']
            print(f"\n🧪 Functionality Test:")
            print(f"Status: {func_result['status'].upper()}")
            
            if func_result['status'] == 'functional':
                print("✅ API is functional")
                print(f"⏱️  Processing time: {func_result['response_time']:.3f}s")
                print(f"🎯 Primary intent: {func_result.get('primary_intent', 'unknown')}")
                print(f"🔄 Processing mode: {func_result.get('processing_mode', 'unknown')}")
            else:
                print(f"❌ API functionality failed: {func_result.get('error', 'Unknown error')}")
    
    # Exit code based on health status
    if health_result['status'] == 'healthy':
        if args.functional:
            func_result = results.get('functionality_test', {})
            if func_result.get('status') == 'functional':
                sys.exit(0)  # Success
            else:
                sys.exit(2)  # Functional test failed
        else:
            sys.exit(0)  # Success
    else:
        sys.exit(1)  # Health check failed


if __name__ == "__main__":
    main()
