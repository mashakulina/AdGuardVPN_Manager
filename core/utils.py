import re
import subprocess
import os

def clean_ansi_codes(text):
    """Очищает текст от ANSI escape sequences"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def detect_os():
    """Определяет операционную систему"""
    import platform
    system = platform.system().lower()
    if system == "darwin":
        return "macOS (darwin)"
    elif system == "linux":
        return "Linux"
    else:
        return f"Неподдерживаемая ОС: {system}"

def detect_arch():
    """Определяет архитектуру процессора"""
    import platform
    machine = platform.machine().lower()
    if machine in ["x86_64", "amd64"]:
        return "x86_64"
    elif machine in ["i386", "i486", "i586", "i686"]:
        return "i386"
    elif machine in ["arm64", "aarch64"]:
        return "arm64"
    elif machine in ["armv7l", "armv8l"]:
        return "armv7"
    else:
        return f"Неподдерживаемая архитектура: {machine}"

def get_latest_version():
    """Получает последнюю версию AdGuard VPN"""
    try:
        return "1.5.10"
    except:
        return "1.5.10"

def get_download_url(os_type, arch, version):
    """Формирует правильный URL для скачивания"""
    package_name = f"adguardvpn-cli-{version}-{os_type}-{arch}.tar.gz"
    download_url = f"https://github.com/AdguardTeam/AdGuardVPNCLI/releases/download/v{version}-release/{package_name}"
    return download_url, package_name

def check_if_connected(text):
    """Точно проверяет, подключен ли VPN"""
    text_lower = text.lower()

    connected_indicators = [
        'connected to',
        'successfully connected',
        'you are connected',
        'подключен к',
        'running on tun',
        'tun mode'
    ]

    disconnected_indicators = [
        'not connected',
        'disconnected',
        'no connection',
        'не подключен',
        'отключен'
    ]

    for indicator in disconnected_indicators:
        if indicator in text_lower:
            return False

    for indicator in connected_indicators:
        if indicator in text_lower:
            return True

    return False

def clean_location_output(text):
    """Очищает вывод локации от лишних данных, включая ANSI коды"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_text = ansi_escape.sub('', text)

    patterns = [
        r'Connected to (.+?) in',
        r'connected to (.+?) in',
        r'Connected to (.+?)\n',
        r'Connected to (.+?)\.',
        r'Location: (.+)',
        r'подключен к (.+?) в',
        r'Подключено к (.+?) в',
        r'Successfully Connected to (.+)',
        r'You are connected to (.+?)\.'
    ]

    for pattern in patterns:
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            return location

    locations = {
        'frankfurt': 'Frankfurt',
        'london': 'London',
        'new york': 'New York',
        'singapore': 'Singapore',
        'tokyo': 'Tokyo',
        'amsterdam': 'Amsterdam',
        'paris': 'Paris',
        'moscow': 'Moscow'
    }

    clean_text_lower = clean_text.lower()
    for key, value in locations.items():
        if key in clean_text_lower:
            return value

    return ""