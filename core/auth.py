import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import re
import os
import time
import webbrowser
import sys
from ui.components.button_styler import create_hover_button, apply_hover_effect

class SudoAuthWindow:
    """Окно авторизации через sudo"""
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window_properties()
        self.root.title("Аутентификация")
        self.root.geometry("260x290")
        self.root.configure(bg='#182030')

        try:
            from tkinter import ttk
            style = ttk.Style()
            style.theme_use('clam')  # или 'alt', 'classic' - простые темы
        except:
            pass

        self.sudo_password = None
        self.auth_success = False
        self.setup_ui()

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

        title_label = tk.Label(main_frame, text="Аутентификация",
                              font=("Arial", 16, "bold"), fg='white', bg='#182030')
        title_label.pack(pady=10)

        desc_label = tk.Label(main_frame,
                             text="Для установки AdGuard VPN\nтребуется права администратора",
                             font=("Arial", 10), fg='white', bg='#182030')
        desc_label.pack(pady=5)

        sudo_frame = tk.Frame(main_frame, bg='#182030')
        sudo_frame.pack(fill=tk.X, pady=10)

        tk.Label(sudo_frame, text="Введите пароль:",
                fg='white', bg='#182030').pack(anchor=tk.W)

        self.sudo_entry = tk.Entry(sudo_frame, show="*", width=40, font=('Arial', 12),
                                  bg='#15354D', fg='white', insertbackground='white')
        self.sudo_entry.pack(fill=tk.X, pady=5)
        self.sudo_entry.bind('<Return>', self.verify_sudo)
        self.sudo_entry.focus()

        btn_frame = tk.Frame(main_frame, bg='#182030')
        btn_frame.pack(fill=tk.X, pady=5)

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

        continue_btn = create_hover_button(btn_frame, text="Продолжить",
                                           command=self.verify_sudo, **button_style)
        continue_btn.grid(row=0, column=0, padx=(0, 10))

        cancel_btn = create_hover_button(btn_frame, text="Отмена",
                                         command=self.cancel, **button_style)
        cancel_btn.grid(row=0, column=1)

        # Центрируем весь фрейм с кнопками
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        self.status_var = tk.StringVar(value="Введите пароль")
        status_bar = tk.Label(main_frame, textvariable=self.status_var,
                             relief=tk.SUNKEN, anchor=tk.W, bg='#15354D', fg='white')
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

    def verify_sudo(self, event=None):
        password = self.sudo_entry.get()
        if not password:
            self.status_var.set("❗Sudo пароль не введен")
            return

        self.status_var.set("🔐 Проверка пароля...")
        self.sudo_entry.config(state='disabled')

        thread = threading.Thread(target=self._verify_sudo_thread, args=(password,))
        thread.daemon = True
        thread.start()

    def _verify_sudo_thread(self, password):
        try:
            process = subprocess.Popen(
                ['sudo', '-S', 'echo', 'success'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            output, error = process.communicate(input=password + '\n')

            if process.returncode == 0:
                self.sudo_password = password
                self.auth_success = True
                self.root.after(0, self._sudo_verified_success)
            else:
                self.root.after(0, lambda: self._sudo_verified_fail("❌ Неверный пароль"))

        except Exception as e:
            self.root.after(0, lambda: self._sudo_verified_fail(f"Ошибка: {str(e)}"))

    def _sudo_verified_success(self):
        self.status_var.set("✅ Пароль подтвержден!")
        self.root.after(1000, self.close_and_proceed)

    def _sudo_verified_fail(self, error_msg):
        self.status_var.set(error_msg)
        self.sudo_entry.config(state='normal')
        self.sudo_entry.delete(0, tk.END)
        self.sudo_entry.focus()

    def close_and_proceed(self):
        self.root.destroy()

    def cancel(self):
        self.sudo_password = None
        self.auth_success = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        return self.sudo_password, self.auth_success

class AuthWindow:
    """Окно авторизации после установки"""
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window_properties()
        self.root.title("AdGuard VPN - Авторизация")

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
        base_width = 425
        base_height = 320

        # --- Учёт ориентации ---
        if screen_height > screen_width:
            # Портретная ориентация (например, у Steam Deck)
            screen_width, screen_height = screen_height, screen_width

        # --- Подстройка под Steam Deck / SteamOS ---
        if is_steamdeck():
            # На Steam Deck — чуть меньше, чтобы влезало в экран даже с рамкой
            width = min(base_width + 20, screen_width + 20)
            height = min(base_height + 40, screen_height + 40)
            # Без центрирования (иначе Wayland игнорирует позицию)
            self.root.geometry(f"{int(width)}x{int(height)}")
        else:
            # На обычных системах (CachyOS, Windows, etc.)
            width = base_width
            height = base_height
            self.root.geometry(f"{width}x{height}")

        self.root.configure(bg='#182030')

        try:
            from tkinter import ttk
            style = ttk.Style()
            style.theme_use('clam')
        except:
            pass

        self.auth_success = False
        self.auth_url = None
        self.monitoring = False
        self.current_countdown = 20
        self.check_count = 0
        self.countdown_running = False
        self.setup_ui()

    def setup_window_properties(self):
        """Настройка свойств окна для корректного отображения"""
        self.root.title("AdGuard VPN Manager")

        try:
            self.root.wm_class("AdGuardVPNManager")
        except:
            pass

        try:
            manager_dir = os.path.expanduser("~/AdGuard VPN Manager")
            icon_path = os.path.join(manager_dir, "ico/adguard.png")
            if os.path.exists(icon_path):
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
        except Exception as e:
            print(f"Не удалось установить иконку: {e}")

    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg='#182030', padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = tk.Label(main_frame, text="AdGuard VPN - Авторизация",
                              font=("Arial", 16, "bold"), fg='white', bg='#182030')
        title_label.pack(pady=10)

        # Фрейм для ссылки
        self.url_frame = tk.Frame(main_frame, bg='#182030')
        self.url_frame.pack(fill=tk.X, pady=10)

        self.url_label = tk.Label(self.url_frame, text="", font=("Arial", 9),
                                 wraplength=400, justify=tk.LEFT,
                                 fg='#0a84ff', bg='#182030', cursor="hand2")
        self.url_label.pack(pady=5)

        # Фрейм для инструкций
        instructions_frame = tk.Frame(main_frame, bg='#182030')
        instructions_frame.pack(fill=tk.X, pady=10)

        instructions_text = (
            "1. Нажмите 'Открыть в браузере' для автоматического открытия\n"
            "2. Следуйте инструкциям на сайте\n"
            "3. Дождитесь завершения авторизации\n"
            "4. Для ускоренной проверки нажмите 'Проверить сейчас'"
        )
        tk.Label(instructions_frame, text=instructions_text, font=("Arial", 9),
                fg='white', bg='#182030', justify=tk.LEFT).pack(anchor=tk.W)

        # Кнопки основного действия
        btn_frame = tk.Frame(main_frame, bg='#182030')
        btn_frame.pack(pady=10)

        button_style = {
            'font': ('Arial', 10),
            'bg': '#15354D',
            'fg': 'white',
            'bd': 0,
            'padx': 10,
            'pady': 5,
            'width': 20,
            'highlightthickness':0,
            'cursor': 'hand2'
        }

        self.browser_btn = create_hover_button(btn_frame, text="Открыть в браузере",
                                    command=self.open_auth_browser, **button_style)
        self.browser_btn.grid(row=0, column=0, padx=(0, 10))

        exit_btn = create_hover_button(btn_frame, text="Выход",
                                       command=self.close_app, **button_style)
        exit_btn.grid(row=0, column=1)

        # Центрируем основной фрейм с кнопками
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        # Кнопка для ускоренной проверки
        self.check_now_btn = create_hover_button(main_frame, text="🔄 Проверить сейчас", command=self.force_check_auth, ** button_style)
        self.check_now_btn.pack(pady=5)
        self.check_now_btn.config(state='disabled')  # Изначально неактивна

        # Статус
        self.status_var = tk.StringVar(value="Нажмите кнопку для получения ссылки")
        status_bar = tk.Label(main_frame, textvariable=self.status_var,
                             relief=tk.SUNKEN, anchor=tk.W, bg='#15354D', fg='white')
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

        # Изначально скрываем кнопки до получения ссылки
        self.browser_btn.config(state='disabled')

    def close_app(self):
        self.monitoring = False
        sys.exit()

    def get_auth_url(self):
        """Получает ссылку для авторизации из команды adguardvpn-cli login"""
        try:
            self.status_var.set("Получение ссылки для авторизации...")

            process = subprocess.Popen(
                ['adguardvpn-cli', 'login'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            time.sleep(2)

            auth_url = None
            output_text = ""

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    output_text += line
                    url_match = re.search(r'https://[^\s]+', line)
                    if url_match:
                        auth_url = url_match.group(0)
                        break

            if not auth_url:
                error_output = process.stderr.read()
                url_match = re.search(r'https://[^\s]+', error_output)
                if url_match:
                    auth_url = url_match.group(0)

            if auth_url:
                self.auth_url = auth_url
                return auth_url
            else:
                return None

        except Exception as e:
            return None

    def open_auth_browser(self):
        if not self.auth_url:
            return

        self.status_var.set("Открываю браузер...")
        webbrowser.open(self.auth_url)

        self.status_var.set("Проверка авторизации")
        self.browser_btn.config(state='disabled')
        self.check_now_btn.config(state='normal')  # Активируем кнопку проверки

        # Запускаем мониторинг статуса авторизации
        self.monitoring = True
        thread = threading.Thread(target=self._monitor_auth_status)
        thread.daemon = True
        thread.start()

    def force_check_auth(self):
        """Принудительная проверка статуса авторизации"""
        if not self.monitoring:
            return

        self.status_var.set("⏩ Принудительная проверка...")
        self.check_now_btn.config(state='disabled')  # Временно отключаем кнопку

        # Прерываем текущий обратный отсчет
        self.countdown_running = False

        # Запускаем проверку в отдельном потоке
        thread = threading.Thread(target=self._perform_auth_check)
        thread.daemon = True
        thread.start()

    def _perform_auth_check(self):
        """Выполняет проверку статуса авторизации"""
        try:
            result = subprocess.run(
                ['adguardvpn-cli', 'list-locations'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                self.auth_success = True
                self.root.after(0, self._auth_success)
            else:
                self.root.after(0, self._check_failed)

        except Exception as e:
            self.root.after(0, lambda: self._check_failed(f"Ошибка: {str(e)}"))

    def _check_failed(self, error_msg=None):
        """Обработка неудачной проверки"""
        if error_msg:
            self.status_var.set(f"❌ {error_msg}")
        else:
            self.status_var.set("❌ Авторизация еще не завершена")

        # Через 3 секунды возвращаем к обычному циклу
        self.root.after(3000, self._resume_normal_check)

    def _resume_normal_check(self):
        """Возобновление обычного цикла проверки"""
        if self.monitoring:
            self.status_var.set("Возобновление автоматической проверки...")
            self.check_now_btn.config(state='normal')
            # Следующая проверка начнется автоматически в основном цикле

    def copy_auth_url(self):
        """Копирует ссылку авторизации в буфер обмена"""
        if self.auth_url:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.auth_url)
            self.status_var.set("Ссылка скопирована в буфер обмена!")

    def start_auth_process(self):
        """Начинает процесс авторизации"""
        thread = threading.Thread(target=self._start_auth_thread)
        thread.daemon = True
        thread.start()

    def _start_auth_thread(self):
        """Поток для получения ссылки авторизации"""
        auth_url = self.get_auth_url()

        if auth_url:
            self.root.after(0, lambda: self._show_auth_url(auth_url))
        else:
            self.root.after(0, lambda: self._auth_fail("❌ Не удалось получить ссылку для авторизации"))

    def _show_auth_url(self, auth_url):
        """Показывает полученную ссылку в интерфейсе"""
        display_url = auth_url
        if len(display_url) > 60:
            display_url = display_url[:60] + "..."

        self.url_label.config(text=display_url)
        self.status_var.set("✅ Ссылка получена! Нажмите 'Открыть в браузере'")

        self.browser_btn.config(state='normal')

    def _monitor_auth_status(self):
        """Мониторит статус авторизации с цикличной проверкой каждые 20 секунд"""
        self.check_count = 0

        while self.monitoring:
            try:
                self.check_count += 1
                self.countdown_running = True

                # Показываем обратный отсчет 20 секунд
                for countdown in range(20, 0, -1):
                    if not self.monitoring:
                        return
                    if not self.countdown_running:
                        break  # Прерываем отсчет если была принудительная проверка

                    self.current_countdown = countdown
                    self.root.after(0, lambda c=countdown: self.status_var.set(
                        f"Проверка авторизации через: {c} сек (попытка #{self.check_count})"
                    ))
                    time.sleep(1)

                # Если отсчет не был прерван, выполняем проверку
                if self.countdown_running:
                    self._perform_auth_check()

                # Сбрасываем флаг для следующего цикла
                self.countdown_running = True

                # Небольшая пауза перед следующим циклом
                time.sleep(1)

            except Exception as e:
                # При ошибке продолжаем цикл
                self.root.after(0, lambda: self.status_var.set(
                    f"Ошибка проверки, повтор через 20 сек (попытка #{self.check_count})"
                ))
                self.countdown_running = True
                continue

    def _auth_success(self):
        """Успешная авторизация"""
        self.monitoring = False
        self.countdown_running = False
        self.status_var.set("✅ Авторизация успешна!")
        self.auth_success = True
        self.check_now_btn.config(state='disabled')
        self.root.after(2000, self.root.destroy)

    def _auth_fail(self, error_msg):
        self.browser_btn.config(state='normal')
        self.check_now_btn.config(state='disabled')
        self.status_var.set("Ошибка авторизации")

    def show_custom_question(self, title, message):
        """Показывает кастомный вопрос с Yes/No"""
        from ui.components.dialogs import show_question_dialog
        return show_question_dialog(self.root, title, message)

    def run(self):
        self.start_auth_process()
        self.root.mainloop()
        return self.auth_success

class ManagerAuthWindow:
    """Окно авторизации через менеджер"""
    def __init__(self, parent):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.setup_window_properties()
        self.root.title("AdGuard VPN - Авторизация")

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
        base_width = 425
        base_height = 320

        # --- Учёт ориентации ---
        if screen_height > screen_width:
            # Портретная ориентация (например, у Steam Deck)
            screen_width, screen_height = screen_height, screen_width

        # --- Подстройка под Steam Deck / SteamOS ---
        if is_steamdeck():
            # На Steam Deck — чуть меньше, чтобы влезало в экран даже с рамкой
            width = min(base_width + 20, screen_width + 20)
            height = min(base_height + 40, screen_height + 40)
            # Без центрирования (иначе Wayland игнорирует позицию)
            self.root.geometry(f"{int(width)}x{int(height)}")
        else:
            # На обычных системах (CachyOS, Windows, etc.)
            width = base_width
            height = base_height
            self.root.geometry(f"{width}x{height}")

        self.root.configure(bg='#182030')

        # Явно позиционируем относительно родительского окна
        self.root.transient(parent)  # Связываем с родителем
        self.root.grab_set()         # Делаем модальным

        try:
            from tkinter import ttk
            style = ttk.Style()
            style.theme_use('clam')
        except:
            pass

        self.auth_success = False
        self.auth_url = None
        self.monitoring = False
        self.current_countdown = 20
        self.check_count = 0
        self.countdown_running = False
        self.setup_ui()

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

        title_label = tk.Label(main_frame, text="AdGuard VPN - Авторизация",
                              font=("Arial", 16, "bold"), fg='white', bg='#182030')
        title_label.pack(pady=10)

        # Фрейм для ссылки
        self.url_frame = tk.Frame(main_frame, bg='#182030')
        self.url_frame.pack(fill=tk.X, pady=10)

        self.url_label = tk.Label(self.url_frame, text="", font=("Arial", 9),
                                 wraplength=400, justify=tk.LEFT,
                                 fg='#0a84ff', bg='#182030', cursor="hand2")
        self.url_label.pack(pady=5)

        # Фрейм для инструкций
        instructions_frame = tk.Frame(main_frame, bg='#182030')
        instructions_frame.pack(fill=tk.X, pady=10)

        instructions_text = (
            "1. Нажмите 'Открыть в браузере' для автоматического открытия\n"
            "2. Следуйте инструкциям на сайте\n"
            "3. Дождитесь завершения авторизации\n"
            "4. Для ускоренной проверки нажмите 'Проверить сейчас'"
        )
        tk.Label(instructions_frame, text=instructions_text, font=("Arial", 9),
                fg='white', bg='#182030', justify=tk.LEFT).pack(anchor=tk.W)

        # Кнопки основного действия
        btn_frame = tk.Frame(main_frame, bg='#182030')
        btn_frame.pack(pady=10)

        button_style = {
            'font': ('Arial', 10),
            'bg': '#15354D',
            'fg': 'white',
            'bd': 0,
            'padx': 10,
            'pady': 5,
            'width': 20,
            'highlightthickness':0,
            'cursor': 'hand2'
        }

        self.browser_btn = create_hover_button(btn_frame, text="Открыть в браузере",
                                    command=self.open_auth_browser, **button_style)
        self.browser_btn.grid(row=0, column=0, padx=(0, 10))

        self.cancel_btn = create_hover_button(btn_frame, text="Отмена",
                                              command=self.cancel, **button_style)
        self.cancel_btn.grid(row=0, column=1)

        # Центрируем основной фрейм с кнопками
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        # Кнопка для ускоренной проверки
        self.check_now_btn = create_hover_button(main_frame, text="🔄 Проверить сейчас", command=self.force_check_auth, ** button_style)
        self.check_now_btn.pack(pady=5)
        self.check_now_btn.config(state='disabled')

        # Статус
        self.status_var = tk.StringVar(value="Получение ссылки для авторизации...")
        status_bar = tk.Label(main_frame, textvariable=self.status_var,
                             relief=tk.SUNKEN, anchor=tk.W, bg='#15354D', fg='white')
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

        # Изначально скрываем кнопки до получения ссылки
        self.browser_btn.config(state='disabled')

    def cancel(self):
        """Закрывает окно авторизации"""
        self.monitoring = False
        self.countdown_running = False
        self.auth_success = False
        self.root.destroy()

    def get_auth_url(self):
        """Получает ссылку для авторизации из команды adguardvpn-cli login"""
        try:
            self.status_var.set("Получение ссылки для авторизации...")

            process = subprocess.Popen(
                ['adguardvpn-cli', 'login'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            time.sleep(2)

            auth_url = None
            output_text = ""

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    output_text += line
                    url_match = re.search(r'https://[^\s]+', line)
                    if url_match:
                        auth_url = url_match.group(0)
                        break

            if not auth_url:
                error_output = process.stderr.read()
                url_match = re.search(r'https://[^\s]+', error_output)
                if url_match:
                    auth_url = url_match.group(0)

            if auth_url:
                self.auth_url = auth_url
                return auth_url
            else:
                return None

        except Exception as e:
            return None

    def open_auth_browser(self):
        """Открывает ссылку авторизации в браузере и запускает мониторинг статуса"""
        if not self.auth_url:
            return

        self.status_var.set("Открываю браузер...")
        webbrowser.open(self.auth_url)

        self.status_var.set("Ожидание авторизации...")
        self.browser_btn.config(state='disabled')
        self.cancel_btn.config(state='disabled')
        self.check_now_btn.config(state='normal')  # Активируем кнопку проверки

        # Запускаем мониторинг статуса авторизации
        self.monitoring = True
        thread = threading.Thread(target=self._monitor_auth_status)
        thread.daemon = True
        thread.start()

    def force_check_auth(self):
        """Принудительная проверка статуса авторизации"""
        if not self.monitoring:
            return

        self.status_var.set("⏩ Принудительная проверка...")
        self.check_now_btn.config(state='disabled')  # Временно отключаем кнопку

        # Прерываем текущий обратный отсчет
        self.countdown_running = False

        # Запускаем проверку в отдельном потоке
        thread = threading.Thread(target=self._perform_auth_check)
        thread.daemon = True
        thread.start()

    def _perform_auth_check(self):
        """Выполняет проверку статуса авторизации"""
        try:
            result = subprocess.run(
                ['adguardvpn-cli', 'list-locations'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                self.auth_success = True
                self.root.after(0, self._auth_success)
            else:
                self.root.after(0, self._check_failed)

        except Exception as e:
            self.root.after(0, lambda: self._check_failed(f"Ошибка: {str(e)}"))

    def _check_failed(self, error_msg=None):
        """Обработка неудачной проверки"""
        if error_msg:
            self.status_var.set(f"❌ {error_msg}")
        else:
            self.status_var.set("❌ Авторизация еще не завершена")

        # Через 3 секунды возвращаем к обычному циклу
        self.root.after(3000, self._resume_normal_check)

    def _resume_normal_check(self):
        """Возобновление обычного цикла проверки"""
        if self.monitoring:
            self.status_var.set("Возобновление автоматической проверки...")
            self.check_now_btn.config(state='normal')
            # Следующая проверка начнется автоматически в основном цикле

    def _monitor_auth_status(self):
        """Мониторит статус авторизации с цикличной проверкой каждые 20 секунд"""
        self.check_count = 0

        while self.monitoring:
            try:
                self.check_count += 1
                self.countdown_running = True

                # Показываем обратный отсчет 20 секунд
                for countdown in range(20, 0, -1):
                    if not self.monitoring:
                        return
                    if not self.countdown_running:
                        break  # Прерываем отсчет если была принудительная проверка

                    self.current_countdown = countdown
                    self.root.after(0, lambda c=countdown: self.status_var.set(
                        f"Проверка авторизации через: {c} сек (попытка #{self.check_count})"
                    ))
                    time.sleep(1)

                # Если отсчет не был прерван, выполняем проверку
                if self.countdown_running:
                    self._perform_auth_check()

                # Сбрасываем флаг для следующего цикла
                self.countdown_running = True

                # Небольшая пауза перед следующим циклом
                time.sleep(1)

            except Exception as e:
                # При ошибке продолжаем цикл
                self.root.after(0, lambda: self.status_var.set(
                    f"Ошибка проверки, повтор через 20 сек (попытка #{self.check_count})"
                ))
                self.countdown_running = True
                continue

    def _auth_success(self):
        """Успешная авторизация"""
        self.monitoring = False
        self.countdown_running = False
        self.status_var.set("✅ Авторизация успешна!")
        self.auth_success = True
        self.check_now_btn.config(state='disabled')
        self.root.after(2000, self.root.destroy)  # Закрываем через 2 секунды

    def _auth_fail(self, error_msg):
        self.browser_btn.config(state='normal')
        self.cancel_btn.config(state='normal')
        self.check_now_btn.config(state='disabled')
        self.status_var.set("❌ Ошибка авторизации")

    def start_auth_process(self):
        """Начинает процесс авторизации"""
        thread = threading.Thread(target=self._start_auth_thread)
        thread.daemon = True
        thread.start()

    def _start_auth_thread(self):
        """Поток для получения ссылки авторизации"""
        auth_url = self.get_auth_url()

        if auth_url:
            self.root.after(0, lambda: self._show_auth_url(auth_url))
        else:
            self.root.after(0, lambda: self._auth_fail("❌ Не удалось получить ссылку для авторизации"))

    def _show_auth_url(self, auth_url):
        """Показывает полученную ссылку в интерфейсе"""
        display_url = auth_url
        if len(display_url) > 60:
            display_url = display_url[:60] + "..."

        self.url_label.config(text=display_url)
        self.status_var.set("✅ Ссылка получена! Нажмите 'Открыть в браузере'")

        self.browser_btn.config(state='normal')

    def run(self):
        self.start_auth_process()
        self.root.wait_window()  # Ждем закрытия окна
        return self.auth_success
