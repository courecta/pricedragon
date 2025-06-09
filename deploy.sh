#!/bin/bash

# PriceDragon Production Deployment Script
# This script sets up the production environment for PriceDragon

set -e  # Exit on any error

echo "🚀 Starting PriceDragon Production Deployment..."

# Configuration
PROJECT_DIR="/home/courecta/pricedragon"
API_PORT=8000
DASHBOARD_PORT=8501
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if port is in use
check_port() {
    local port=$1
    if netstat -tuln | grep -q ":$port "; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to stop existing processes
stop_services() {
    print_status "Stopping existing services..."
    
    # Stop API server
    if [ -f "$PID_DIR/api.pid" ]; then
        local api_pid=$(cat "$PID_DIR/api.pid")
        if ps -p $api_pid > /dev/null; then
            kill $api_pid
            print_status "Stopped API server (PID: $api_pid)"
        fi
        rm -f "$PID_DIR/api.pid"
    fi
    
    # Stop dashboard
    if [ -f "$PID_DIR/dashboard.pid" ]; then
        local dashboard_pid=$(cat "$PID_DIR/dashboard.pid")
        if ps -p $dashboard_pid > /dev/null; then
            kill $dashboard_pid
            print_status "Stopped dashboard (PID: $dashboard_pid)"
        fi
        rm -f "$PID_DIR/dashboard.pid"
    fi
    
    # Kill any remaining uvicorn or streamlit processes
    pkill -f "uvicorn.*pricedragon" 2>/dev/null || true
    pkill -f "streamlit.*pricedragon" 2>/dev/null || true
    
    sleep 2
}

# Function to optimize database
optimize_database() {
    print_status "Optimizing database..."
    cd "$PROJECT_DIR"
    PYTHONPATH="$PROJECT_DIR" python database/performance_optimizations.py > "$LOG_DIR/optimization.log" 2>&1
    if [ $? -eq 0 ]; then
        print_status "Database optimization completed"
    else
        print_warning "Database optimization had warnings (check logs)"
    fi
}

# Function to start API server
start_api() {
    print_status "Starting API server on port $API_PORT..."
    
    if check_port $API_PORT; then
        print_error "Port $API_PORT is already in use"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    nohup python -m uvicorn api.main:app \
        --host 0.0.0.0 \
        --port $API_PORT \
        --workers 2 \
        --access-log \
        --log-level info > "$LOG_DIR/api.log" 2>&1 &
    
    local api_pid=$!
    echo $api_pid > "$PID_DIR/api.pid"
    
    # Wait for API to start
    sleep 3
    if ps -p $api_pid > /dev/null; then
        print_status "API server started successfully (PID: $api_pid)"
        
        # Test API health
        if curl -s http://localhost:$API_PORT/health > /dev/null; then
            print_status "API health check passed"
        else
            print_warning "API health check failed"
        fi
    else
        print_error "Failed to start API server"
        exit 1
    fi
}

# Function to start dashboard
start_dashboard() {
    print_status "Starting dashboard on port $DASHBOARD_PORT..."
    
    if check_port $DASHBOARD_PORT; then
        print_error "Port $DASHBOARD_PORT is already in use"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    nohup streamlit run dashboard/enhanced_main.py \
        --server.port $DASHBOARD_PORT \
        --server.address 0.0.0.0 \
        --server.headless true \
        --server.runOnSave false \
        --server.fileWatcherType none > "$LOG_DIR/dashboard.log" 2>&1 &
    
    local dashboard_pid=$!
    echo $dashboard_pid > "$PID_DIR/dashboard.pid"
    
    # Wait for dashboard to start
    sleep 5
    if ps -p $dashboard_pid > /dev/null; then
        print_status "Dashboard started successfully (PID: $dashboard_pid)"
    else
        print_error "Failed to start dashboard"
        exit 1
    fi
}

# Function to run system health check
health_check() {
    print_status "Running system health check..."
    
    local errors=0
    
    # Check API
    if curl -s http://localhost:$API_PORT/health | grep -q "healthy"; then
        print_status "✅ API server is healthy"
    else
        print_error "❌ API server health check failed"
        errors=$((errors + 1))
    fi
    
    # Check database
    cd "$PROJECT_DIR"
    if PYTHONPATH="$PROJECT_DIR" python -c "from database.db_utils import DatabaseManager; db = DatabaseManager(); print('Database OK')" > /dev/null 2>&1; then
        print_status "✅ Database connection is healthy"
    else
        print_error "❌ Database connection failed"
        errors=$((errors + 1))
    fi
    
    # Check dashboard (basic port check)
    if check_port $DASHBOARD_PORT; then
        print_status "✅ Dashboard is running"
    else
        print_error "❌ Dashboard is not running"
        errors=$((errors + 1))
    fi
    
    if [ $errors -eq 0 ]; then
        print_status "🎉 All health checks passed!"
        return 0
    else
        print_error "❌ $errors health check(s) failed"
        return 1
    fi
}

# Function to display system status
show_status() {
    echo
    echo "=================== PRICEDRAGON STATUS ==================="
    echo "API Server:    http://localhost:$API_PORT"
    echo "Dashboard:     http://localhost:$DASHBOARD_PORT"
    echo "API Docs:      http://localhost:$API_PORT/docs"
    echo "Log Directory: $LOG_DIR"
    echo "PID Directory: $PID_DIR"
    echo
    echo "Process Status:"
    
    if [ -f "$PID_DIR/api.pid" ]; then
        local api_pid=$(cat "$PID_DIR/api.pid")
        if ps -p $api_pid > /dev/null; then
            echo "  API Server:  Running (PID: $api_pid)"
        else
            echo "  API Server:  Stopped"
        fi
    else
        echo "  API Server:  Not started"
    fi
    
    if [ -f "$PID_DIR/dashboard.pid" ]; then
        local dashboard_pid=$(cat "$PID_DIR/dashboard.pid")
        if ps -p $dashboard_pid > /dev/null; then
            echo "  Dashboard:   Running (PID: $dashboard_pid)"
        else
            echo "  Dashboard:   Stopped"
        fi
    else
        echo "  Dashboard:   Not started"
    fi
    
    echo "=========================================================="
}

# Main deployment logic
main() {
    case "${1:-start}" in
        "start")
            stop_services
            optimize_database
            start_api
            start_dashboard
            sleep 2
            health_check
            show_status
            ;;
        "stop")
            stop_services
            print_status "All services stopped"
            ;;
        "restart")
            stop_services
            sleep 2
            start_api
            start_dashboard
            sleep 2
            health_check
            show_status
            ;;
        "status")
            show_status
            health_check
            ;;
        "logs")
            echo "=== API Logs ==="
            tail -n 20 "$LOG_DIR/api.log" 2>/dev/null || echo "No API logs found"
            echo
            echo "=== Dashboard Logs ==="
            tail -n 20 "$LOG_DIR/dashboard.log" 2>/dev/null || echo "No dashboard logs found"
            ;;
        "health")
            health_check
            ;;
        *)
            echo "Usage: $0 [start|stop|restart|status|logs|health]"
            echo
            echo "Commands:"
            echo "  start    - Start all services (default)"
            echo "  stop     - Stop all services"
            echo "  restart  - Restart all services"
            echo "  status   - Show service status"
            echo "  logs     - Show recent logs"
            echo "  health   - Run health checks"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
