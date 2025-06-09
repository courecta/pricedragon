"""PriceDragon Setup Test and System Monitor"""
import sys
import subprocess
import importlib
import time
import psutil
import requests
import logging
from datetime import datetime
from typing import Dict, Any
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Setup_Monitor')

def test_package_imports() -> bool:
    """Test if all required packages can be imported"""
    required_packages = [
        'requests', 'bs4', 'selenium', 'pandas', 
        'sqlalchemy', 'streamlit', 'plotly', 
        'fastapi', 'pydantic', 'redis'
    ]
    
    failed = []
    for package in required_packages:
        try:
            importlib.import_module(package)
            logger.info(f"✅ {package} imported successfully")
        except ImportError:
            logger.error(f"❌ {package} import failed")
            failed.append(package)
    
    return len(failed) == 0

def test_selenium() -> bool:
    """Test Selenium WebDriver (using Selenium Manager - no manual driver needed)"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        logger.info("  Setting up Chrome options...")
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--remote-debugging-port=9222')
        
        logger.info("  Starting Chrome driver (this may take a moment on first run)...")
        # Set a longer timeout for the initial setup
        driver = webdriver.Chrome(options=options)
        
        logger.info("  Testing navigation...")
        driver.set_page_load_timeout(10)
        driver.get('https://www.google.com')
        title = driver.title
        driver.quit()
        
        logger.info(f"✅ Selenium works - Got title: {title}")
        return True
    except Exception as e:
        logger.error(f"❌ Selenium failed: {e}")
        logger.info("  This might be due to network timeout during ChromeDriver download")
        return False

def test_database() -> bool:
    """Test database connection"""
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine('sqlite:///test.db')
        with engine.connect() as conn:
            result = conn.execute(text('SELECT 1'))
            logger.info("✅ Database connection works")
        return True
    except Exception as e:
        logger.error(f"❌ Database failed: {e}")
        return False

def check_system_resources() -> Dict[str, Any]:
    """Check CPU, memory, and disk usage"""
    logger.info("🖥️ Checking system resources...")
    
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        resource_info = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / (1024**3),
            'status': 'healthy'
        }
        
        logger.info(f"  💻 CPU Usage: {cpu_percent:.1f}%")
        logger.info(f"  🧠 Memory Usage: {memory.percent:.1f}% ({resource_info['memory_available_gb']:.1f}GB available)")
        logger.info(f"  💾 Disk Usage: {disk.percent:.1f}% ({resource_info['disk_free_gb']:.1f}GB free)")
        
        # Check for concerning resource usage
        warnings = []
        if cpu_percent > 80:
            warnings.append("High CPU usage")
        if memory.percent > 85:
            warnings.append("High memory usage")
        if disk.percent > 90:
            warnings.append("Low disk space")
        
        if warnings:
            logger.warning(f"⚠️ Resource warnings: {', '.join(warnings)}")
            resource_info['warnings'] = warnings
        else:
            logger.info("✅ System resources look healthy")
        
        return resource_info
        
    except Exception as e:
        logger.error(f"❌ Failed to check system resources: {e}")
        return {'status': 'error', 'error': str(e)}

def check_api_health(api_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Check API service health and response times"""
    logger.info("🌐 Checking API health...")
    
    try:
        start_time = time.time()
        
        # Test health endpoint
        health_response = requests.get(f"{api_url}/health", timeout=10)
        health_time = time.time() - start_time
        
        # Test products endpoint
        start_time = time.time()
        products_response = requests.get(f"{api_url}/products/", 
                                       params={"limit": 1}, timeout=10)
        products_time = time.time() - start_time
        
        api_info = {
            'timestamp': datetime.now().isoformat(),
            'health_status': health_response.status_code,
            'health_response_time': health_time,
            'products_status': products_response.status_code,
            'products_response_time': products_time,
            'api_available': health_response.status_code == 200,
            'status': 'healthy' if health_response.status_code == 200 else 'error'
        }
        
        if api_info['api_available']:
            logger.info(f"✅ API is healthy")
            logger.info(f"  📡 Health endpoint: {health_time:.2f}s")
            logger.info(f"  📦 Products endpoint: {products_time:.2f}s")
        else:
            logger.error(f"❌ API health check failed (Status: {health_response.status_code})")
        
        return api_info
        
    except requests.exceptions.ConnectionError:
        logger.warning("⚠️ API service is not running")
        return {
            'timestamp': datetime.now().isoformat(),
            'api_available': False,
            'status': 'not_running',
            'error': 'Connection refused - service not running'
        }
    except Exception as e:
        logger.error(f"❌ Failed to check API health: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'api_available': False,
            'status': 'error',
            'error': str(e)
        }

