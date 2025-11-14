#!/usr/bin/env python3
"""
Standalone Test Runner for UI-TARS
Tests services without Docker
"""
import sys
import time
import subprocess
import requests
import json
from pathlib import Path

# Add color support
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

# Test 1: Import Tests
def test_imports():
    print_header("Test 1: Python Package Imports")

    tests = [
        ("fastapi", "FastAPI framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("redis", "Redis client"),
        ("httpx", "HTTP client"),
    ]

    passed = 0
    failed = 0

    for package, description in tests:
        try:
            __import__(package)
            print_success(f"{package:20} - {description}")
            passed += 1
        except ImportError:
            print_error(f"{package:20} - {description} (NOT INSTALLED)")
            failed += 1

    print(f"\n{Colors.BOLD}Result: {passed}/{len(tests)} packages available{Colors.ENDC}")
    return failed == 0

# Test 2: UI-TARS Library Test
def test_ui_tars_library():
    print_header("Test 2: UI-TARS Library Functionality")

    try:
        from ui_tars.action_parser import (
            parse_action_to_structure_output,
            parsing_response_to_pyautogui_code
        )
        print_success("UI-TARS library imported successfully")

        # Test parsing
        test_text = "Thought: Click the button\\nAction: click(start_box='(960,540)')"
        result = parse_action_to_structure_output(
            text=test_text,
            factor=1000,
            origin_resized_height=1080,
            origin_resized_width=1920,
            model_type="qwen25vl"
        )

        if result and len(result) > 0:
            print_success(f"Parsed {len(result)} actions")
            print_info(f"Action type: {result[0].get('action_type', 'N/A')}")

            # Test code generation
            code = parsing_response_to_pyautogui_code(
                responses=result,
                image_height=1080,
                image_width=1920
            )

            if code and "pyautogui" in code:
                print_success("PyAutoGUI code generated successfully")
                print_info(f"Generated code:\n{Colors.OKCYAN}{code[:200]}...{Colors.ENDC}")
                return True
            else:
                print_error("Failed to generate PyAutoGUI code")
                return False
        else:
            print_error("Failed to parse action")
            return False

    except ImportError as e:
        print_error(f"UI-TARS library not installed: {e}")
        print_warning("Install with: pip install ui-tars")
        return False
    except Exception as e:
        print_error(f"UI-TARS test failed: {e}")
        return False

# Test 3: Mock Model Service
def test_mock_model_service():
    print_header("Test 3: Mock Model Service")

    # Check if service file exists
    service_path = Path(__file__).parent / "model-service" / "mock_model_service.py"
    if not service_path.exists():
        print_error(f"Mock service not found: {service_path}")
        return False

    print_success(f"Mock service file found: {service_path}")

    # Try to import and validate
    try:
        sys.path.insert(0, str(service_path.parent))
        import mock_model_service
        print_success("Mock service imports successfully")

        # Check if FastAPI app exists
        if hasattr(mock_model_service, 'app'):
            print_success("FastAPI app found")
            print_info(f"App title: {mock_model_service.app.title}")
            return True
        else:
            print_error("FastAPI app not found in module")
            return False

    except Exception as e:
        print_error(f"Failed to import mock service: {e}")
        return False

# Test 4: Service Endpoints (if running)
def test_service_endpoints():
    print_header("Test 4: Service Endpoint Tests (Optional)")

    services = [
        ("Mock Model", "http://localhost:8081/health", 8081),
        ("Parser Service", "http://localhost:8082/health", 8082),
        ("API Gateway", "http://localhost:8080/health", 8080),
    ]

    print_info("Checking if services are running...")
    print_warning("(Services need to be started separately)")

    running = 0
    for name, url, port in services:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print_success(f"{name:20} - Running on port {port}")
                print_info(f"Response: {response.json()}")
                running += 1
            else:
                print_warning(f"{name:20} - Responded with status {response.status_code}")
        except requests.exceptions.ConnectionError:
            print_warning(f"{name:20} - Not running (port {port})")
        except Exception as e:
            print_error(f"{name:20} - Error: {e}")

    if running > 0:
        print_success(f"{running}/{len(services)} services are running")
    else:
        print_warning("No services running. Start them with:")
        print_info("  cd deployment/model-service && python mock_model_service.py")

    return True  # Don't fail if services aren't running

# Test 5: Docker Compose Files
def test_docker_compose_files():
    print_header("Test 5: Docker Compose Configuration")

    files = [
        ("docker-compose.yml", "Production config"),
        ("docker-compose.test.yml", "Test config (mock model)"),
    ]

    passed = 0
    for filename, description in files:
        filepath = Path(__file__).parent / filename
        if filepath.exists():
            print_success(f"{filename:30} - {description}")

            # Check file size
            size = filepath.stat().st_size
            print_info(f"  File size: {size} bytes")
            passed += 1
        else:
            print_error(f"{filename:30} - Not found")

    return passed == len(files)

# Test 6: Dockerfile Validation
def test_dockerfiles():
    print_header("Test 6: Dockerfile Validation")

    dockerfiles = [
        ("api-gateway/Dockerfile", "API Gateway"),
        ("parser-service/Dockerfile", "Parser Service"),
        ("executor-service/Dockerfile", "Executor Service"),
        ("model-service/Dockerfile.mock", "Mock Model Service"),
    ]

    passed = 0
    for dockerfile, description in dockerfiles:
        filepath = Path(__file__).parent / dockerfile
        if filepath.exists():
            print_success(f"{description:25} - {dockerfile}")
            passed += 1
        else:
            print_error(f"{description:25} - {dockerfile} not found")

    return passed == len(dockerfiles)

# Test 7: Integration Test
def test_integration():
    print_header("Test 7: Integration Test (End-to-End)")

    print_info("Simulating full workflow...")

    # Step 1: Mock model response
    print_info("\n[Step 1] Mock model generates action")
    mock_response = "Thought: I see a login button\\nAction: click(start_box='(960,540)')"
    print_success(f"Generated: {mock_response[:50]}...")

    # Step 2: Parse action
    try:
        from ui_tars.action_parser import (
            parse_action_to_structure_output,
            parsing_response_to_pyautogui_code
        )

        print_info("\n[Step 2] Parser processes action")
        result = parse_action_to_structure_output(
            text=mock_response,
            factor=1000,
            origin_resized_height=1080,
            origin_resized_width=1920,
            model_type="qwen25vl"
        )
        print_success(f"Parsed action: {result[0].get('action_type', 'unknown')}")

        # Step 3: Generate code
        print_info("\n[Step 3] Generate PyAutoGUI code")
        code = parsing_response_to_pyautogui_code(
            responses=result,
            image_height=1080,
            image_width=1920
        )
        print_success("Generated executable code")
        print_info(f"Code:\n{Colors.OKCYAN}{code}{Colors.ENDC}")

        # Step 4: Validate code
        print_info("\n[Step 4] Validate generated code")
        if "pyautogui" in code and "click" in code:
            print_success("Code validation passed")
            return True
        else:
            print_error("Code validation failed")
            return False

    except Exception as e:
        print_error(f"Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# Main Test Runner
def main():
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔═══════════════════════════════════════════════════════╗")
    print("║         UI-TARS Standalone Test Suite                 ║")
    print("║         Testing without Docker                        ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")

    tests = [
        ("Package Imports", test_imports),
        ("UI-TARS Library", test_ui_tars_library),
        ("Mock Model Service", test_mock_model_service),
        ("Service Endpoints", test_service_endpoints),
        ("Docker Compose Files", test_docker_compose_files),
        ("Dockerfiles", test_dockerfiles),
        ("Integration Test", test_integration),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Test '{name}' crashed: {e}")
            results.append((name, False))

        time.sleep(0.5)

    # Final Summary
    print_header("Test Summary")

    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed

    for name, result in results:
        if result:
            print_success(f"{name:30} PASSED")
        else:
            print_error(f"{name:30} FAILED")

    print(f"\n{Colors.BOLD}Total: {passed}/{len(results)} tests passed{Colors.ENDC}")

    if failed == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 All tests passed!{Colors.ENDC}")
        return 0
    else:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  {failed} test(s) failed{Colors.ENDC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
