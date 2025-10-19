import tkinter as tk
import subprocess
import threading
import re
import os
from ui.components.button_styler import create_hover_button, apply_hover_effect
import platform

class SettingsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.setup_window_properties()
        self.root.title("Настройки AdGuard VPN")

        # --- Определяем окружение ---
        def is_steamdeck():
            """Проверяет, запущено ли приложение на Steam Deck или SteamOS"""
            try:
                # Проверяем /etc/os-release
                if os.path.exists("/etc/os-release"):
                    with open("/etc/os-release") as f:
                        os_info = f.read().lower()
                        if "steamos" in os_info or "steam deck" in os_info:
                            return True

                # Проверяем по системному имени (fallback)
                sys_name = platform.uname().machine.lower()
                if "steam" in sys_name or "deck" in sys_name:
                    return True

                # Проверяем compositor (часто Gamescope)
                result = subprocess.run(
                    ["ps", "-A"], capture_output=True, text=True
                )
                if "gamescope" in result.stdout.lower():
                    return True
            except:
                pass
            return False

        # --- Определяем размеры экрана ---
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Базовые размеры (оригинал)
        base_width = 525
        base_height = 520

        # --- Учёт ориентации ---
        if screen_height > screen_width:
            # Портретная ориентация (например, у Steam Deck)
            screen_width, screen_height = screen_height, screen_width

        # --- Подстройка под Steam Deck / SteamOS ---
        if is_steamdeck():
            # На Steam Deck — чуть меньше, чтобы влезало в экран даже с рамкой
            width = min(base_width + 20, screen_width + 20)
            height = min(base_height + 50, screen_height + 40)
            # Без центрирования (иначе Wayland игнорирует позицию)
            self.root.geometry(f"{int(width)}x{int(height)}")
        else:
            # На обычных системах (CachyOS, Windows, etc.)
            width = base_width
            height = base_height
            self.root.geometry(f"{width}x{height}")

        self.root.configure(bg='#182030')
        self.root.transient(parent)
        self.root.grab_set()

        try:
            from tkinter import ttk
            style = ttk.Style()
            style.theme_use('clam')  # или 'alt', 'classic' - простые темы
        except:
            pass

        self.setup_ui()
        self.load_current_settings()

    def setup_window_properties(self):
        """Настройка свойств окна для корректного отображения"""
        self.root.title("AdGuard VPN Manager")

        # Устанавливаем WM_CLASS (БЕЗ ПРОБЕЛОВ!)
        try:
            self.root.wm_class("AdGuardVPNManager")
        except:
            pass

        # Устанавливаем иконку
        try:
            manager_dir = os.path.expanduser("~/AdGuard VPN Manager")
            icon_path = os.path.join(manager_dir, "ico/adguard.png")
            if os.path.exists(icon_path):
                # Для PNG файлов в tkinter
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
        except Exception as e:
            print(f"Не удалось установить иконку: {e}")

    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg='#182030', padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = tk.Label(main_frame, text="Настройки AdGuard VPN",
                              font=("Arial", 16, "bold"), fg='white', bg='#182030')
        title_label.pack(pady=(0, 20))

        # Создаем контейнер для двух колонок
        columns_frame = tk.Frame(main_frame, bg='#182030')
        columns_frame.pack(fill=tk.BOTH, expand=True)

        # Левая колонка - Основные настройки
        left_column = tk.Frame(columns_frame, bg='#182030', width=300)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        left_column.pack_propagate(False)

        # Правая колонка - Дополнительные настройки
        right_column = tk.Frame(columns_frame, bg='#182030', width=300)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        right_column.pack_propagate(False)

        button_style = {
            'font': ('Arial', 10),
            'bg': '#15354D',
            'fg': 'white',
            'bd': 0,
            'padx': 10,
            'pady': 5,
            'width': 15,
            'highlightthickness':0,
            'cursor': 'hand2'
        }

        # === ЛЕВАЯ КОЛОНКА - ОСНОВНЫЕ НАСТРОЙКИ ===

        # Настройка режима VPN
        mode_frame = tk.Frame(left_column, bg='#182030', relief=tk.GROOVE, bd=0, padx=5, pady=5)
        mode_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(mode_frame, text="Режим VPN:",
                font=("Arial", 12, "bold"), fg='white', bg='#182030').pack(anchor=tk.W)

        # Фрейм для кнопок режима
        mode_buttons_frame = tk.Frame(mode_frame, bg='#182030')
        mode_buttons_frame.pack(fill=tk.X, pady=10)

        self.mode_var = tk.StringVar(value="TUN")

        self.tun_btn = tk.Radiobutton(mode_buttons_frame, text="TUN режим",
                                    variable=self.mode_var, value="TUN",
                                    font=("Arial", 10), fg='white', bg='#182030',
                                    selectcolor='#15354D', activebackground='#182030',
                                    activeforeground='white', bd=0, highlightthickness=0, cursor="hand2")
        self.tun_btn.pack(side=tk.LEFT, padx=(0, 20))

        self.socks_btn = tk.Radiobutton(mode_buttons_frame, text="SOCKS5 режим",
                                       variable=self.mode_var, value="SOCKS",
                                       font=("Arial", 10), fg='white', bg='#182030',
                                       selectcolor='#15354D', activebackground='#182030',
                                       activeforeground='white', bd=0, highlightthickness=0, cursor="hand2")
        self.socks_btn.pack(side=tk.LEFT)

        # Кнопка применения режима
        apply_btn = create_hover_button(mode_frame, text="Применить",
                                        command=self.apply_mode, **button_style)
        apply_btn.pack(anchor=tk.W, pady=(10, 0))

        # Настройка DNS-адреса
        dns_frame = tk.Frame(left_column, bg='#182030', relief=tk.GROOVE, bd=0, padx=5, pady=5)
        dns_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(dns_frame, text="DNS-настройки:",
                font=("Arial", 12, "bold"), fg='white', bg='#182030').pack(anchor=tk.W)

        # Фрейм для ввода порта
        dns_input_frame = tk.Frame(dns_frame, bg='#182030')
        dns_input_frame.pack(fill=tk.X, pady=10)

        tk.Label(dns_input_frame, text="DNS сервер:",
                font=("Arial", 10), fg='white', bg='#182030').pack(side=tk.LEFT)

        self.dns_entry = tk.Entry(dns_input_frame, width=10, font=('Arial', 10),
                                bg='#15354D', fg='white', highlightthickness=0, cursor="hand2")
        self.dns_entry.pack(side=tk.LEFT, padx=(10, 20))
        self.dns_entry.insert(0, "1.1.1.1")  # Пример порта по умолчанию

        # Кнопки для DNS
        dns_buttons_frame = tk.Frame(dns_frame, bg='#182030')
        dns_buttons_frame.pack(fill=tk.X, pady=(10, 0))

        apply_dns_btn = create_hover_button(dns_buttons_frame, text="Применить DNS",
                                            command=self.set_dns, **button_style)
        apply_dns_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Кнопка для возврата к настройкам по умолчанию
        default_btn = create_hover_button(dns_buttons_frame, text="Сбросить",
                                          command=self.set_default_dns, **button_style)
        default_btn.pack(side=tk.LEFT, padx=(0, 10))


        # === ПРАВАЯ КОЛОНКА - ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ ===
        # Настройка режима маршрутизации VPN-туннеля
        routing_frame = tk.Frame(right_column, bg='#182030', relief=tk.GROOVE, bd=0, padx=5, pady=5)
        routing_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(routing_frame, text="Режим VPN-туннеля:",
                font=("Arial", 12, "bold"), fg='white', bg='#182030').pack(anchor=tk.W)

        # Фрейм для кнопок режима маршрутизации
        routing_buttons_frame = tk.Frame(routing_frame, bg='#182030')
        routing_buttons_frame.pack(fill=tk.X, pady=10)

        self.routing_var = tk.StringVar(value="NONE")

        self.routing_none_btn = tk.Radiobutton(routing_buttons_frame, text="NONE",
                                              variable=self.routing_var, value="NONE",
                                              font=("Arial", 10), fg='white', bg='#182030',
                                              selectcolor='#15354D', activebackground='#182030',
                                              activeforeground='white', bd=0, highlightthickness=0, cursor="hand2")
        self.routing_none_btn.pack(side=tk.LEFT, padx=(0, 20))

        self.routing_auto_btn = tk.Radiobutton(routing_buttons_frame, text="AUTO",
                                              variable=self.routing_var, value="AUTO",
                                              font=("Arial", 10), fg='white', bg='#182030',
                                              selectcolor='#15354D', activebackground='#182030',
                                              activeforeground='white', bd=0, highlightthickness=0, cursor="hand2")
        self.routing_auto_btn.pack(side=tk.LEFT)

        # Кнопка применения режима маршрутизации
        apply_tun_btn = create_hover_button(routing_frame, text="Применить",
                                            command=self.apply_routing_mode, **button_style)
        apply_tun_btn.pack(anchor=tk.W, pady=(10, 0))

        # Настройка порта SOCKS5
        port_frame = tk.Frame(right_column, bg='#182030', relief=tk.GROOVE, bd=0, padx=5, pady=5)
        port_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(port_frame, text="Порт SOCKS5:",
                font=("Arial", 12, "bold"), fg='white', bg='#182030').pack(anchor=tk.W)

        # Фрейм для ввода порта
        port_input_frame = tk.Frame(port_frame, bg='#182030')
        port_input_frame.pack(fill=tk.X, pady=10)

        tk.Label(port_input_frame, text="Номер порта:",
                font=("Arial", 10), fg='white', bg='#182030').pack(side=tk.LEFT)

        self.port_entry = tk.Entry(port_input_frame, width=10, font=('Arial', 10),
                                bg='#15354D', fg='white', highlightthickness=0, cursor="hand2")
        self.port_entry.pack(side=tk.LEFT, padx=(10, 0))
        self.port_entry.insert(0, "1080")  # Пример порта по умолчанию

        # Кнопка установки порта
        apply_port_btn = create_hover_button(port_frame, text="Установить порт",
                                             command=self.set_socks_port, **button_style)
        apply_port_btn.pack(anchor=tk.W, pady=(10, 0))

        # # Пустое пространство для выравнивания
        # spacer_frame = tk.Frame(right_column, bg='#182030')
        # spacer_frame.pack(fill=tk.BOTH, expand=True)


        # Информационная рамка
        info_frame = tk.Frame(main_frame, bg='#182030', relief=tk.GROOVE, bd=0, padx=0, pady=0)
        info_frame.pack(fill=tk.X, pady=(0, 0))

        tk.Label(info_frame, text="Справка:",
                font=("Arial", 11, "bold"), fg='white', bg='#182030').pack(anchor=tk.W)

        info_text = (
            "• TUN: Полное VPN-подключение\n"
            "• SOCKS5: Прокси-режим через порт\n"
            "• NONE: Без маршрутизации\n"
            "• AUTO: Автоматическая маршрутизация\n"
            "• DNS: Укажите свой"
        )

        info_label = tk.Label(info_frame, text=info_text, font=("Arial", 10),
                             fg='#8e8e93', bg='#182030', justify=tk.LEFT)
        info_label.pack(anchor=tk.W, pady=0)

        # Статус бар внизу основного окна
        self.status_var = tk.StringVar(value="Готов к настройке")
        status_bar = tk.Label(main_frame, textvariable=self.status_var,
                             relief=tk.SUNKEN, anchor=tk.W, bg='#15354D', fg='white', highlightthickness=0)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 0))

        # Кнопка закрытия - по центру
        btn_frame = tk.Frame(main_frame, bg='#182030')
        btn_frame.pack(fill=tk.X, pady=5)

        close_btn = create_hover_button(btn_frame, text="Закрыть",
                                        command=self.close_window, **button_style)
        close_btn.pack(anchor=tk.CENTER)

    def load_current_settings(self):
        """Загружает текущие настройки"""
        try:
            # Получаем текущий режим VPN
            result = subprocess.run(
                ['adguardvpn-cli', 'config', 'get-mode'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                current_mode = result.stdout.strip()
                if "SOCKS" in current_mode.upper():
                    self.mode_var.set("SOCKS")
                else:
                    self.mode_var.set("TUN")

            # Получаем текущий порт SOCKS5
            result = subprocess.run(
                ['adguardvpn-cli', 'config', 'get-socks-port'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                current_port = result.stdout.strip()
                self.port_entry.delete(0, tk.END)
                self.port_entry.insert(0, current_port)

            # Получаем текущий DNS
            result = subprocess.run(
                ['adguardvpn-cli', 'config', 'get-dns'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                current_dns = result.stdout.strip()
                self.dns_entry.delete(0, tk.END)
                self.dns_entry.insert(0, current_dns)

            # Получаем текущий режим маршрутизации
            result = subprocess.run(
                ['adguardvpn-cli', 'config', 'get-tun-routing-mode'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                current_routing = result.stdout.strip().upper()
                if "NONE" in current_routing:
                    self.routing_var.set("NONE")
                else:
                    self.routing_var.set("AUTO")

        except Exception as e:
            self.status_var.set(f"❌ Ошибка загрузки настроек: {str(e)}")

    def apply_mode(self):
        """Применяет выбранный режим VPN"""
        selected_mode = self.mode_var.get()

        if selected_mode == "SOCKS":
            command = ['adguardvpn-cli', 'config', 'set-mode', 'SOCKS']
        else:
            command = ['adguardvpn-cli', 'config', 'set-mode', 'TUN']

        thread = threading.Thread(target=self._apply_setting_thread,
                                args=(command, f"Режим {selected_mode} успешно установлен"))

        thread.daemon = True
        thread.start()

    def set_socks_port(self):
        """Устанавливает порт SOCKS5"""
        port_text = self.port_entry.get().strip()

        if not port_text:
            self.status_var.set(f"❌ Ошибка. Введите номер порта")
            return

        if not port_text.isdigit():
            self.status_var.set(f"❌ Ошибка. Номер порта должен быть числом")
            return

        port = int(port_text)
        if port < 1 or port > 65535:
            self.status_var.set(f"❌ Ошибка. Номер порта должен быть в диапазоне 1-65535")
            return

        command = ['adguardvpn-cli', 'config', 'set-socks-port', str(port)]

        thread = threading.Thread(target=self._apply_setting_thread,
                                args=(command, f"Порт SOCKS5 изменен на {port}"))
        thread.daemon = True
        thread.start()

    def set_dns(self):
        """Устанавливает DNS-сервер"""
        dns_address = self.dns_entry.get().strip()

        if not dns_address:
            self.status_var.set(f"❌ Ошибка. Введите DNS-адрес")
            return

        # Простая валидация DNS-адреса
        if not re.match(r'^([0-9]{1,3}\.){3}[0-9]{1,3}$', dns_address):
            self.status_var.set(f"❌ Ошибка. Введите корректный IP-адрес DNS-сервера")
            return

        command = ['adguardvpn-cli', 'config', 'set-dns', dns_address]

        thread = threading.Thread(target=self._apply_setting_thread,
                                args=(command, f"DNS-сервер изменен на {dns_address}"))
        thread.daemon = True
        thread.start()

    def set_default_dns(self):
        """Возвращает DNS настройки к значениям по умолчанию"""
        default_dns = "default"

        # Обновляем поле ввода
        self.dns_entry.delete(0, tk.END)
        self.dns_entry.insert(0, default_dns)

        # Применяем настройку
        command = ['adguardvpn-cli', 'config', 'set-dns', default_dns]

        thread = threading.Thread(target=self._apply_setting_thread,
                                args=(command, f"DNS восстановлен по умолчанию: {default_dns}"))
        thread.daemon = True
        thread.start()

    def apply_routing_mode(self):
        """Применяет выбранный режим маршрутизации"""
        selected_routing = self.routing_var.get()

        command = ['adguardvpn-cli', 'config', 'set-tun-routing-mode', selected_routing]

        thread = threading.Thread(target=self._apply_setting_thread,
                                args=(command, f"Режим маршрутизации изменен на {selected_routing}"))
        thread.daemon = True
        thread.start()

    def _apply_setting_thread(self, command, success_message):
        """Общий поток для применения настроек"""
        try:
            setting_name = command[2]  # Получаем название настройки из команды
            self.root.after(0, lambda: self.status_var.set(f"Установка {setting_name}..."))

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                self.root.after(0, lambda: self.status_var.set(f"✅ {success_message}"))
            else:
                error_msg = result.stderr if result.stderr else "Неизвестная ошибка"
                self.root.after(0, lambda: self.status_var.set(f"❌ Не удалось изменить настройку: {error_msg}"))

        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"❌ Ошибка при изменении настройки: {str(e)}"))

    def close_window(self):
        self.root.destroy()

    def run(self):
        self.root.wait_window()
