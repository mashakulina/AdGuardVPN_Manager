import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import threading
import os
import sys
import shutil
from ui.components.button_styler import create_hover_button, apply_hover_effect

class SudoPasswordWindow:
    def __init__(self, parent):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.setup_window_properties()
        self.root.title("Аутентификация")
        self.root.geometry("270x280")
        self.root.configure(bg='#182030')
        self.root.transient(parent)
        self.root.grab_set()

        try:
            from tkinter import ttk
            style = ttk.Style()
            style.theme_use('clam')  # или 'alt', 'classic' - простые темы
        except:
            pass

        self.sudo_password = None
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
                              font=("Arial", 14, "bold"), fg='white', bg='#182030')
        title_label.pack(pady=5)

        desc_label = tk.Label(main_frame,
                             text="Для удаления AdGuard VPN\nтребуется права администратора",
                             font=("Arial", 10), fg='white', bg='#182030')
        desc_label.pack(pady=5)

        sudo_frame = tk.Frame(main_frame, bg='#182030')
        sudo_frame.pack(fill=tk.X, pady=10)

        tk.Label(sudo_frame, text="Введите пароль:",
                fg='white', bg='#182030').pack(anchor=tk.W)

        self.sudo_entry = tk.Entry(sudo_frame, show="*", width=30, font=('Arial', 12),
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

        resume_btn = create_hover_button(btn_frame, text="Продолжить",
                                         command=self.verify_sudo, **button_style)
        resume_btn.grid(row=0, column=0, padx=(0, 10))

        cancel_btn = create_hover_button(btn_frame, text="Отмена",
                                         command=self.cancel, **button_style)
        cancel_btn.grid(row=0, column=1)

        # Центрируем весь фрейм с кнопками
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        # Статус бар
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
        self.root.after(500, self.close_window)

    def _sudo_verified_fail(self, error_msg):
        self.status_var.set(error_msg)
        self.sudo_entry.config(state='normal')
        self.sudo_entry.delete(0, tk.END)
        self.sudo_entry.focus()

    def close_window(self):
        self.root.destroy()

    def cancel(self):
        self.sudo_password = None
        self.root.destroy()

    def run(self):
        self.root.wait_window()
        return self.sudo_password


class UninstallWindow:
    def __init__(self, parent):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.setup_window_properties()
        self.root.title("Удаление AdGuard VPN")
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
        base_width = 335
        base_height = 460

        # --- Учёт ориентации ---
        if screen_height > screen_width:
            # Портретная ориентация (например, у Steam Deck)
            screen_width, screen_height = screen_height, screen_width

        # --- Подстройка под Steam Deck / SteamOS ---
        if is_steamdeck():
            # На Steam Deck — чуть меньше, чтобы влезало в экран даже с рамкой
            width = min(base_width + 20, screen_width + 20)
            height = min(base_height + 10, screen_height + 40)
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
            style.theme_use('clam')
        except:
            pass

        self.sudo_password = None
        self.filesystem_unlocked = False

        # Переменные для чекбоксов
        self.remove_vpn_var = tk.BooleanVar(value=True)
        self.remove_manager_var = tk.BooleanVar(value=True)
        self.remove_config_var = tk.BooleanVar(value=False)

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

        title_label = tk.Label(main_frame, text="Удаление AdGuard VPN",
                              font=("Arial", 16, "bold"), fg='white', bg='#182030')
        title_label.pack(pady=10)

        warning_label = tk.Label(main_frame,
                                text="Выберите компоненты для удаления:",
                                font=("Arial", 12), fg='#ff3b30', bg='#182030')
        warning_label.pack(pady=5)

        # Фрейм для чекбоксов
        checkboxes_frame = tk.Frame(main_frame, bg='#182030')
        checkboxes_frame.pack(fill=tk.X, pady=10)

        # Стиль для чекбоксов
        checkbox_style = {
            'font': ('Arial', 10),
            'fg': 'white',
            'bg': '#182030',
            'selectcolor': '#15354D',
            'activebackground': '#182030',
            'activeforeground': 'white',
            'bd': 0,
            'highlightthickness': 0
        }

        # Чекбокс для удаления AdGuard VPN
        self.vpn_checkbox = tk.Checkbutton(
            checkboxes_frame,
            text="AdGuard VPN",
            variable=self.remove_vpn_var,
            **checkbox_style
        )
        self.vpn_checkbox.pack(anchor=tk.W, pady=5)

        # Чекбокс для удаления менеджера
        self.manager_checkbox = tk.Checkbutton(
            checkboxes_frame,
            text="Менеджер AdGuard VPN",
            variable=self.remove_manager_var,
            **checkbox_style
        )
        self.manager_checkbox.pack(anchor=tk.W, pady=5)

        # Чекбокс для удаления конфигов
        self.config_checkbox = tk.Checkbutton(
            checkboxes_frame,
            text="Файлы конфигурации и настройки",
            variable=self.remove_config_var,
            **checkbox_style
        )
        self.config_checkbox.pack(anchor=tk.W, pady=5)

        # Информационная метка
        info_label = tk.Label(main_frame,
                             text="Это действие нельзя отменить.\nВыбранные данные будут удалены.",
                             font=("Arial", 10), fg='white', bg='#182030')
        info_label.pack(pady=5)

        # Кнопки
        btn_frame = tk.Frame(main_frame, bg='#182030')
        btn_frame.pack(fill=tk.X, pady=10)

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

        self.uninstall_btn = create_hover_button(btn_frame, text="Удалить",
                                                 command=self.uninstall, **button_style)
        self.uninstall_btn.grid(row=0, column=0, padx=(0, 10))

        self.cancel_btn = create_hover_button(btn_frame, text="Отмена",
                                              command=self.close_window, **button_style)
        self.cancel_btn.grid(row=0, column=1)

        # Центрируем весь фрейм с кнопками
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        # Область логов (всегда видима)
        log_frame = tk.Frame(main_frame, bg='#182030')
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_text = tk.Text(log_frame, height=8, width=40, highlightthickness=0,
                                                 wrap=tk.WORD, bg='#15354D', fg='white',
                                                 font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

    def log_message(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def get_sudo_password(self):
        """Запрашивает sudo пароль с проверкой"""
        self.log_message("🔐 Запрос прав администратора...")
        sudo_window = SudoPasswordWindow(self.root)
        password = sudo_window.run()

        if password:
            self.log_message("✅ Sudo аутентификация успешна")
            return password
        else:
            self.log_message("Ввод пароля отменен")
            return None

    def unlock_filesystem(self):
        """Разблокировка файловой системы SteamOS"""
        try:
            self.log_message("🔓 Разблокировка файловой системы SteamOS...")
            cmd = f'echo "{self.sudo_password}" | sudo -S steamos-readonly disable'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                self.filesystem_unlocked = True
                self.log_message("✅ Файловая система разблокирована")
                return True
            else:
                self.log_message(f"⚠️ Не удалось разблокировать файловую систему: {result.stderr}")
                return True  # Продолжаем удаление
        except Exception as e:
            self.log_message(f"⚠️ Ошибка разблокировки: {str(e)}")
            return True

    def lock_filesystem(self):
        """Блокировка файловой системы SteamOS"""
        if not self.filesystem_unlocked:
            return

        try:
            self.log_message("🔒 Блокировка файловой системы SteamOS...")
            cmd = f'echo "{self.sudo_password}" | sudo -S steamos-readonly enable'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                self.log_message("✅ Файловая система заблокирована")
                self.log_message("✅ Процесс удаления завершен")
            else:
                self.log_message(f"⚠️ Не удалось заблокировать файловую систему: {result.stderr}")
        except Exception as e:
            self.log_message(f"⚠️ Ошибка блокировки: {str(e)}")

    def uninstall(self):
        """Запуск процесса удаления"""
        # Проверяем, что выбран хотя бы один компонент
        if not any([self.remove_vpn_var.get(), self.remove_config_var.get(), self.remove_manager_var.get()]):
            self.log_message("❌ Выберите хотя бы один компонент для удаления")
            return

        self.sudo_password = self.get_sudo_password()
        if not self.sudo_password:
            return

        # Отключаем кнопки
        self.uninstall_btn.config(state='disabled')
        self.cancel_btn.config(state='disabled')

        # Запускаем удаление в отдельном потоке
        thread = threading.Thread(target=self._uninstall_thread)
        thread.daemon = True
        thread.start()

    def _uninstall_thread(self):
        """Поток удаления"""
        try:
            self.root.after(0, lambda: self.log_message("=== Начало удаления выбранных компонентов ==="))

            # Логируем выбранные компоненты
            selected_components = []
            if self.remove_vpn_var.get():
                selected_components.append("AdGuard VPN")
            if self.remove_config_var.get():
                selected_components.append("конфигурационные файлы")
            if self.remove_manager_var.get():
                selected_components.append("менеджер")

            self.root.after(0, lambda: self.log_message(f"📝 Выбрано для удаления: {', '.join(selected_components)}"))

            # Разблокируем файловую систему (только если нужно удалять VPN)
            if self.remove_vpn_var.get():
                if not self.unlock_filesystem():
                    raise Exception("Не удалось разблокировать файловую систему")

            # Выполняем удаление по выбранным компонентам
            success = self.perform_uninstall()

            if success:
                self.root.after(0, self._uninstall_success)
            else:
                self.root.after(0, lambda: self._uninstall_fail("Ошибка удаления"))

        except Exception as e:
            self.root.after(0, lambda: self._uninstall_fail(f"Ошибка: {str(e)}"))
        finally:
            # Всегда блокируем файловую систему обратно (только если она была разблокирована)
            if self.filesystem_unlocked:
                self.lock_filesystem()

    def perform_uninstall(self):
        """Выполняет удаление выбранных компонентов"""
        try:
            # Удаление AdGuard VPN
            if self.remove_vpn_var.get():
                # 1. Удаляем символическую ссылку
                self.root.after(0, lambda: self.log_message("🗑️ Удаление символической ссылки..."))
                link_cmd = f'echo "{self.sudo_password}" | sudo -S rm -f /usr/local/bin/adguardvpn-cli'
                result = subprocess.run(link_cmd, shell=True, capture_output=True, text=True)

                if result.returncode == 0:
                    self.root.after(0, lambda: self.log_message("✅ Символическая ссылка удалена"))
                else:
                    self.root.after(0, lambda: self.log_message("⚠️ Не удалось удалить символическую ссылку"))

                # 2. Удаляем директорию установки
                self.root.after(0, lambda: self.log_message("🗑️ Удаление файлов AdGuard VPN..."))
                install_dir = "/opt/adguardvpn_cli"
                rm_cmd = f'echo "{self.sudo_password}" | sudo -S rm -rf {install_dir}'
                result = subprocess.run(rm_cmd, shell=True, capture_output=True, text=True)

                if result.returncode == 0:
                    self.root.after(0, lambda: self.log_message("✅ Файлы AdGuard VPN удалены"))
                else:
                    self.root.after(0, lambda: self.log_message("⚠️ Не удалось удалить файлы AdGuard VPN"))

            # Удаление конфигурационных файлов
            if self.remove_config_var.get():
                self.root.after(0, lambda: self.log_message("🗑️ Удаление конфигурационных файлов..."))

                # Директория конфигурации
                config_dir = os.path.expanduser("~/.local/share/adguardvpn-cli")
                rm_config_cmd = f'echo "{self.sudo_password}" | sudo -S rm -rf {config_dir}'
                result = subprocess.run(rm_config_cmd, shell=True, capture_output=True, text=True)

                if result.returncode == 0:
                    self.root.after(0, lambda: self.log_message("✅ Конфигурационные файлы удалены"))
                else:
                    self.root.after(0, lambda: self.log_message("⚠️ Не удалось удалить конфигурационные файлы"))

            # Удаление менеджера и ярлыков
            if self.remove_manager_var.get():
                self.root.after(0, lambda: self.log_message("🗑️ Удаление менеджера и ярлыков..."))

                # Удаляем ярлыки с рабочего стола
                self.root.after(0, lambda: self.log_message("🗑️ Удаление ярлыков с рабочего стола..."))
                desktop_paths = [
                    os.path.expanduser("~/Рабочий стол/AdGuard_VPN_Manager.desktop"),  # Русский
                    os.path.expanduser("~/Desktop/AdGuard_VPN_Manager.desktop"),       # Английский
                ]

                desktop_removed = False
                for desktop_path in desktop_paths:
                    if os.path.exists(desktop_path):
                        try:
                            os.remove(desktop_path)
                            self.root.after(0, lambda: self.log_message(f"✅ Ярлык удален: {desktop_path}"))
                            desktop_removed = True
                        except Exception as e:
                            self.root.after(0, lambda: self.log_message(f"⚠️ Не удалось удалить ярлык {desktop_path}: {e}"))

                if not desktop_removed:
                    self.root.after(0, lambda: self.log_message("ℹ️ Ярлыки на рабочем столе не найдены"))

                # Удаляем ярлык из меню приложений
                self.root.after(0, lambda: self.log_message("🗑️ Удаление ярлыка из меню приложений..."))

                try:
                    # Получаем путь к пользовательской папке приложений
                    home_dir = os.path.expanduser("~")
                    applications_path = os.path.join(home_dir, ".local/share/applications/AdGuard_VPN_Manager.desktop")

                    # Удаляем файл напрямую
                    if os.path.exists(applications_path):
                        os.remove(applications_path)
                        self.root.after(0, lambda: self.log_message("✅ Ярлык из меню приложений удален"))

                        # Обновляем базу данных desktop файлов
                        self.root.after(0, lambda: self.log_message("🔄 Обновление меню приложений..."))
                        applications_dir = os.path.dirname(applications_path)
                        update_result = subprocess.run(['update-desktop-database', applications_dir],
                                                    capture_output=True, text=True)

                        if update_result.returncode == 0:
                            self.root.after(0, lambda: self.log_message("✅ Меню приложений обновлено"))
                        else:
                            self.root.after(0, lambda: self.log_message("⚠️ Не удалось обновить меню приложений"))
                    else:
                        self.root.after(0, lambda: self.log_message("ℹ️ Ярлык в меню приложений не найден"))

                except Exception as e:
                    self.root.after(0, lambda: self.log_message(f"❌ Ошибка удаления ярлыка: {str(e)}"))

                # Удаляем директорию менеджера
                self.root.after(0, lambda: self.log_message("🗑️ Удаление папки менеджера..."))
                manager_dir = os.path.expanduser("~/AdGuard VPN Manager")
                if os.path.exists(manager_dir):
                    try:
                        shutil.rmtree(manager_dir)
                        self.root.after(0, lambda: self.log_message("✅ Папка менеджера удалена"))
                    except Exception as e:
                        self.root.after(0, lambda: self.log_message(f"⚠️ Не удалось удалить папку менеджера: {str(e)}"))
                else:
                    self.root.after(0, lambda: self.log_message("ℹ️ Папка менеджера не найдена"))

            return True


        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"❌ Ошибка при удалении: {str(e)}"))
            return False

    def _uninstall_success(self):
        self.log_message("=== Удаление завершено успешно ===")

        # Показываем сообщение и закрываем окна (только если удаляется менеджер)
        if self.remove_manager_var.get():
            self.root.after(2000, lambda: [self.root.destroy(), self.parent.destroy()])
        else:
            # Включаем кнопки обратно если менеджер не удаляется
            self.uninstall_btn.config(state='normal')
            self.cancel_btn.config(state='normal')

    def _uninstall_fail(self, error_msg):
        self.log_message(f"❌ {error_msg}")

        # Включаем кнопки обратно
        self.uninstall_btn.config(state='normal')
        self.cancel_btn.config(state='normal')

    def close_window(self):
        self.root.destroy()

    def run(self):
        self.root.wait_window()
