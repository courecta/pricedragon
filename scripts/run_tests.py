#!/usr/bin/env python3
"""
PriceDragon Test Runner
======================

Comprehensive test execution script for the PriceDragon platform.
Provides easy access to all testing functionality with detailed reporting.

Usage:
    python scripts/run_tests.py [options]
    
Examples:
    python scripts/run_tests.py --quick          # Quick health check
    python scripts/run_tests.py --full           # Full test suite
    python scripts/run_tests.py --setup          # Setup tests only
    python scripts/run_tests.py --scraper        # Scraper tests only
    python scripts/run_tests.py --etl            # ETL tests only
    python scripts/run_tests.py --performance    # Performance testing
"""

import argparse
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Color codes for console output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title: str, char: str = "=") -> None:
    """Print formatted header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{title}{Colors.END}")
    print(f"{Colors.CYAN}{char * len(title)}{Colors.END}")

def print_success(message: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_warning(message: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def run_command(command: List[str], description: str) -> Tuple[bool, str]:
    """
    Run a command and return success status and output.
    
    Args:
        command: Command to run as list of strings
        description: Description of what the command does
        
    Returns:
        Tuple of (success, output)
    """
    print(f"\n{Colors.YELLOW}🔄 {description}...{Colors.END}")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            cwd=Path(__file__).parent.parent
        )
        end_time = time.time()
        
        duration = end_time - start_time
        
        if result.returncode == 0:
            print_success(f"{description} completed in {duration:.1f}s")
            return True, result.stdout
        else:
            print_error(f"{description} failed in {duration:.1f}s")
            if result.stderr:
                print(f"{Colors.RED}{result.stderr}{Colors.END}")
            return False, result.stderr
            
    except Exception as e:
        print_error(f"{description} failed with exception: {str(e)}")
        return False, str(e)

def run_quick_tests() -> Dict[str, bool]:
    """Run quick health check tests."""
    print_header("🚀 Quick Health Check", "=")
    results = {}
    
    # Setup health check
    success, _ = run_command(
        ["python", "scripts/test_setup.py", "--mode", "health"],
        "Setup Health Check"
    )
    results["setup_health"] = success
    
    # Basic scraper test (PChome only for speed)
    success, _ = run_command(
        ["python", "scripts/test_scraper.py", "--mode", "basic", "--platforms", "pchome"],
        "Basic Scraper Test"
    )
    results["scraper_basic"] = success
    
    # ETL health check
    success, _ = run_command(
        ["python", "scripts/test_etl.py", "--mode", "health"],
        "ETL Health Check"
    )
    results["etl_health"] = success
    
    return results

def run_full_tests() -> Dict[str, bool]:
    """Run comprehensive test suite."""
    print_header("🧪 Full Test Suite", "=")
    results = {}
    
    # Setup tests
    success, _ = run_command(
        ["python", "scripts/test_setup.py", "--mode", "all"],
        "Complete Setup Testing"
    )
    results["setup_all"] = success
    
    # Scraper tests
    success, _ = run_command(
        ["python", "scripts/test_scraper.py", "--mode", "all"],
        "Complete Scraper Testing"
    )
    results["scraper_all"] = success
    
    # ETL tests
    success, _ = run_command(
        ["python", "scripts/test_etl.py", "--mode", "all"],
        "Complete ETL Testing"
    )
    results["etl_all"] = success
    
    return results

def run_setup_tests() -> Dict[str, bool]:
    """Run setup and environment tests."""
    print_header("🔧 Setup & Environment Tests", "=")
    results = {}
    
    success, _ = run_command(
        ["python", "scripts/test_setup.py", "--mode", "all"],
        "Complete Setup Testing"
    )
    results["setup_complete"] = success
    
    return results

def run_scraper_tests() -> Dict[str, bool]:
    """Run scraper and web scraping tests."""
    print_header("🕷️ Scraper & Web Scraping Tests", "=")
    results = {}
    
    success, _ = run_command(
        ["python", "scripts/test_scraper.py", "--mode", "all"],
        "Complete Scraper Testing"
    )
    results["scraper_complete"] = success
    
    return results

def run_etl_tests() -> Dict[str, bool]:
    """Run ETL pipeline tests."""
    print_header("📊 ETL Pipeline Tests", "=")
    results = {}
    
    success, _ = run_command(
        ["python", "scripts/test_etl.py", "--mode", "all"],
        "Complete ETL Testing"
    )
    results["etl_complete"] = success
    
    return results

def run_performance_tests() -> Dict[str, bool]:
    """Run performance and monitoring tests."""
    print_header("⚡ Performance & Monitoring Tests", "=")
    results = {}
    
    # System monitoring
    success, _ = run_command(
        ["python", "scripts/test_setup.py", "--mode", "monitor"],
        "System Resource Monitoring"
    )
    results["system_monitoring"] = success
    
    # Category diversity testing
    success, _ = run_command(
        ["python", "scripts/test_scraper.py", "--mode", "categories"],
        "Category Diversity Testing"
    )
    results["category_diversity"] = success
    
    # Automated ETL testing
    success, _ = run_command(
        ["python", "scripts/test_etl.py", "--mode", "automated"],
        "Automated ETL Performance"
    )
    results["etl_performance"] = success
    
    # Integration testing
    success, _ = run_command(
        ["python", "scripts/test_scraper.py", "--mode", "integration"],
        "Integration Performance Testing"
    )
    results["integration_performance"] = success
    
    return results

def print_summary(results: Dict[str, bool], test_type: str) -> None:
    """Print test results summary."""
    print_header(f"📋 {test_type} Summary", "=")
    
    total_tests = len(results)
    passed_tests = sum(1 for success in results.values() if success)
    failed_tests = total_tests - passed_tests
    
    print(f"\n{Colors.BOLD}Test Results:{Colors.END}")
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        formatted_name = test_name.replace('_', ' ').title()
        print(f"  {status} - {formatted_name}")
    
    print(f"\n{Colors.BOLD}Overall Statistics:{Colors.END}")
    print(f"  Total Tests: {total_tests}")
    print(f"  {Colors.GREEN}Passed: {passed_tests}{Colors.END}")
    print(f"  {Colors.RED}Failed: {failed_tests}{Colors.END}")
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    color = Colors.GREEN if success_rate >= 95 else Colors.YELLOW if success_rate >= 80 else Colors.RED
    print(f"  {color}Success Rate: {success_rate:.1f}%{Colors.END}")
    
    if failed_tests == 0:
        print(f"\n{Colors.GREEN}🎉 All tests passed! System is ready for operation.{Colors.END}")
    else:
        print(f"\n{Colors.RED}⚠️  {failed_tests} test(s) failed. Please review the output above.{Colors.END}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="PriceDragon Test Runner - Comprehensive testing for the PriceDragon platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_tests.py --quick         # Quick health check (recommended for development)
  python scripts/run_tests.py --full          # Full test suite (recommended before deployment)
  python scripts/run_tests.py --setup         # Setup and environment tests only
  python scripts/run_tests.py --scraper       # Web scraping tests only
  python scripts/run_tests.py --etl           # ETL pipeline tests only
  python scripts/run_tests.py --performance   # Performance and monitoring tests

Note: Tests run from the project root directory and require all dependencies to be installed.
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--quick", action="store_true", help="Run quick health check tests")
    group.add_argument("--full", action="store_true", help="Run complete test suite")
    group.add_argument("--setup", action="store_true", help="Run setup and environment tests")
    group.add_argument("--scraper", action="store_true", help="Run scraper tests")
    group.add_argument("--etl", action="store_true", help="Run ETL pipeline tests")
    group.add_argument("--performance", action="store_true", help="Run performance tests")
    
    args = parser.parse_args()
    
    # Print banner
    print(f"{Colors.BOLD}{Colors.MAGENTA}")
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║                    🐉 PriceDragon Test Runner                 ║")
    print("║                  Comprehensive Testing Suite                  ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Colors.CYAN}Started at: {timestamp}{Colors.END}")
    
    # Run appropriate test suite
    results = {}
    
    if args.quick:
        results = run_quick_tests()
        test_type = "Quick Health Check"
    elif args.full:
        results = run_full_tests()
        test_type = "Full Test Suite"
    elif args.setup:
        results = run_setup_tests()
        test_type = "Setup Tests"
    elif args.scraper:
        results = run_scraper_tests()
        test_type = "Scraper Tests"
    elif args.etl:
        results = run_etl_tests()
        test_type = "ETL Tests"
    elif args.performance:
        results = run_performance_tests()
        test_type = "Performance Tests"
    
    # Calculate total execution time
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Print summary
    print_summary(results, test_type)
    
    print(f"\n{Colors.CYAN}Completed in: {total_duration:.1f} seconds{Colors.END}")
    
    # Exit with appropriate code
    failed_tests = sum(1 for success in results.values() if not success)
    sys.exit(1 if failed_tests > 0 else 0)

if __name__ == "__main__":
    main()
