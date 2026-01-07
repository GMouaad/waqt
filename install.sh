#!/bin/bash
set -e

# Waqt installer script for Linux/macOS
# Usage: curl -fsSL https://raw.githubusercontent.com/GMouaad/waqt/main/install.sh | bash
# Usage: curl -fsSL https://raw.githubusercontent.com/GMouaad/waqt/main/install.sh | bash -s -- --prerelease

REPO="GMouaad/waqt"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.waqt/bin}"
TMPDIR="${TMPDIR:-/tmp}"
PRERELEASE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

info() { echo -e "${GREEN}==>${NC} $1"; }
warn() { echo -e "${YELLOW}warning:${NC} $1"; }
error() { echo -e "${RED}error:${NC} $1" >&2; exit 1; }

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--prerelease)
            PRERELEASE=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Detect OS
detect_os() {
    case "$(uname -s)" in
        Linux*)  echo "linux" ;;
        Darwin*) echo "macos" ;;
        *)       error "Unsupported OS: $(uname -s)" ;;
    esac
}

# Detect architecture
detect_arch() {
    case "$(uname -m)" in
        x86_64|amd64)  echo "amd64" ;;
        arm64|aarch64) echo "arm64" ;;
        *)             error "Unsupported architecture: $(uname -m)" ;;
    esac
}

# Get release version (latest stable or dev prerelease)
get_release_version() {
    if [ "$PRERELEASE" = true ]; then
        # Dev prerelease always uses 'dev' tag - no API call needed
        echo "dev"
    else
        # Get latest stable release
        curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" |
            grep '"tag_name":' |
            sed -E 's/.*"([^"]+)".*/\1/'
    fi
}

main() {
    if [ "$PRERELEASE" = true ]; then
        info "Installing waqt (development build)..."
    else
        info "Installing waqt..."
    fi

    OS=$(detect_os)
    ARCH=$(detect_arch)

    info "Detected: ${OS}-${ARCH}"

    # Get release version
    VERSION=$(get_release_version)
    if [ -z "$VERSION" ]; then
        if [ "$PRERELEASE" = true ]; then
            error "No development build found. Dev builds are created on each push to main."
        else
            error "Could not determine latest version. Check https://github.com/${REPO}/releases"
        fi
    fi
    if [ "$PRERELEASE" = true ]; then
        info "Development build: ${VERSION}"
    else
        info "Latest version: ${VERSION}"
    fi

    # Download URL
    FILENAME="waqtracker-${OS}-${ARCH}.zip"
    URL="https://github.com/${REPO}/releases/download/${VERSION}/${FILENAME}"

    info "Downloading ${URL}..."

    DOWNLOAD_PATH="${TMPDIR}/waqt-download-$$"
    mkdir -p "$DOWNLOAD_PATH"

    if ! curl -fsSL "$URL" -o "${DOWNLOAD_PATH}/${FILENAME}"; then
        error "Failed to download ${URL}"
    fi

    # Extract
    info "Extracting..."
    unzip -q "${DOWNLOAD_PATH}/${FILENAME}" -d "${DOWNLOAD_PATH}"

    # Install
    mkdir -p "$INSTALL_DIR"
    mv "${DOWNLOAD_PATH}/waqtracker" "${INSTALL_DIR}/waqtracker"
    chmod +x "${INSTALL_DIR}/waqtracker"

    # Create symlink for 'waqt' command
    ln -sf "${INSTALL_DIR}/waqtracker" "${INSTALL_DIR}/waqt"

    # Cleanup
    rm -rf "$DOWNLOAD_PATH"

    # Verify installation
    info "Successfully installed waqt!"
    "${INSTALL_DIR}/waqtracker" --version

    # Add to PATH if not already there
    if [[ ":$PATH:" != *":${INSTALL_DIR}:"* ]]; then
        add_to_path
    else
        info "Install directory is already in PATH"
    fi

    echo ""
    info "Installation complete! You can now use 'waqt' or 'waqtracker' commands."
    echo ""
    echo "  Quick start:"
    echo "    waqt --version      # Check version"
    echo "    waqtracker          # Start the web server (http://localhost:5555)"
    echo "    waqt start          # Start time tracking from CLI"
    echo "    waqt summary        # View summary"
    echo ""
}

# Detect shell and add to appropriate config file
add_to_path() {
    # GitHub Actions: add to GITHUB_PATH
    if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
        echo "$INSTALL_DIR" >> "$GITHUB_PATH"
        info "Added to GITHUB_PATH for this workflow"
        return
    fi

    local shell_name
    shell_name=$(basename "${SHELL:-/bin/bash}")

    local config_file=""
    local path_line=""

    case "$shell_name" in
        bash)
            if [[ -f "$HOME/.bashrc" ]]; then
                config_file="$HOME/.bashrc"
            elif [[ -f "$HOME/.bash_profile" ]]; then
                config_file="$HOME/.bash_profile"
            else
                config_file="$HOME/.bashrc"
            fi
            path_line='export PATH="$HOME/.waqt/bin:$PATH"'
            ;;
        zsh)
            config_file="${ZDOTDIR:-$HOME}/.zshrc"
            path_line='export PATH="$HOME/.waqt/bin:$PATH"'
            ;;
        fish)
            config_file="${XDG_CONFIG_HOME:-$HOME/.config}/fish/config.fish"
            path_line='fish_add_path $HOME/.waqt/bin'
            ;;
        *)
            # Fallback to .profile for other POSIX shells
            config_file="$HOME/.profile"
            path_line='export PATH="$HOME/.waqt/bin:$PATH"'
            ;;
    esac

    # Create config file directory if needed
    mkdir -p "$(dirname "$config_file")"

    # Check if already added
    if [[ -f "$config_file" ]] && grep -q "/.waqt/bin" "$config_file" 2>/dev/null; then
        info "PATH already configured in $config_file"
        return
    fi

    # Add to config file
    echo "" >> "$config_file"
    echo "# Added by waqt installer" >> "$config_file"
    echo "$path_line" >> "$config_file"

    info "Added waqt to PATH in $config_file"
    echo ""
    echo "Restart your terminal or run:"
    echo "  source $config_file"
}

main "$@"
