import os
import platform

def is_adguard_installed():
    return os.path.exists("/usr/local/bin/adguardvpn-cli")

def is_logged_in():
    """Проверяет, авторизован ли пользователь"""
    import subprocess
    try:
        result = subprocess.run(
            ['adguardvpn-cli', 'list-locations'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

def get_system_info():
    """Возвращает информацию о системе"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    os_info = ""
    if system == "darwin":
        os_info = "macOS (darwin)"
    elif system == "linux":
        os_info = "Linux"
    else:
        os_info = f"Неподдерживаемая ОС: {system}"
    
    arch_info = ""
    if machine in ["x86_64", "amd64"]:
        arch_info = "x86_64"
    elif machine in ["i386", "i486", "i586", "i686"]:
        arch_info = "i386"
    elif machine in ["arm64", "aarch64"]:
        arch_info = "arm64"
    elif machine in ["armv7l", "armv8l"]:
        arch_info = "armv7"
    else:
        arch_info = f"Неподдерживаемая архитектура: {machine}"
    
    return os_info, arch_info