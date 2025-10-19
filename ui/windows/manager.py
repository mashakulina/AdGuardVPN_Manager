import tkinter as tk
from tkinter import ttk, scrolledtext, PhotoImage
import subprocess
import threading
import time
import webbrowser
import sys
import re
from datetime import datetime, date
from ui.windows.locations import LocationSelectionWindow
from ui.windows.settings import SettingsWindow
from ui.windows.updates import UpdateWindow
from core.uninstall import UninstallWindow
from ui.components.common import create_tooltip
from core.auth import ManagerAuthWindow
from core.utils import clean_ansi_codes, clean_location_output, check_if_connected
import os
from ui.components.dialogs import show_message_dialog, show_question_dialog
from ui.components.button_styler import create_hover_button, create_hover_button_for_manager
from ui.windows.license import LicenseWindow
from ui.windows.info_dialog import show_info_dialog
from ui.windows.donat import DonationWindow
_last_available_site = None
_last_check_time = 0

def get_available_site():
    """Возвращает доступный сайт с кэшированием на 5 минут"""
    global _last_available_site, _last_check_time

    import time
    current_time = time.time()

    # Если прошло меньше 5 минут, возвращаем кэшированный результат
    if _last_available_site and (current_time - _last_check_time) < 300:
        return _last_available_site

    sites = [
        "https://adguard-vpn.com",
        "https://adguard-vpn.work",
        "https://adguardvpn-help.net"
    ]

    # Используем улучшенную проверку
    for site in sites:
        if check_site_availability_improved(site):
            _last_available_site = site
            _last_check_time = current_time
            return site

    # Если ни один сайт не доступен, возвращаем основной
    _last_available_site = sites[0]
    _last_check_time = current_time
    return sites[0]

def check_site_availability_improved(url):
    """Улучшенная проверка доступности сайта"""
    try:
        import socket
        import ssl
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.netloc
        port = 443  # HTTPS по умолчанию

        # Создаем socket с таймаутом
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)  # 3 секунды таймаут

        # Пробуем подключиться
        sock.connect((domain, port))

        # Для HTTPS создаем SSL контекст
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        ssl_sock = context.wrap_socket(sock, server_hostname=domain)
        ssl_sock.close()

        return True

    except (socket.timeout, ConnectionRefusedError, ssl.SSLError, OSError):
        return False
    except Exception:
        return False

