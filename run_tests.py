#!/usr/bin/env python3
"""
Test runner for the upgraded MCP Document Generator.

This script runs all tests for the hybrid prompt-based workflow,
including unit tests, integration tests, and mock-based tests.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and report results."""
    print(f"\n🧪 {description}")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print("STDERR:", result.stderr)
            if result.stdout:
                print("STDOUT:", result.stdout)
            return False
            
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False
    
    return True


def main():
    """Run all test suites."""
    print("🚀 Running MCP Document Generator Tests (Hybrid Workflow)")
    print("=" * 60)
    
    all_passed = True
    
    # Test categories to run
    test_suites = [
        {
            "command": "python -m pytest tests/test_basic_functionality.py -v",
            "description": "Basic Functionality Tests (Updated for Hybrid)"
        },
        {
            "command": "python -m pytest tests/test_prompt_generation.py -v",
            "description": "Prompt Generation Tests"
        },
        {
            "command": "python -m pytest tests/test_ai_content_handling.py -v",
            "description": "AI Content Handling Tests"
        },
        {
            "command": "python -m pytest tests/test_hybrid_integration.py -v",
            "description": "Hybrid Integration Tests"
        },
        {
            "command": "python -m pytest tests/test_mocked_hybrid_workflow.py -v",
            "description": "Mocked Hybrid Workflow Tests"
        },
        {
            "command": "python -m pytest tests/test_security.py -v",
            "description": "Security Tests (Existing)"
        }
    ]
    
    # Run each test suite
    for suite in test_suites:
        success = run_command(suite["command"], suite["description"])
        if not success:
            all_passed = False
    
    # Run coverage report
    print(f"\n📊 Running Coverage Analysis")
    print("=" * 60)
    coverage_success = run_command(
        "python -m pytest --cov=document_generator_mcp --cov-report=term-missing tests/",
        "Coverage Analysis"
    )
    
    # Summary
    print(f"\n📋 Test Summary")
    print("=" * 60)
    
    if all_passed:
        print("🎉 All test suites passed!")
        print("\n✅ The upgraded MCP Document Generator is working correctly.")
        print("\n💡 Key Features Tested:")
        print("   • Prompt generation for PRD, SPEC, and DESIGN")
        print("   • AI content saving and validation")
        print("   • Hybrid workflow integration")
        print("   • Error handling and edge cases")
        print("   • Security and validation")
        
        print("\n🔧 Next Steps:")
        print("   1. Test with actual Claude Desktop MCP client")
        print("   2. Verify prompt quality with real AI responses")
        print("   3. Test with various reference resource types")
        print("   4. Performance testing with large projects")
        
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        print("\n🔍 Debugging Tips:")
        print("   • Check import statements for new models")
        print("   • Verify template configurations")
        print("   • Ensure all dependencies are installed")
        print("   • Run individual test files to isolate issues")
    
    # Return appropriate exit code
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
