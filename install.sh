#!/bin/bash
set -e

# Stylized Terminal output colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

clear
echo -e "${CYAN}========================================================================${NC}"
echo -e "                 ${CYAN}🌟 Welcome to the OmniHub Installer 🌟${NC}"
echo -e "        Enterprise Multi-Agent Self-Learning Workspace Setup"
echo -e "${CYAN}========================================================================${NC}"
echo ""

# 1. Check Python installation
echo -e "${BLUE}[1/4] Checking Python Environment...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: Python 3 is not installed on this system.${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "✅ Found Python ${GREEN}${PYTHON_VERSION}${NC}"

# 2. Setup/Verify Virtual Environment
echo -e "\n${BLUE}[2/4] Verifying Virtual Environment (venv)...${NC}"
if [ ! -d "venv" ]; then
    echo -e "Creating virtual environment..."
    python3 -m venv venv
    echo -e "✅ Virtual environment created."
else
    echo -e "✅ Existing virtual environment found."
fi

# Ensure pip is up to date and requirements are met
echo -e "Upgrading pip and installing requirements..."
venv/bin/pip install --upgrade pip --quiet
if [ -f "requirements.txt" ]; then
    venv/bin/pip install -r requirements.txt --quiet
elif [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
    venv/bin/pip install . --quiet
fi
echo -e "✅ Python dependencies are up to date."

# 3. Interactive Oracle detection
echo -e "\n${BLUE}[3/4] Scanning System for External LLM CLI Tools (Oracles)...${NC}"

# Define candidates
CANDIDATES=("gemini" "chatgpt" "claude")
FOUND_CLIS=()

for cli in "${CANDIDATES[@]}"; do
    if command -v "$cli" &> /dev/null; then
        FOUND_CLIS+=("$cli")
        echo -e "  🔍 Found: ${GREEN}$cli${NC} at $(which $cli)"
    fi
done

DEFAULT_ORACLE=""
if [ ${#FOUND_CLIS[@]} -gt 0 ]; then
    DEFAULT_ORACLE="${FOUND_CLIS[0]}"
else
    echo -e "  ⚠️  No standard AI CLIs found. We recommend installing the 'gemini' CLI tool."
fi

echo -e "\n${YELLOW}Configuration Time! Please select or type your Oracle Command:${NC}"
if [ ${#FOUND_CLIS[@]} -gt 0 ]; then
    echo -e "We found these CLI tools on your system:"
    for i in "${!FOUND_CLIS[@]}"; do
        echo -e "  [$i] ${CYAN}${FOUND_CLIS[$i]}${NC}"
    done
    echo -e "  [c] ${YELLOW}Enter a custom command${NC}"
    
    read -p "Choose an option [default: 0]: " opt
    opt=${opt:-0}
    
    if [ "$opt" = "c" ]; then
        read -p "Enter custom command (e.g. chatgpt -p): " custom_cmd
        ORACLE_CMD="$custom_cmd"
    else
        SELECTED_CLI="${FOUND_CLIS[$opt]}"
        if [ "$SELECTED_CLI" = "gemini" ]; then
            ORACLE_CMD="gemini --prompt"
        else
            ORACLE_CMD="$SELECTED_CLI"
        fi
    fi
else
    read -p "No CLIs detected. Enter your desired Oracle command [default: gemini --prompt]: " custom_cmd
    ORACLE_CMD=${custom_cmd:-"gemini --prompt"}
fi

# Confirm Oracle configuration
echo -e "\n${GREEN}Oracle Command selected:${NC} ${MAGENTA}${ORACLE_CMD}${NC}"

# 4. Generate .env file
echo -e "\n${BLUE}[4/4] Generating Configuration Files...${NC}"
cat << EOF > .env
# OmniHub Environment Configuration
ORACLE_CMD="$ORACLE_CMD"
EOF
echo -e "✅ File ${GREEN}.env${NC} successfully generated!"

# Let's verify run_main.sh has .env support
if ! grep -q "source .env" run_main.sh; then
    echo "Updating run_main.sh to load the .env configuration..."
    cat << 'EOF' > run_main.sh
#!/bin/bash
if [ -f .env ]; then
    export $(cat .env | xargs)
fi
source venv/bin/activate
export PYTHONPATH="$PWD/venv/lib/python3.14/site-packages:$PYTHONPATH"
python main.py
EOF
    chmod +x run_main.sh
fi

echo -e "\n${CYAN}========================================================================${NC}"
echo -e "       🎉 ${GREEN}Congratulations! OmniHub is configured and ready to go!${NC} 🎉"
echo -e "            To start OmniHub, run: ${YELLOW}./run_main.sh${NC}"
echo -e "${CYAN}========================================================================${NC}\n"
