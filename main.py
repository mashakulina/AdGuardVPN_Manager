#!/usr/bin/env python3
import tkinter as tk
import os
import sys
import subprocess
from core.auth import SudoAuthWindow, AuthWindow
from core.installer import AdGuardVPNInstaller
from ui.windows.manager import AdGuardVPNManager

def is_adguard_installed():
    return os.path.exists("/usr/local/bin/adguardvpn-cli")

def is_logged_in():
    """Проверяет, авторизован ли пользователь"""
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

def main():
    if os.geteuid() == 0:
        print("Не запускайте скрипт напрямую от root!")
        sys.exit(1)

    # Сначала проверяем установлен ли AdGuard VPN
    if not is_adguard_installed():
        print("AdGuard VPN не установлен, запуск установки...")
        # Только для установки запрашиваем sudo пароль
        auth_window = SudoAuthWindow()
        sudo_password, auth_success = auth_window.run()

        if not auth_success or not sudo_password:
            print("Sudo аутентификация отменена")
            sys.exit(0)

        installer = AdGuardVPNInstaller(sudo_password)
        installer.run()
        # После установки продолжаем

    # Проверяем статус авторизации
    if not is_logged_in():
        # Если не авторизован, показываем окно авторизации
        auth_window = AuthWindow()
        auth_success = auth_window.run()
        # Независимо от результата, запускаем приложение

    root = tk.Tk()
    app = AdGuardVPNManager(root)
    app.run()

if __name__ == "__main__":
    main()
