#!/bin/bash

# PLANNER AGENT Setup Script
# Installs conda via Homebrew, sets up environment, and runs the health data collection system

set -e  # Exit on any error

echo "🏥 PLANNER AGENT Setup - Strategic Health Data Collection System"
echo "================================================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [[ ! "$(pwd)" == *"/heltia"* ]]; then
    print_error "This script should be run from ~/heltia directory"
    print_status "Please run: mkdir ~/heltia && cd ~/heltia"
    exit 1
fi

# Function to install Homebrew
install_homebrew() {
    print_status "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for current session
    if [[ $(uname -m) == "arm64" ]]; then
        # Apple Silicon Mac
        export PATH="/opt/homebrew/bin:$PATH"
        echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
    else
        # Intel Mac
        export PATH="/usr/local/bin:$PATH"
        echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
    fi
    
    print_success "Homebrew installed successfully!"
}

# Function to check and install Homebrew if needed
setup_homebrew() {
    if command -v brew &> /dev/null; then
        print_success "Homebrew is already installed: $(brew --version | head -n1)"
    else
        print_warning "Homebrew not found. Installing..."
        install_homebrew
    fi
}

# Function to check and install conda via Homebrew
setup_conda() {
    if command -v conda &> /dev/null; then
        print_success "Conda is already installed: $(conda --version)"
    else
        print_status "Installing miniconda via Homebrew..."
        brew install --cask miniconda
        
        # Add conda to PATH for current session
        if [[ $(uname -m) == "arm64" ]]; then
            # Apple Silicon Mac
            export PATH="/opt/homebrew/Caskroom/miniconda/base/bin:$PATH"
        else
            # Intel Mac  
            export PATH="/usr/local/Caskroom/miniconda/base/bin:$PATH"
        fi
        
        # Initialize conda for current session
        conda init zsh
        conda init bash
        
        # Source the appropriate zsh config file to activate conda immediately (skip errors)
        if [ -f ~/.config/zsh/.zshrc ]; then
            source ~/.config/zsh/.zshrc 2>/dev/null || true
            print_status "Sourced conda from ~/.config/zsh/.zshrc"
        elif [ -f ~/.zshrc ]; then
            source ~/.zshrc 2>/dev/null || true
            print_status "Sourced conda from ~/.zshrc"
        fi
        
        print_success "Miniconda installed via Homebrew!"
        print_warning "You may need to restart terminal for conda to be fully available"
    fi
}

# Function to clone the repository
clone_repository() {
    if [ -d "onboarding_assistant" ]; then
        print_warning "Directory 'onboarding_assistant' already exists. Pulling latest changes..."
        cd onboarding_assistant
        git pull origin master || git pull origin main
        cd ..
    else
        print_status "Cloning PLANNER AGENT repository..."
        git clone https://github.com/PoyrazTahan/onboarding_assistant.git
        print_success "Repository cloned successfully!"
    fi
}

# Function to create conda environment
create_environment() {
    print_status "Creating conda environment 'planner_agent'..."
    
    # Check if environment already exists
    if conda env list | grep -q "planner_agent"; then
        print_warning "Environment 'planner_agent' already exists. Removing and recreating..."
        conda env remove -n planner_agent -y
    fi
    
    # Create new environment with Python 3.11
    conda create -n planner_agent python=3.11 -y
    
    print_success "Conda environment 'planner_agent' created!"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Get conda base path
    CONDA_BASE=$(conda info --base)
    
    # Activate environment using proper script method
    source "${CONDA_BASE}/etc/profile.d/conda.sh"
    conda activate planner_agent
    
    # Navigate to project directory
    cd onboarding_assistant
    
    # Install dependencies from requirements.txt
    pip install -r requirements.txt
    
    print_success "All dependencies installed successfully!"
}

# Function to setup environment file
setup_env_file() {
    # Go back to heltia directory and then into onboarding_assistant
    cd ~/heltia/onboarding_assistant
    
    if [ ! -f ".env" ]; then
        print_status "Creating .env file template..."
        cat > .env << EOF
# OpenAI API Key - Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=your-openai-api-key-here
EOF
        print_warning "⚠️  IMPORTANT: Edit the .env file and add your OpenAI API key!"
        print_status "Your .env file is located at: $(pwd)/.env"
    else
        print_success ".env file already exists"
    fi
}

# Function to test the installation
test_installation() {
    print_status "Testing installation..."
    
    cd ~/heltia/onboarding_assistant
    
    # Activate environment for testing using proper script method
    CONDA_BASE=$(conda info --base)
    source "${CONDA_BASE}/etc/profile.d/conda.sh"
    conda activate planner_agent
    
    # Check if we can import the main modules
    if python -c "import sys; sys.path.append('.'); from core.agent import Agent; print('✅ Core modules import successfully')"; then
        print_success "Installation test passed!"
        return 0
    else
        print_error "Installation test failed. Please check dependencies."
        return 1
    fi
}

# Function to provide next steps
show_next_steps() {
    echo ""
    echo "🎉 Setup Complete!"
    echo "================="
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo "1. Add your OpenAI API key to the .env file:"
    echo -e "   ${BLUE}nano ~/heltia/onboarding_assistant/.env${NC}"
    echo ""
    echo "2. Activate the conda environment:"
    echo -e "   ${BLUE}conda activate planner_agent${NC}"
    echo ""
    echo "3. Navigate to the project directory:"
    echo -e "   ${BLUE}cd ~/heltia/onboarding_assistant${NC}"
    echo ""
    echo "4. Run the PLANNER AGENT:"
    echo -e "   ${BLUE}python app.py${NC}                    # Turkish persona mode"
    echo -e "   ${BLUE}python app.py --core-agent${NC}       # English only mode"
    echo -e "   ${BLUE}python app.py --debug${NC}            # Debug mode"
    echo ""
    echo "5. Run automated tests:"
    echo -e "   ${BLUE}python test.py${NC}                   # Run all tests"
    echo -e "   ${BLUE}python test.py list${NC}              # List available tests"
    echo -e "   ${BLUE}python test.py run 1${NC}             # Run specific test"
    echo ""
    echo -e "${YELLOW}📖 For more information, see the README.md file${NC}"
    echo ""
    echo -e "${GREEN}🔄 If conda commands don't work, restart your terminal and try again${NC}"
}

# Main installation flow
main() {
    print_status "Starting PLANNER AGENT setup..."
    
    # Step 1: Setup Homebrew
    setup_homebrew
    
    # Step 2: Setup conda via Homebrew
    setup_conda
    
    # Step 3: Clone repository
    clone_repository
    
    # Step 4: Create conda environment
    create_environment
    
    # Step 5: Install dependencies
    install_dependencies
    
    # Step 6: Setup environment file
    setup_env_file
    
    # Step 7: Test installation
    if test_installation; then
        show_next_steps
    else
        print_error "Setup completed with errors. Please check the output above."
        print_status "You may need to restart your terminal and run 'conda activate planner_agent' manually"
        exit 1
    fi
}

# Handle script interruption
trap 'echo -e "\n${RED}[ERROR]${NC} Setup interrupted. Please run the script again."; exit 1' INT

# Run main function
main

print_success "🏥 PLANNER AGENT setup completed successfully!"