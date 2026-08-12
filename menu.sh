#!/bin/bash

###############################################################################
# UNIVERSAL AI CODING BRIDGE (UACB) - CONTROL CENTER
# Version: 1.0.0
# Author: Senior Software Architect & AI Agent Engineer
###############################################################################

# --- CẤU HÌNH MÀU SẮC & GIAO DIỆN ---
COLOR_RESET="\033[0m"
COLOR_BOLD="\033[1m"
COLOR_DIM="\033[2m"
COLOR_RED="\033[31m"
COLOR_GREEN="\033[32m"
COLOR_YELLOW="\033[33m"
COLOR_BLUE="\033[34m"
COLOR_MAGENTA="\033[35m"
COLOR_CYAN="\033[36m"
COLOR_WHITE="\033[37m"

# Ký tự vẽ khung
BOX_TOP_LEFT="╔"
BOX_TOP_RIGHT="╗"
BOX_BOTTOM_LEFT="╚"
BOX_BOTTOM_RIGHT="╝"
BOX_VERTICAL="║"
BOX_HORIZONTAL="═"
BOX_INTERSECTION="╠"
BOX_T_RIGHT="╣"

# --- BIẾN TOÀN CỤC ---
BRIDGE_PORT=8765
BRIDGE_PID_FILE="/tmp/uacb_bridge.pid"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON_CMD="python3"

# --- HÀM TIỆN ÍCH ---

# Xóa màn hình và đưa con trỏ về gốc
clear_screen() {
    clear
    echo -ne "\033[3J" # Xóa lịch sử buffer (tùy terminal)
}

# In văn bản có màu
print_color() {
    local color=$1
    local text=$2
    echo -e "${color}${text}${COLOR_RESET}"
}

# In đậm
print_bold() {
    echo -e "${COLOR_BOLD}$1${COLOR_RESET}"
}

# Delay ngắn để tạo hiệu ứng
sleep_short() {
    sleep 0.05
}

# --- ANIMATION ENGINE ---