class AdGuardVPNManager:
    def __init__(self, root):
        self.root = root
        self.setup_window_properties()
        self.root.title("AdGuard VPN Manager")
        self.window_height_hidden = 210  # Высота когда лог скрыт
        self.window_height_visible = 355  # Высота когда лог показан
        self.window_width = 570
        self.root.geometry(f"{self.window_width}x{self.window_height_hidden}")
        self.root.configure(bg='#182030')


        try:
            from tkinter import ttk
            style = ttk.Style()
            style.theme_use('clam')  # или 'alt', 'classic' - простые темы
        except:
            pass

        self.sudo_password = None
        self.current_location = ""
        self.is_connected = False

        self.is_logged_in = False
        self.check_initial_login_status()  # Проверяем статус при запуске

        # Флаг для отслеживания состояния выпадающего меню
        self.account_menu_open = False
        self.settings_menu_open = False

        # Bind событий фокус
        self.root.bind("<FocusIn>", self.on_focus_in)
        self.root.bind("<FocusOut>", self.on_focus_out)

        self.setup_gui()
        self.update_status()
        self.update_ui_for_auth_status()
        self.schedule_status_update()
        self.hide_log()
        self.log_visible = False

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

    def on_focus_in(self, event):
        """Обрабатывает получение фокуса окном"""
        pass  # Можно добавить логику при необходимости

    def on_focus_out(self, event):
        """Обрабатывает потерю фокуса окном - закрываем меню"""
        self.close_all_menus()

    def check_initial_login_status(self):
        """Синхронно проверяет статус авторизации при запуске"""
        try:
            result = subprocess.run(
                ['adguardvpn-cli', 'list-locations'],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.is_logged_in = (result.returncode == 0)
        except:
            self.is_logged_in = False

    def setup_gui(self):
        # Основной контейнер
        main_container = tk.Frame(self.root, bg='#182030')
        main_container.pack(fill=tk.BOTH, expand=True)

        # Верхняя панель с логотипом и статусом
        header_frame = tk.Frame(main_container, bg='#182030', height=100)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        header_frame.pack_propagate(False)

        # Верхняя строка: логотип + иконки
        top_row_frame = tk.Frame(header_frame, bg='#182030')
        top_row_frame.pack(fill=tk.X, pady=(5, 0))

        left_icons_frame = tk.Frame(top_row_frame, bg='#182030')
        left_icons_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Иконка личного кабинета
        self.account_icon = tk.Label(left_icons_frame, text="👤", font=("Arial", 16),
                                fg='#0a84ff', bg='#182030', cursor="hand2")
        self.account_icon.pack(side=tk.LEFT, padx=(0, 15))
        self.account_icon.bind("<Enter>", lambda e: self.account_icon.config(fg='#30d158'))
        self.account_icon.bind("<Leave>", lambda e: self.account_icon.config(fg='#0a84ff'))
        self.account_icon.bind("<Button-1>", self.toggle_account_menu)
        create_tooltip(self.account_icon, "Личный кабинет")

        # Email пользователя (рядом с иконкой)
        self.email_label = tk.Label(left_icons_frame, text="",
                            font=("Arial", 11), fg='#8e8e93', bg='#182030', justify='left')
        self.email_label.pack(side=tk.LEFT, padx=(0, 15))

        self.update_email_display()

        # Логотип и заголовок по центру
        logo_container = tk.Frame(header_frame, bg='#182030')
        logo_container.pack(expand=True, fill=tk.BOTH)

        # Центрирующий фрейм
        center_frame = tk.Frame(logo_container, bg='#182030')
        center_frame.pack(expand=True)

        try:
            # Загрузка изображения
            manager_dir = os.path.expanduser("~/AdGuard VPN Manager")
            logo_path = os.path.join(manager_dir, "ico/logo.png")
            self.logo_image = tk.PhotoImage(file=logo_path)
            logo_icon = tk.Label(center_frame, image=self.logo_image, bg='#182030')
            logo_icon.pack(side=tk.LEFT, padx=(0, 10))

        except Exception as e:
            print(f"Не удалось загрузить логотип: {e}")
            logo_icon = tk.Label(center_frame, text="🛡️", font=("Arial", 24),
                            fg='white', bg='#182030')
            logo_icon.pack(side=tk.LEFT, padx=(0, 10))

        title_label = tk.Label(center_frame, text="AdGuard VPN",
                            font=("Arial", 24, "bold"),
                            fg='white', bg='#182030')
        title_label.pack(side=tk.LEFT)

        # Иконки справа
        icons_frame = tk.Frame(top_row_frame, bg='#182030')
        icons_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Статус подключения
        self.status_label = tk.Label(icons_frame, text="🔴", font=("Arial", 12),
                                    fg='#ff3b30', bg='#182030')
        self.status_label.pack(side=tk.LEFT, padx=(0, 15))
        self.status_label.bind("<Enter>", lambda e: self.status_label.config(fg='#30d158'))
        self.status_label.bind("<Leave>", lambda e: self.status_label.config(fg='#0a84ff'))
        create_tooltip(self.status_label, "Статус подключения к VPN")

        # Иконка глаза для скрытия/показа лога
        self.eye_icon = tk.Label(icons_frame, text="📝", font=("Arial", 14),
                                    fg='#0a84ff', bg='#182030', cursor="hand2")
        self.eye_icon.pack(side=tk.LEFT, padx=(0, 15))
        self.eye_icon.bind("<Enter>", lambda e: self.eye_icon.config(fg='#30d158'))
        self.eye_icon.bind("<Leave>", lambda e: self.eye_icon.config(fg='#0a84ff'))
        self.eye_icon.bind("<Button-1>", self.toggle_log_visibility)
        create_tooltip(self.eye_icon, "Показать/скрыть лог")

        # Иконка шестеренки (настройки)
        self.settings_icon = tk.Label(icons_frame, text="⚙️", font=("Arial", 22),
                                    fg='#0a84ff', bg='#182030', cursor="hand2")
        self.settings_icon.pack(side=tk.LEFT, padx=(0, 15))
        self.settings_icon.bind("<Enter>", lambda e: self.settings_icon.config(fg='#30d158'))
        self.settings_icon.bind("<Leave>", lambda e: self.settings_icon.config(fg='#0a84ff'))
        self.settings_icon.bind("<Button-1>", self.toggle_settings_menu)
        create_tooltip(self.settings_icon, "Настройки")

        # Иконка информации
        self.info_icon = tk.Label(icons_frame, text="🛈︎", font=("Arial", 16),
                                fg='#0a84ff', bg='#182030', cursor="hand2")
        self.info_icon.pack(side=tk.LEFT, padx=(0, 15))
        self.info_icon.bind("<Enter>", lambda e: self.info_icon.config(fg='#30d158'))
        self.info_icon.bind("<Leave>", lambda e: self.info_icon.config(fg='#0a84ff'))
        self.info_icon.bind("<Button-1>", lambda e: show_info_dialog(self.root))

        # Иконка доната
        self.donate_icon = tk.Label(icons_frame, text="💸", font=("Arial", 14),
                                fg='#ffcc00', bg='#182030', cursor="hand2")
        self.donate_icon.pack(side=tk.LEFT)
        self.donate_icon.bind("<Enter>", lambda e: self.donate_icon.config(fg='#ffdd44'))
        self.donate_icon.bind("<Leave>", lambda e: self.donate_icon.config(fg='#ffcc00'))
        self.donate_icon.bind("<Button-1>", self.open_donate_link)

        # Добавляем подсказки
        create_tooltip(self.settings_icon, "Список настроек")
        create_tooltip(self.info_icon, "Открыть справку AdGuard VPN")
        create_tooltip(self.donate_icon, "Поддержать разработку")

        # Основная область контента
        content_frame = tk.Frame(main_container, bg='#182030')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Кнопки
        btn_frame = tk.Frame(content_frame, bg='#182030')
        btn_frame.pack(fill=tk.X, pady=10)

        self.connect_button = tk.Button(btn_frame, text="Подключиться",
                                        command=self.connect_vpn, font=('Arial', 11), bg='#5BA06A', fg='white', bd=0, padx=12, pady=12, width=17, anchor='center',
                                        highlightthickness=0, cursor='hand2',
                                        activebackground='#5BA06A', activeforeground='white', takefocus=0)
        self.connect_button.grid(row=0, column=1, padx=(0, 10))


        location_button = create_hover_button_for_manager(btn_frame, "Выбрать локацию", self.select_location)
        location_button.grid(row=0, column=2)

        # Центрируем весь фрейм с кнопками
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)
        btn_frame.grid_columnconfigure(3, weight=1)

        # Фрейм для лога (изначально скрыт)
        self.log_frame = tk.Frame(content_frame, bg='#182030', height=140)
        self.log_frame.pack(fill=tk.X, pady=(0, 0), expand=False)
        self.log_frame.pack_propagate(False)

        tk.Label(self.log_frame, text="Логи:",
                font=("Arial", 11), fg='white', bg='#182030').pack(anchor=tk.W, pady=(0, 5))

        self.log_text = tk.Text(self.log_frame, bg='#15354D', highlightthickness=0, wrap=tk.WORD,
                            fg='#00ff00', font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

    def log_message(self, message):
        """Добавление сообщения в лог"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def toggle_log_visibility(self, event=None):
        """Переключает видимость лога"""
        if self.log_visible:
            self.hide_log()
        else:
            self.show_log()

    def show_log(self):
        """Показывает лог"""
        self.log_frame.pack(fill=tk.X, pady=(0, 5))
        self.eye_icon.config(text="🚫")
        self.log_visible = True
        create_tooltip(self.eye_icon, "Скрыть лог")
        self.log_text.see(tk.END)

        # Увеличиваем высоту окна
        self.root.geometry(f"{self.window_width}x{self.window_height_visible}")

    def hide_log(self):
        """Скрывает лог"""
        self.log_frame.pack_forget()
        self.eye_icon.config(text="📝")
        self.log_visible = False
        create_tooltip(self.eye_icon, "Показать лог")

        # Уменьшаем высоту окна
        self.root.geometry(f"{self.window_width}x{self.window_height_hidden}")

    def update_login_button(self):
        """Обновляет текст и цвет кнопки входа/выхода"""
        pass

    def toggle_account_menu(self, event=None):
        """Открывает/закрывает меню личного кабинета"""
        if self.account_menu_open:
            self.close_account_menu()
        else:
            self.open_account_menu()

    def open_account_menu(self):
        """Открывает меню личного кабинета"""
        if self.account_menu_open:
            return

        if hasattr(self, 'settings_menu_open') and self.settings_menu_open:
            self.close_settings_menu()

        self.account_menu_open = True

        # Создаем выпадающее меню
        menu_x = self.account_icon.winfo_rootx()
        menu_y = self.account_icon.winfo_rooty() + self.account_icon.winfo_height()

        self.account_menu = tk.Toplevel(self.root)
        self.account_menu.wm_overrideredirect(True)

        # Получаем тип лицензии для определения текста кнопки
        license_type = self.get_license_type() if self.is_logged_in else "Free"

        # Динамически рассчитываем высоту меню
        if self.is_logged_in:
            # Для авторизованных: тип лицензии + инфо о лицензии + купить/продлить + выход
            menu_height = 165
        else:
            # Для неавторизованных: только вход
            menu_height = 40

        self.account_menu.geometry(f"165x{menu_height}+{menu_x}+{menu_y}")
        self.account_menu.configure(bg='#15354D', relief=tk.RAISED, bd=1)

        # Стиль для кнопок меню
        menu_button_style = {
            'font': ('Arial', 11),
            'bg': '#15354D',
            'fg': 'white',
            'bd': 0,
            'relief': tk.FLAT,
            'padx': 12,
            'pady': 10,
            'anchor': tk.W,
            'width': 15,
            'highlightthickness':0,
            'cursor': 'hand2'
        }

        # Стиль для текстовой информации
        text_style = {
            'font': ('Arial', 10),
            'bg': '#15354D',
            'fg': '#8e8e93',
            'bd': 0,
            'padx': 12,
            'pady': 5,
            'anchor': tk.W
        }

        # Отображаем тип лицензии (только для авторизованных пользователей)
        if self.is_logged_in:
            license_text = f"Тип лицензии: {license_type}"

            license_label = tk.Label(self.account_menu, text=license_text, **text_style)
            license_label.pack(fill=tk.X)

            # Разделитель
            separator = tk.Frame(self.account_menu, height=1, bg='#1e4a6a')
            separator.pack(fill=tk.X, padx=5, pady=2)

            # Кнопка "Инфо о лицензии"
            license_info_button = create_hover_button_for_manager(self.account_menu, text="Инфо о лицензии",
                                        command=self.check_license, **menu_button_style)
            license_info_button.pack(fill=tk.X)

            # Bind событий для hover эффекта
            license_info_button.bind("<Enter>", lambda e: license_info_button.config(bg='#1e4a6a'))
            license_info_button.bind("<Leave>", lambda e: license_info_button.config(bg='#15354D'))

            # Разделитель
            separator = tk.Frame(self.account_menu, height=1, bg='#1e4a6a')
            separator.pack(fill=tk.X, padx=5, pady=2)

            # Кнопка "Купить лицензию" или "Продлить лицензию" в зависимости от типа
            if license_type == "Free":
                renew_button_text = "Купить лицензию"
            else:
                renew_button_text = "Продлить лицензию"

            renew_button = create_hover_button_for_manager(self.account_menu, text=renew_button_text,
                                command=self.renew_license, **menu_button_style)
            renew_button.pack(fill=tk.X)

            # Bind событий для hover эффекта
            renew_button.bind("<Enter>", lambda e: renew_button.config(bg='#1e4a6a'))
            renew_button.bind("<Leave>", lambda e: renew_button.config(bg='#15354D'))

            # Разделитель перед кнопкой выхода
            separator2 = tk.Frame(self.account_menu, height=1, bg='#1e4a6a')
            separator2.pack(fill=tk.X, padx=5, pady=2)

        # Кнопка входа/выхода
        auth_text = "Выйти из аккаунта" if self.is_logged_in else "Войти в аккаунт"
        self.menu_auth_button = create_hover_button_for_manager(self.account_menu, text=auth_text,
                                        command=self.handle_menu_auth, **menu_button_style)
        self.menu_auth_button.pack(fill=tk.X)

        # Bind событий для hover эффекта
        self.menu_auth_button.bind("<Enter>", lambda e: self.menu_auth_button.config(bg='#1e4a6a'))
        self.menu_auth_button.bind("<Leave>", lambda e: self.menu_auth_button.config(bg='#15354D'))

        # Bind событие клика вне меню для закрытия
        self.account_menu.bind("<FocusOut>", lambda e: self.close_account_menu())
        self.root.bind("<Button-1>", self.check_close_account_menu)

    def close_account_menu(self):
        """Закрывает меню личного кабинета"""
        if hasattr(self, 'account_menu') and self.account_menu:
            try:
                self.account_menu.destroy()
            except:
                pass  # Если окно уже уничтожено
        self.account_menu_open = False
        try:
            self.root.unbind("<Button-1>")
        except:
            pass

    def check_close_account_menu(self, event):
        """Проверяет, нужно ли закрыть меню при клике вне его области"""
        if (hasattr(self, 'account_menu') and self.account_menu and
            self.account_menu.winfo_exists()):

            # Проверяем, был ли клик на самом меню или иконке
            menu_widget = event.widget
            while menu_widget:
                if menu_widget == self.account_menu:
                    return  # Клик внутри меню - не закрываем
                menu_widget = menu_widget.master

            # Если клик был не в меню и не на иконке - закрываем
            if (event.widget != self.account_icon and
                not self.is_event_in_widget(event, self.account_icon)):
                self.close_account_menu()

    def is_event_in_widget(self, event, widget):
        """Проверяет, находится ли событие в области виджета"""
        try:
            x, y, width, height = (widget.winfo_rootx(), widget.winfo_rooty(),
                                widget.winfo_width(), widget.winfo_height())
            return (x <= event.x_root <= x + width and
                y <= event.y_root <= y + height)
        except:
            return False

    def handle_menu_auth(self):
        """Обрабатывает авторизацию/выход из меню"""
        self.close_account_menu()
        if self.is_logged_in:
            self.logout()
        else:
            thread = threading.Thread(target=self._login_thread)
            thread.daemon = True
            thread.start()

    def renew_license(self):
        """Открывает страницу покупки/продления лицензии"""
        self.close_account_menu()
        license_type = self.get_license_type() if self.is_logged_in else "Free"

        if license_type == "Free":
            action_text = "покупки лицензии"
        else:
            action_text = "продления лицензии"

        available_site = get_available_site()
        webbrowser.open(available_site)
        self.log_message(f"🔗 Открыта страница {action_text}")

    def toggle_settings_menu(self, event=None):
        """Открывает/закрывает меню настроек"""
        if hasattr(self, 'settings_menu_open') and self.settings_menu_open:
            self.close_settings_menu()
        else:
            self.open_settings_menu()

    def open_settings_menu(self):
        """Открывает меню настроек"""
        if hasattr(self, 'settings_menu_open') and self.settings_menu_open:
            return

        # Закрываем другие меню перед открытием
        if self.account_menu_open:
            self.close_account_menu()

        self.settings_menu_open = True

        # Создаем выпадающее меню
        menu_x = self.settings_icon.winfo_rootx()
        menu_y = self.settings_icon.winfo_rooty() + self.settings_icon.winfo_height()

        self.settings_menu = tk.Toplevel(self.root)
        self.settings_menu.wm_overrideredirect(True)
        self.settings_menu.geometry(f"180x135+{menu_x}+{menu_y}")
        self.settings_menu.configure(bg='#15354D', relief=tk.RAISED, bd=1)

        # Стиль для кнопок меню
        menu_button_style = {
            'font': ('Arial', 11),
            'bg': '#15354D',
            'fg': 'white',
            'bd': 0,
            'relief': tk.FLAT,
            'padx': 12,
            'pady': 10,
            'anchor': tk.W,
            'width': 15,
            'highlightthickness':0,
            'cursor': 'hand2'
        }

        # Кнопка "Основные настройки"
        settings_button = create_hover_button_for_manager(self.settings_menu, text="Основные настройки",
                                command=self.handle_settings, **menu_button_style)
        settings_button.pack(fill=tk.X)
        settings_button.bind("<Enter>", lambda e: settings_button.config(bg='#1e4a6a'))
        settings_button.bind("<Leave>", lambda e: settings_button.config(bg='#15354D'))

        # Разделитель
        separator = tk.Frame(self.settings_menu, height=1, bg='#1e4a6a')
        separator.pack(fill=tk.X, padx=5, pady=2)

        # Кнопка "Обновление"
        update_button = create_hover_button_for_manager(self.settings_menu, text="Обновление",
                                command=self.handle_update, **menu_button_style)
        update_button.pack(fill=tk.X)
        update_button.bind("<Enter>", lambda e: update_button.config(bg='#1e4a6a'))
        update_button.bind("<Leave>", lambda e: update_button.config(bg='#15354D'))

        # Разделитель
        separator = tk.Frame(self.settings_menu, height=1, bg='#1e4a6a')
        separator.pack(fill=tk.X, padx=5, pady=2)

        # Кнопка "Удалить AdGuard VPN"
        uninstall_button = create_hover_button_for_manager(self.settings_menu, text="Удалить AdGuard VPN",
                                command=self.handle_uninstall, **menu_button_style)
        uninstall_button.pack(fill=tk.X)
        uninstall_button.bind("<Enter>", lambda e: uninstall_button.config(bg='#1e4a6a'))
        uninstall_button.bind("<Leave>", lambda e: uninstall_button.config(bg='#15354D'))

        # Bind событие клика вне меню для закрытия
        self.settings_menu.bind("<FocusOut>", lambda e: self.close_settings_menu())
        self.root.bind("<Button-1>", self.check_close_settings_menu)

    def close_settings_menu(self):
        """Закрывает меню настроек"""
        if hasattr(self, 'settings_menu') and self.settings_menu:
            try:
                self.settings_menu.destroy()
            except:
                pass  # Если окно уже уничтожено
        self.settings_menu_open = False
        try:
            self.root.unbind("<Button-1>")
        except:
            pass

    def check_close_settings_menu(self, event):
        """Проверяет, нужно ли закрыть меню настроек при клике вне его области"""
        if (hasattr(self, 'settings_menu') and self.settings_menu and
            self.settings_menu.winfo_exists()):

            # Проверяем, был ли клик на самом меню или иконке
            menu_widget = event.widget
            while menu_widget:
                if menu_widget == self.settings_menu:
                    return  # Клик внутри меню - не закрываем
                menu_widget = menu_widget.master

            # Если клик был не в меню и не на иконке - закрываем
            if (event.widget != self.settings_icon and
                not self.is_event_in_widget(event, self.settings_icon)):
                self.close_settings_menu()

    def close_all_menus(self):
        """Закрывает все открытые выпадающие меню"""
        if self.account_menu_open:
            self.close_account_menu()
        if hasattr(self, 'settings_menu_open') and self.settings_menu_open:
            self.close_settings_menu()

    def handle_settings(self):
        """Обрабатывает клик по Основные настройки"""
        self.close_settings_menu()
        self.open_settings()

    def handle_update(self):
        """Обрабатывает клик по Обновление"""
        self.close_settings_menu()
        self.check_update()

    def handle_uninstall(self):
        """Обрабатывает клик по Удалить AdGuard VPN"""
        self.close_settings_menu()
        self.uninstall()

    def open_info_link(self, event=None):
        """Открывает ссылку на справку AdGuard VPN"""
        webbrowser.open("https://adguard-vpn.com/kb/ru/")
        self.log_message("🛈︎ Открыта справка AdGuard VPN")

    def open_donate_link(self, event=None):
        """Показывает окно доната"""
        donation_window = DonationWindow(self.root)
        donation_window.run()

    def open_settings(self):
        """Открывает окно настроек"""
        settings_window = SettingsWindow(self.root)
        settings_window.run()

    def update_status(self):
        try:
            result = subprocess.run(
                ['adguardvpn-cli', 'status'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                ansi_escape = re.compile(r'\x1B\[[0-9;]*m')
                clean_text = ansi_escape.sub('', result.stdout)

                is_connected = check_if_connected(clean_text)

                if is_connected:
                    location = clean_location_output(clean_text)
                    if location:
                        self.current_location = location
                        self.status_label.config(text="🟢")
                        self.connect_button.config(text="Отключиться", bg='#ff3b30',
                                                activebackground='#ff3b30')  # Тот же цвет при нажатии
                        self.is_connected = True
                    else:
                        self.current_location = "Подключено"
                        self.status_label.config(text="🟢")
                        self.connect_button.config(text="Отключиться", bg='#ff3b30',
                                                activebackground='#ff3b30')  # Тот же цвет при нажатии
                        self.is_connected = True
                else:
                    self.current_location = ""
                    self.status_label.config(text="🔴")
                    self.connect_button.config(text="Подключиться", bg='#5BA06A',
                                            activebackground='#5BA06A')  # Тот же цвет при нажатии
                    self.is_connected = False
            else:
                self.current_location = ""
                self.status_label.config(text="🔴")
                self.connect_button.config(text="Подключиться", bg='#5BA06A',
                                        activebackground='#5BA06A')  # Тот же цвет при нажатии
                self.is_connected = False
        except Exception as e:
            self.current_location = ""
            self.status_label.config(text="🔴")
            self.connect_button.config(text="Подключиться", bg='#15354D',
                                    activebackground='#15354D')  # Тот же цвет при нажатии
            self.is_connected = False

    def get_user_email(self):
        """Получает email пользователя из информации о лицензии"""
        try:
            result = subprocess.run(
                ['adguardvpn-cli', 'license'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return self.parse_user_email(result.stdout)
            return None
        except:
            return None

    def parse_user_email(self, license_text):
        """Парсит email пользователя из вывода adguardvpn-cli license"""
        try:
            # Очищаем ANSI коды
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean_text = ansi_escape.sub('', license_text)

            lines = clean_text.split('\n')

            for line in lines:
                line_clean = line.strip()

                # Ищем email в строке "Logged in as"
                if "Logged in as" in line_clean:
                    email_match = re.search(r'Logged in as (.+)$', line_clean)
                    if email_match:
                        email = email_match.group(1).strip()
                        # Убираем скобки если есть
                        email = email.replace('(', '').replace(')', '')
                        return email

            return None

        except Exception as e:
            return None

    def update_email_display(self):
        """Обновляет отображение email пользователя и информации о лицензии"""
        if self.is_logged_in:
            email = self.get_user_email()
            license_type = self.get_license_type()

            if email:
                # Сокращаем email для отображения
                if len(email) > 20:
                    display_email = email[:15] + "..."
                else:
                    display_email = email

                # Для Free версии показываем трафик
                if license_type == "Free":
                    traffic = self.get_traffic_left()
                    if traffic:
                        display_text = f"{display_email} ({traffic})"
                    else:
                        display_text = display_email

                # Для Premium версий показываем дни до окончания
                elif license_type in ["Premium"]:
                    expiry_date = self.get_license_expiry()
                    if expiry_date:
                        days_left = self.get_days_until_expiry(expiry_date)
                        if days_left is not None:
                            if days_left == 0:
                                display_text = f"{display_email}\n(Лицензия истекает сегодня)"
                            elif days_left == 1:
                                display_text = f"{display_email}\n(До окончания лицензии остался 1 день)"
                            else:
                                days_text = self.get_days_text(days_left)
                                display_text = f"{display_email}\n(Лицензия истекает через {days_left} {days_text})"
                        else:
                            display_text = f"{display_email}\n(Лицензия действует до {expiry_date})"
                    else:
                        display_text = display_email

                else:
                    display_text = display_email

                # Устанавливаем текст и цвет для авторизованного пользователя
                self.email_label.config(text=display_text, fg='#5BA06A')
            else:
                self.email_label.config(text="Авторизован", fg='#5BA06A')
        else:
            # Для неавторизованного пользователя
            self.email_label.config(text="Не авторизован", fg='#8e8e93')

    def get_traffic_left(self):
        """Получает оставшийся трафик из информации о лицензии"""
        try:
            result = subprocess.run(
                ['adguardvpn-cli', 'license'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return self.parse_traffic_left(result.stdout)
            return None
        except:
            return None

    def parse_traffic_left(self, license_text):
        """Парсит оставшийся трафик из вывода adguardvpn-cli license"""
        try:
            # Очищаем ANSI коды
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean_text = ansi_escape.sub('', license_text)

            lines = clean_text.split('\n')

            for line in lines:
                line_clean = line.strip()

                # Ищем оставшийся трафик в разных форматах
                if "GB left" in line_clean or "MB left" in line_clean:
                    # Паттерн для "You have X.XX GB left" или подобных
                    traffic_match = re.search(r'(\d+\.?\d*)\s*(GB|MB)\s*left', line_clean, re.IGNORECASE)
                    if traffic_match:
                        amount = traffic_match.group(1)
                        unit = traffic_match.group(2)
                        return f"{amount} {unit}"

                # Альтернативный паттерн
                if "left" in line_clean.lower():
                    traffic_match = re.search(r'(\d+\.?\d*)\s*(GB|MB)', line_clean, re.IGNORECASE)
                    if traffic_match:
                        amount = traffic_match.group(1)
                        unit = traffic_match.group(2)
                        return f"{amount} {unit}"

            return None

        except Exception as e:
            return None

    def get_license_type(self):
        """Получает тип лицензии"""
        try:
            result = subprocess.run(
                ['adguardvpn-cli', 'license'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                license_type = self.parse_license_type(result.stdout)

                # Дополнительная проверка: если есть дата окончания - это не Free
                expiry_date = self.parse_license_expiry(result.stdout)
                if expiry_date and license_type == "Free":
                    return "Premium"

                return license_type
            return "Неизвестно"
        except:
            return "Неизвестно"

    def parse_license_type(self, license_text):
        """Парсит тип лицензии из вывода adguardvpn-cli license"""
        try:
            # Очищаем ANSI коды
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean_text = ansi_escape.sub('', license_text)

            lines = clean_text.split('\n')

            for line in lines:
                line_clean = line.strip()

                # Ищем тип лицензии
                if "FREE version" in line_clean:
                    return "Free"
                elif "PREMIUM" in line_clean.upper():
                    return "Premium"

            # Если не нашли явного указания, считаем Free
            return "Free"

        except Exception as e:
            return "Неизвестно"

    def parse_license_info(self, license_text):
        """Парсит информацию о лицензии из вывода adguardvpn-cli license"""
        try:
            # Очищаем ANSI коды
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean_text = ansi_escape.sub('', license_text)

            lines = clean_text.split('\n')
            license_type = "Неизвестно"
            devices = ""
            traffic_left = ""
            email = ""

            for line in lines:
                line_clean = line.strip()

                # Ищем тип лицензии
                if "FREE version" in line_clean:
                    license_type = "Free"
                elif "PREMIUM" in line_clean.upper():
                    license_type = "Premium"

                # Ищем информацию об устройствах
                if "devices simultaneously" in line_clean:
                    devices_match = re.search(r'Up to (\d+) devices', line_clean)
                    if devices_match:
                        devices = f", {devices_match.group(1)} устройств"

                # Ищем оставшийся трафик
                if "GB left" in line_clean or "MB left" in line_clean:
                    traffic_match = re.search(r'(\d+\.?\d*)\s*(GB|MB)\s*left', line_clean)
                    if traffic_match:
                        traffic_left = f", {traffic_match.group(1)} {traffic_match.group(2)}"

                # Ищем email
                if "Logged in as" in line_clean:
                    email_match = re.search(r'Logged in as (.+)$', line_clean)
                    if email_match:
                        email = email_match.group(1)
                        # Сокращаем email для отображения
                        if len(email) > 20:
                            email = email[:15] + "..."
                        email = f" ({email})"

            # Формируем финальную строку
            if license_type != "Неизвестно":
                return f"Лицензия: {license_type}{devices}{traffic_left}{email}"
            else:
                # Если не нашли явного указания типа, но есть другие данные
                if devices or traffic_left:
                    return f"Лицензия: Free{devices}{traffic_left}{email}"
                else:
                    return "Лицензия: Free"

        except Exception as e:
            return "Лицензия: Ошибка парсинга"


    def get_license_expiry(self):
        """Получает дату окончания лицензии"""
        try:
            result = subprocess.run(
                ['adguardvpn-cli', 'license'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return self.parse_license_expiry(result.stdout)
            return None
        except:
            return None

    def parse_license_expiry(self, license_text):
        """Парсит дату окончания лицензии из вывода adguardvpn-cli license"""
        try:
            # Очищаем ANSI коды
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean_text = ansi_escape.sub('', license_text)

            lines = clean_text.split('\n')

            for line in lines:
                line_clean = line.strip()

                # Ищем дату окончания в разных форматах
                if "subscription will be renewed on" in line_clean:
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', line_clean)
                    if date_match:
                        return date_match.group(1)

                # Альтернативные форматы
                elif "expires on" in line_clean.lower():
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', line_clean)
                    if date_match:
                        return date_match.group(1)

                elif "valid until" in line_clean.lower():
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', line_clean)
                    if date_match:
                        return date_match.group(1)

            return None

        except Exception as e:
            return None

    def get_days_text(self, days):
        """Возвращает правильное склонение слова 'день' в зависимости от числа"""
        if days % 10 == 1 and days % 100 != 11:
            return "день"
        elif days % 10 in [2, 3, 4] and days % 100 not in [12, 13, 14]:
            return "дня"
        else:
            return "дней"

    def get_days_until_expiry(self, expiry_date_str):
        """Рассчитывает количество дней до окончания лицензии"""
        try:
            from datetime import datetime, date

            # Парсим дату окончания
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()

            # Получаем текущую дату
            current_date = date.today()

            # Рассчитываем разницу в днях
            days_left = (expiry_date - current_date).days + 1

            return max(0, days_left)  # Возвращаем 0 если лицензия уже истекла

        except Exception as e:
            return None

    def update_ui_for_auth_status(self):
        """Обновляет состояние UI в зависимости от статуса авторизации"""
        if self.is_logged_in:
            # Разблокировать кнопки
            self.connect_button.config(state=tk.NORMAL, bg='#15354D')
            # Найти кнопку "Выбрать локацию" (вторая кнопка в left_panel)
            for widget in self.connect_button.master.winfo_children():
                if isinstance(widget, tk.Button) and widget.cget('text') == "Выбрать локацию":
                    widget.config(state=tk.NORMAL, bg='#15354D')
                    break
        else:
            # Заблокировать кнопки
            self.connect_button.config(state=tk.DISABLED, bg='#2a4d6a')
            # Найти кнопку "Выбрать локацию"
            for widget in self.connect_button.master.winfo_children():
                if isinstance(widget, tk.Button) and widget.cget('text') == "Выбрать локацию":
                    widget.config(state=tk.DISABLED, bg='#2a4d6a')
                    break

    def schedule_status_update(self):
        """Периодически обновляет статус"""
        self.update_status()

        # Обновляем email и трафик каждые 30 секунд
        static_info_counter = getattr(self, '_static_info_counter', 0) + 1
        self._static_info_counter = static_info_counter

        if static_info_counter >= 10:  # 30 секунд (10 * 3 секунды)
            self.update_email_display()  # Теперь обновляет и email и трафик
            self._static_info_counter = 0

        self.root.after(3000, self.schedule_status_update)

    def check_connection_status(self):
        """Проверяет статус подключения и возвращает True если подключен"""
        try:
            result = subprocess.run(
                ['adguardvpn-cli', 'status'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                status_text = result.stdout.strip()
                connected = check_if_connected(status_text)

                if connected:
                    location = clean_location_output(status_text)
                    if location:
                        self.current_location = location
                    else:
                        detailed_location = self.get_current_location()
                        if detailed_location:
                            self.current_location = detailed_location
                        else:
                            self.current_location = "🟢"
                    return True
                else:
                    self.current_location = ""
                    return False

            result = subprocess.run(
                ['adguardvpn-cli', 'list-locations'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                current_location = self.get_current_location()
                if current_location:
                    self.current_location = current_location
                else:
                    self.current_location = "🟢"
                return True

            return False

        except Exception as e:
            self.current_location = ""
            return False

    def get_current_location(self):
        """Получает текущую локацию через детальную команду"""
        try:
            result = subprocess.run(
                ['adguardvpn-cli', 'status', '--verbose'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                output = result.stdout
                location_patterns = [
                    r'Location:\s*(.+)',
                    r'Server:\s*(.+)',
                    r'Endpoint:\s*(.+)',
                    r'Connected to:\s*(.+)'
                ]

                for pattern in location_patterns:
                    match = re.search(pattern, output, re.IGNORECASE)
                    if match:
                        location = match.group(1).strip()
                        return location

            result = subprocess.run(
                ['adguardvpn-cli', 'status'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                text = result.stdout
                if 'connected to' in text.lower():
                    parts = text.split()
                    for i, part in enumerate(parts):
                        if part.lower() == 'connected' and i + 2 < len(parts) and parts[i + 1].lower() == 'to':
                            location = parts[i + 2]
                            return location

            return None

        except Exception as e:
            return None

    def connect_vpn(self):
        """Подключается к VPN через внешнюю консоль"""
        if self.is_connected:
            self.disconnect_vpn()
            return

        # Запускаем в отдельном потоке, чтобы GUI не блокировался
        thread = threading.Thread(target=self._connect_vpn_thread)
        thread.daemon = True
        thread.start()

    def _connect_vpn_thread(self):
        self.log_message("🔗 Запуск подключения в терминале...")
        try:
            # Запускаем подключение в отдельном терминале (konsole для KDE)
            command = 'konsole -e bash -c "(echo y; echo y; echo y) | adguardvpn-cli connect && echo Успешно подключено, терминал автоматически закроется! && sleep 1 || echo Ошибка подключения && sleep 2"'

            process = subprocess.Popen(
                command,
                shell=True
            )

            time.sleep(10)

            # Проверяем статус подключения
            max_attempts = 5
            for attempt in range(max_attempts):
                self.log_message(f"🔍 Проверка подключения... ({attempt + 1}/{max_attempts})")

                if self.check_connection_status():
                    current_location = self.get_current_location()
                    location_text = f" к {current_location}" if current_location else ""
                    self.log_message(f"✅ VPN успешно подключен!")
                    return

                time.sleep(3)
                self.update_status()

            self.log_message("⚠️ Проверьте терминал - возможно требуется дополнительное время")

        except Exception as e:
            self.log_message(f"❌ Ошибка при запуске подключения: {str(e)}")

    def select_location(self):
        """Подключение к выбранной локации через внешнюю консоль"""
        location_window = LocationSelectionWindow(self.root)
        selected_location = location_window.run()

        if not selected_location:
            return

        # Запускаем в отдельном потоке
        thread = threading.Thread(target=self._select_location_thread, args=(selected_location,))
        thread.daemon = True
        thread.start()

    def _select_location_thread(self, selected_location):
        """Поток для подключения к выбранной локации с автоматическими ответами"""
        try:
            self.log_message(f"🔗 Подключение к {selected_location} через терминал...")

            # Запускаем подключение к конкретной локации в терминале
            command = f'konsole -e bash -c "(echo y; echo y; echo y) | adguardvpn-cli connect -l \\"{selected_location}\\" && echo Успешно подключено, терминал автоматически закроется! && sleep 3 || echo Ошибка подключения && sleep 5"'

            process = subprocess.Popen(
                command,
                shell=True
            )

            time.sleep(10)

            # Проверяем статус
            max_attempts = 5
            connected = False

            for attempt in range(max_attempts):
                self.update_status()
                if self.check_connection_status():
                    connected = True
                    break
                time.sleep(3)

            if connected:
                current_location = self.get_current_location()
                display_location = current_location if current_location else selected_location
                self.log_message(f"✅ VPN успешно подключен!")
            else:
                time.sleep(2)
                self.update_status()

        except Exception as e:
            self.log_message(f"❌ Ошибка при подключении: {str(e)}")

    def check_update(self):
        """Открывает окно проверки обновлений"""
        update_window = UpdateWindow(self.root)
        update_window.run()

    def check_license(self):
        """Проверка лицензии"""
        self.close_account_menu()
        license_window = LicenseWindow(self.root)
        license_window.run()

    def disconnect_vpn(self):
        """Отключает VPN"""
        try:
            self.log_message("🔒 Отключение VPN...")

            # Простая команда без терминала - как в старой версии
            result = subprocess.run(
                ['adguardvpn-cli', 'disconnect'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                self.log_message("✅ VPN отключен")
                self.update_status()
            else:
                self.log_message("❌ Не удалось отключить VPN")

        except Exception as e:
            self.log_message(f"❌ Ошибка при отключении: {str(e)}")

    def logout(self):
        """Выход из аккаунта"""
        if show_question_dialog(self.root, "Подтверждение", "Вы уверены, что хотите выйти из аккаунта?"):
            # Запускаем выход в отдельном потоке
            thread = threading.Thread(target=self._logout_thread)
            thread.daemon = True
            thread.start()

    def _logout_thread(self):
        """Поток для обработки выхода из аккаунта"""
        try:
            self.log_message("🚪 Выход из аккаунта...")

            # Отключаем VPN перед выходом из аккаунта
            if self.is_connected:
                self.disconnect_vpn()
                time.sleep(2)

            # Выходим из аккаунта
            result = subprocess.run(
                ['adguardvpn-cli', 'logout'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                self.root.after(0, self._logout_success)
            else:
                self.root.after(0, self._logout_failed)

        except Exception as e:
            self.root.after(0, lambda: self._logout_error(str(e)))

    def _logout_success(self):
        """Обновляет GUI после успешного выхода"""
        self.is_logged_in = False
        self.update_email_display()
        self.update_ui_for_auth_status()
        self.log_message("✅ Успешный выход из аккаунт")

        # Сбрасываем состояние интерфейса
        self.current_location = ""
        self.status_label.config(text="🔴", fg='#ff3b30')
        self.connect_button.config(text="Подключиться", bg='#2a4d6a', state=tk.DISABLED)

    def _logout_failed(self):
        """Обновляет GUI после неудачного выхода"""
        self.log_message("❌ Не удалось выйти из аккаунта")

    def _logout_error(self, error_msg):
        """Обновляет GUI при ошибке выхода"""
        self.log_message(f"❌ Ошибка при выходе: {error_msg}")

    def toggle_auth(self):
        """Единый обработчик для входа/выхода из аккаунта"""
        if self.is_logged_in:
            self.logout()
        else:
            # Запускаем авторизацию в отдельном потоке
            thread = threading.Thread(target=self._login_thread)
            thread.daemon = True
            thread.start()

    def _login_thread(self):
        """Поток для обработки авторизации"""
        try:
            # Создаем окно авторизации в этом потоке
            auth_window = ManagerAuthWindow(self.root)
            auth_success = auth_window.run()

            if auth_success:
                # Обновляем GUI в основном потоке
                self.root.after(0, self._login_success)
            else:
                self.root.after(0, self._login_failed)

        except Exception as e:
            self.root.after(0, lambda: self._login_error(str(e)))

    def _login_success(self):
        """Обновляет GUI после успешной авторизации"""
        self.is_logged_in = True
        self.update_email_display()
        self.update_ui_for_auth_status()
        self.log_message("✅ Успешный вход в аккаунт")

    def _login_failed(self):
        """Обновляет GUI после неудачной авторизации"""
        self.log_message("❌ Авторизация не удалась")

    def _login_error(self, error_msg):
        """Обновляет GUI при ошибке авторизации"""
        self.log_message(f"❌ Ошибка авторизации: {error_msg}")

    def uninstall(self):
        """Удаление AdGuard VPN"""
        uninstall_window = UninstallWindow(self.root)
        uninstall_window.run()

    def close_app(self):
        """Закрывает приложение"""
        self.close_all_menus()
        sys.exit()

    def run(self):
        self.root.mainloop()