def check_dashboard_health(dashboard_url: str = "http://localhost:8501") -> Dict[str, Any]:
    """Check dashboard service health"""
    logger.info("📊 Checking dashboard health...")
    
    try:
        start_time = time.time()
        response = requests.get(dashboard_url, timeout=10)
        response_time = time.time() - start_time
        
        dashboard_info = {
            'timestamp': datetime.now().isoformat(),
            'status_code': response.status_code,
            'response_time': response_time,
            'dashboard_available': response.status_code == 200,
            'status': 'healthy' if response.status_code == 200 else 'error'
        }
        
        if dashboard_info['dashboard_available']:
            logger.info(f"✅ Dashboard is healthy (Response time: {response_time:.2f}s)")
        else:
            logger.error(f"❌ Dashboard health check failed (Status: {response.status_code})")
        
        return dashboard_info
        
    except requests.exceptions.ConnectionError:
        logger.warning("⚠️ Dashboard service is not running")
        return {
            'timestamp': datetime.now().isoformat(),
            'dashboard_available': False,
            'status': 'not_running',
            'error': 'Connection refused - service not running'
        }
    except Exception as e:
        logger.error(f"❌ Failed to check dashboard health: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'dashboard_available': False,
            'status': 'error',
            'error': str(e)
        }

def run_comprehensive_health_check() -> Dict[str, Any]:
    """Run complete system health check"""
    logger.info("🩺 Running Comprehensive Health Check")
    logger.info("=" * 50)
    
    health_report = {
        'timestamp': datetime.now().isoformat(),
        'system_resources': check_system_resources(),
        'api_health': check_api_health(),
        'dashboard_health': check_dashboard_health()
    }
    
    # Overall health assessment
    issues = []
    if health_report['system_resources'].get('status') == 'error':
        issues.append("System resource check failed")
    if health_report['system_resources'].get('warnings'):
        issues.append("System resource warnings")
    if not health_report['api_health'].get('api_available'):
        issues.append("API not available")
    if not health_report['dashboard_health'].get('dashboard_available'):
        issues.append("Dashboard not available")
    
    health_report['overall_status'] = 'healthy' if not issues else 'issues_detected'
    health_report['issues'] = issues
    
    logger.info("\n" + "=" * 50)
    logger.info("🏥 Health Check Summary")
    logger.info("=" * 50)
    
    if not issues:
        logger.info("🎉 All systems healthy!")
    else:
        logger.warning(f"⚠️ Issues detected: {', '.join(issues)}")
    
    return health_report

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='PriceDragon Setup Test and System Monitor')
    parser.add_argument('--mode', choices=['setup', 'monitor', 'health', 'all'], 
                       default='all', help='Test mode to run')
    parser.add_argument('--api-url', default='http://localhost:8000', 
                       help='API service URL')
    parser.add_argument('--dashboard-url', default='http://localhost:8501', 
                       help='Dashboard service URL')
    
    args = parser.parse_args()
    
    logger.info("🐉 PriceDragon Setup Test and System Monitor")
    logger.info("=" * 60)
    logger.info(f"Python version: {sys.version}")
    
    results = {}
    
    if args.mode in ['setup', 'all']:
        logger.info("\n🔸 Running Setup Tests...")
        results['imports'] = test_package_imports()
        results['selenium'] = test_selenium()
        results['database'] = test_database()
    
    if args.mode in ['monitor', 'health', 'all']:
        logger.info("\n🔸 Running System Health Check...")
        results['health'] = run_comprehensive_health_check()
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("🏆 SETUP & MONITOR SUMMARY")
    logger.info("=" * 60)
    
    if 'imports' in results:
        status = "✅" if results['imports'] else "❌"
        logger.info(f"  Package Imports: {status}")
    
    if 'selenium' in results:
        status = "✅" if results['selenium'] else "❌"
        logger.info(f"  Selenium WebDriver: {status}")
    
    if 'database' in results:
        status = "✅" if results['database'] else "❌"
        logger.info(f"  Database Connection: {status}")
    
    if 'health' in results:
        health_status = results['health'].get('overall_status', 'unknown')
        status = "✅" if health_status == 'healthy' else "⚠️"
        logger.info(f"  System Health: {status}")
        if results['health'].get('issues'):
            logger.info(f"    Issues: {', '.join(results['health']['issues'])}")
    
    # Determine overall success
    setup_success = all([
        results.get('imports', True),
        results.get('selenium', True), 
        results.get('database', True)
    ])
    
    health_good = results.get('health', {}).get('overall_status') != 'error'
    
    overall_success = setup_success and health_good
    
    if overall_success:
        if not results.get('health', {}).get('issues'):
            logger.info("\n🎉 ALL SYSTEMS GO! PriceDragon is ready for action!")
        else:
            logger.info("\n👍 MOSTLY READY! Some minor issues to address.")
    else:
        logger.info("\n⚠️ ISSUES DETECTED! Please review and fix before proceeding.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)