# Hiệu ứng gõ chữ (Typewriter)
type_writer() {
    local text="$1"
    local delay="${2:-0.02}"
    echo -n "  "
    for (( i=0; i<${#text}; i++ )); do
        echo -n "${text:$i:1}"
        sleep $delay
    done
    echo ""
}

# Vẽ khung hộp
draw_box() {
    local width=$1
    local height=$2
    local title="$3"
    
    local h_line=""
    for ((i=0; i<$width; i++)); do h_line+="${BOX_HORIZONTAL}"; done
    
    echo -e "${COLOR_CYAN}${BOX_TOP_LEFT}${h_line}${BOX_TOP_RIGHT}${COLOR_RESET}"
    
    if [ -n "$title" ]; then
        local padding=$(( (width - ${#title} - 2) / 2 ))
        local left_pad=""
        local right_pad=""
        for ((i=0; i<$padding; i++)); do left_pad+=" "; done
        for ((i=0; i<$((width - ${#title} - 2 - padding)); i++)); do right_pad+=" "; done
        echo -e "${COLOR_CYAN}${BOX_VERTICAL}${COLOR_RESET} ${COLOR_BOLD}${title}${COLOR_RESET}${left_pad}${right_pad} ${COLOR_CYAN}${BOX_VERTICAL}${COLOR_RESET}"
    else
        echo -e "${COLOR_CYAN}${BOX_VERTICAL}${COLOR_RESET}$(printf '%*s' $width '')${COLOR_CYAN}${BOX_VERTICAL}${COLOR_RESET}"
    fi

    for ((i=0; i<$height; i++)); do
        echo -e "${COLOR_CYAN}${BOX_VERTICAL}${COLOR_RESET}$(printf '%*s' $width '')${COLOR_CYAN}${BOX_VERTICAL}${COLOR_RESET}"
    done
    
    echo -e "${COLOR_CYAN}${BOX_BOTTOM_LEFT}${h_line}${BOX_BOTTOM_RIGHT}${COLOR_RESET}"
}

# Thanh tiến trình (Progress Bar)
show_progress() {
    local duration=$1
    local task=$2
    local steps=20
    local interval=$(echo "scale=2; $duration / $steps" | bc)
    
    echo -ne "  ${COLOR_CYAN}[$task]${COLOR_RESET} ["
    for ((i=0; i<=$steps; i++)); do
        echo -ne "${COLOR_GREEN}█${COLOR_RESET}"
        sleep $interval
    done
    echo -e "] ${COLOR_GREEN}DONE${COLOR_RESET}"
}

# Hiệu ứng loading quay tròn
spinner() {
    local pid=$1
    local msg=$2
    local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0
    
    echo -ne "  ${COLOR_YELLOW}⠋${COLOR_RESET} $msg ... "
    while kill -0 $pid 2>/dev/null; do
        i=$(( (i+1) % 10 ))
        echo -ne "\r  ${COLOR_YELLOW}${spin:$i:1}${COLOR_RESET} $msg ... "
        sleep 0.1
    done
    echo -e "\r  ${COLOR_GREEN}✔${COLOR_RESET} $msg ... ${COLOR_GREEN}COMPLETED${COLOR_RESET}\n"
}

# --- LOGIC KIỂM TRA HỆ THỐNG ---

check_dependencies() {
    local missing=()
    
    command -v python3 >/dev/null 2>&1 || missing+=("python3")
    command -v pip3 >/dev/null 2>&1 || missing+=("pip3")
    command -v node >/dev/null 2>&1 || missing+=("nodejs")
    command -v bc >/dev/null 2>&1 || missing+=("bc")
    
    if [ ${#missing[@]} -ne 0 ]; then
        print_color $COLOR_RED "❌ Thiếu dependencies: ${missing[*]}"
        print_color $COLOR_YELLOW "   Vui lòng chạy: sudo apt install ${missing[*]} -y"
        return 1
    fi
    return 0
}

check_bridge_status() {
    if [ -f "$BRIDGE_PID_FILE" ]; then
        local pid=$(cat "$BRIDGE_PID_FILE")
        if kill -0 $pid 2>/dev/null; then
            return 0 # Đang chạy
        fi
    fi
    # Thử check port nếu file PID mất
    if lsof -Pi :$BRIDGE_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0
    fi
    return 1 # Không chạy
}

# --- CÁC CHỨC NĂNG CHÍNH ---

func_install() {
    clear_screen
    draw_box 60 5 "🚀 UACB INSTALLATION WIZARD"
    echo ""
    
    if [ ! -d "$VENV_DIR" ]; then
        type_writer "Đang tạo môi trường ảo Python..."
        python3 -m venv "$VENV_DIR"
        show_progress 2 "venv"
    else
        print_color $COLOR_GREEN "  ✓ Môi trường ảo đã tồn tại."
    fi
    
    source "$VENV_DIR/bin/activate"
    
    type_writer "Đang cài đặt dependencies..."
    pip install -q -r requirements.txt 2>/dev/null || pip install -q fastapi uvicorn pydantic pytest requests
    show_progress 3 "pip install"
    
    if [ -f "install.sh" ]; then
        type_writer "Đang chạy script cài đặt bổ sung..."
        chmod +x install.sh
        ./install.sh > /dev/null 2>&1 &
        spinner $! "Setup sandbox & permissions"
    fi
    
    echo ""
    print_color $COLOR_GREEN "✅ CÀI ĐẶT HOÀN TẤT!"
    echo ""
    print_color $COLOR_WHITE "👉 BƯỚC TIẾP THEO:"
    echo "   1. Chọn option '2' trong menu này để khởi động Bridge."
    echo "   2. Mở Chrome và load folder 'browser-extension'."
    read -p "   Nhấn Enter để quay lại menu..."
}

func_start_bridge() {
    clear_screen
    draw_box 60 5 "🌉 STARTING LOCAL BRIDGE SERVER"
    echo ""
    
    if check_bridge_status; then
        print_color $COLOR_YELLOW "  ⚠️ Bridge đang chạy rồi tại port $BRIDGE_PORT"
        print_color $COLOR_DIM "     PID: $(cat $BRIDGE_PID_FILE 2>/dev/null || echo 'N/A')"
    else
        source "$VENV_DIR/bin/activate" 2>/dev/null || true
        
        # Chạy background
        nohup python3 -m bridge.server > logs/bridge.log 2>&1 &
        echo $! > "$BRIDGE_PID_FILE"
        
        type_writer "Đang khởi động server..."
        sleep 1
        
        # Chờ server ready
        local max_wait=10
        local count=0
        while ! check_bridge_status && [ $count -lt $max_wait ]; do
            echo -ne "."
            sleep 0.5
            count=$((count+1))
        done
        echo ""
        
        if check_bridge_status; then
            print_color $COLOR_GREEN "✅ BRIDGE ĐÃ CHẠY THÀNH CÔNG!"
            print_color $COLOR_CYAN "   URL: http://127.0.0.1:$BRIDGE_PORT"
            print_color $COLOR_CYAN "   Health: http://127.0.0.1:$BRIDGE_PORT/health"
        else
            print_color $COLOR_RED "❌ KHÔNG THỂ KHỞI ĐỘNG BRIDGE."
            print_color $COLOR_YELLOW "   Xem log chi tiết: cat logs/bridge.log"
        fi
    fi
    
    echo ""
    print_color $COLOR_WHITE "👉 BƯỚC TIẾP THEO:"
    echo "   1. Mở Google Chrome (hoặc Chromium)."
    echo "   2. Truy cập: chrome://extensions/"
    echo "   3. Bật 'Developer mode' (góc trên phải)."
    echo "   4. Nhấn 'Load unpacked' và chọn folder: $SCRIPT_DIR/browser-extension"
    echo "   5. Mở ChatGPT/Claude và bắt đầu chat."
    read -p "   Nhấn Enter để quay lại menu..."
}

func_stop_bridge() {
    clear_screen
    draw_box 60 3 "🛑 STOPPING BRIDGE SERVER"
    echo ""
    
    if [ -f "$BRIDGE_PID_FILE" ]; then
        local pid=$(cat "$BRIDGE_PID_FILE")
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            rm -f "$BRIDGE_PID_FILE"
            print_color $COLOR_GREEN "✅ Đã dừng Bridge (PID: $pid)"
        else
            print_color $COLOR_YELLOW "⚠️ Process không tồn tại nhưng file PID vẫn còn. Đã xóa."
            rm -f "$BRIDGE_PID_FILE"
        fi
    elif lsof -Pi :$BRIDGE_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        local pid=$(lsof -ti:$BRIDGE_PORT)
        kill $pid
        print_color $COLOR_GREEN "✅ Đã dừng Bridge (Tìm qua Port)"
    else
        print_color $COLOR_YELLOW "ℹ️ Bridge chưa chạy."
    fi
    
    read -p "   Nhấn Enter để quay lại menu..."
}

func_run_tests() {
    clear_screen
    draw_box 60 5 "🧪 RUNNING TEST SUITE"
    echo ""
    
    source "$VENV_DIR/bin/activate" 2>/dev/null || true
    
    if [ ! -d "tests" ]; then
        print_color $COLOR_RED "❌ Không tìm thấy thư mục tests/"
        read -p "   Nhấn Enter..."
        return
    fi
    
    type_writer "Đang chạy Unit Tests & Integration Tests..."
    echo ""
    
    pytest tests/ -v --tb=short
    
    echo ""
    print_color $COLOR_WHITE "👉 KẾT QUẢ:"
    if [ $? -eq 0 ]; then
        print_color $COLOR_GREEN "   ✅ TẤT CẢ TESTS ĐÃ PASS"
        echo "   Hệ thống sẵn sàng cho Production."
    else
        print_color $COLOR_RED "   ❌ MỘT SỐ TESTS FAILED"
        echo "   Vui lòng kiểm tra log lỗi ở trên."
    fi
    
    read -p "   Nhấn Enter để quay lại menu..."
}

func_view_logs() {
    clear_screen
    draw_box 60 15 "📜 LIVE LOGS (TAIL)"
    echo ""
    
    local log_file="logs/bridge.log"
    if [ ! -f "$log_file" ]; then
        touch "$log_file"
        echo "Log file created." > "$log_file"
    fi
    
    print_color $COLOR_DIM "   (Nhấn Ctrl+C để thoát chế độ xem log)"
    echo ""
    
    # Sử dụng tail -f nhưng bắt tín hiệu ngắt để quay lại menu
    trap 'break' INT
    tail -n 50 -f "$log_file" --color=always
    trap - INT
    
    read -p "   Nhấn Enter để quay lại menu..."
}

func_show_guide() {
    clear_screen
    draw_box 70 20 "📘 HƯỚNG DẪN SỬ DỤNG UACB"
    echo ""
    
    cat << EOF
${COLOR_BOLD}QUY TRÌNH CHUẨN (ZERO-CONFIG FLOW):${COLOR_RESET}

1. 📂 **Chuẩn bị Project**:
   - Copy project của bạn vào: ${COLOR_CYAN}sandbox/my_project/${COLOR_RESET}
   - Ví dụ: smart_pet_ai/

2. 🌉 **Khởi động Bridge**:
   - Chọn option ${COLOR_GREEN}[2] Start Bridge${COLOR_RESET} trong menu này.
   - Đảm bảo status là "RUNNING".

3. 🔌 **Cài đặt Extension**:
   - Mở Chrome -> chrome://extensions/
   - Bật Developer Mode -> Load unpacked -> Chọn folder ${COLOR_CYAN}browser-extension/${COLOR_RESET}
   - Vào Popup của Extension, đảm bảo URL là: http://127.0.0.1:8765

4. 🤖 **Kết nối AI Web**:
   - Mở ChatGPT / Claude / Gemini.
   - Nhắn lệnh tự nhiên:
     ${COLOR_YELLOW}"Sửa AgentExecutor, chạy python3 main.py, phân tích traceback, 
     sửa tất cả lỗi và chạy pytest cho tới khi PASS."${COLOR_RESET}

5. 👁️ **Quan sát**:
   - Extension sẽ tự động detect block code đặc biệt.
   - Gửi lệnh về Local Bridge.
   - Bridge thực thi trong Sandbox.
   - Kết quả trả ngược lại AI.
   - AI tự sửa lỗi và lặp lại cho đến khi PASS.

${COLOR_BOLD}LƯU Ý BẢO MẬT:${COLOR_RESET}
- Bridge chỉ chạy trên localhost (127.0.0.1).
- Chỉ truy cập được folder sandbox/.
- Không thể truy cập file hệ thống quan trọng.

EOF
    read -p "   Nhấn Enter để đóng hướng dẫn..."
}

# --- MENU CHÍNH ---

show_menu() {
    clear_screen
    
    # Header Animation
    echo -e "${COLOR_CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║   🌌  UNIVERSAL AI CODING BRIDGE (UACB) - CONTROL CENTER      ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${COLOR_RESET}"
    
    # Status Check
    local status_text="OFFLINE"
    local status_color=$COLOR_RED
    if check_bridge_status; then
        status_text="ONLINE (Port $BRIDGE_PORT)"
        status_color=$COLOR_GREEN
    fi
    
    echo -e "  Trạng thái Bridge: ${status_color}● $status_text${COLOR_RESET}"
    echo -e "  Thư mục làm việc:  ${COLOR_DIM}$SCRIPT_DIR${COLOR_RESET}"
    echo ""
    echo -e "${COLOR_DIM}──────────────────────────────────────────────────────────────────${COLOR_RESET}"
    echo ""
    
    # Menu Items
    local options=(
        "🚀 Cài đặt / Update Dependencies"
        "🌉 Khởi động Local Bridge Server"
        "🛑 Dừng Local Bridge Server"
        "🧪 Chạy Test Suite (Pytest)"
        "📜 Xem Live Logs"
        "📘 Hướng dẫn sử dụng (Guide)"
        "❌ Thoát"
    )
    
    for i in "${!options[@]}"; do
        local num=$((i+1))
        if [ $num -eq 7 ]; then
             echo -e "  ${COLOR_RED}[$num]${COLOR_RESET} ${options[$i]}"
        else
             echo -e "  ${COLOR_GREEN}[$num]${COLOR_RESET} ${options[$i]}"
        fi
    done
    
    echo ""
    echo -e "${COLOR_DIM}──────────────────────────────────────────────────────────────────${COLOR_RESET}"
    echo -ne "  👉 Chọn chức năng [1-7]: "
}

# --- VÒNG LẶP CHÍNH ---

main_loop() {
    # Kiểm tra dependency lần đầu
    if ! check_dependencies; then
        exit 1
    fi
    
    # Tạo thư mục logs nếu chưa có
    mkdir -p logs
    
    while true; do
        show_menu
        read -r choice
        
        case $choice in
            1) func_install ;;
            2) func_start_bridge ;;
            3) func_stop_bridge ;;
            4) func_run_tests ;;
            5) func_view_logs ;;
            6) func_show_guide ;;
            7|q|Q) 
                clear_screen
                print_color $COLOR_CYAN "Cảm ơn bạn đã sử dụng UACB. Hẹn gặp lại!"
                exit 0 
                ;;
            *) 
                echo -e "  ${COLOR_RED}Lựa chọn không hợp lệ. Vui lòng thử lại.${COLOR_RESET}"
                sleep 1
                ;;
        esac
    done
}

# Bắt đầu chương trình
main_loop
