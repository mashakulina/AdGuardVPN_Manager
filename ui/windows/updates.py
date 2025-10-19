import os
import shutil
import tarfile
import tempfile
import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import threading
import re
from ui.components.dialogs import show_question_dialog
from ui.components.button_styler import create_hover_button
from core.github_updater import GitHubUpdater
from config.manager_config import MANAGER_CONFIG


class UpdateWindow:
    def __init__(self, parent):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.setup_window_properties()
        self.root.title("Обновление")

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
        base_width = 480
        base_height = 340

        # --- Учёт ориентации ---
        if screen_height > screen_width:
            # Портретная ориентация (например, у Steam Deck)
            screen_width, screen_height = screen_height, screen_width

        # --- Подстройка под Steam Deck / SteamOS ---
        if is_steamdeck():
            # На Steam Deck — чуть меньше, чтобы влезало в экран даже с рамкой
            width = min(base_width + 30, screen_width + 20)
            height = min(base_height + 40, screen_height + 40)
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

        # Флаг наличия обновления для AdGuard VPN
        self.update_available = False
        self.available_version = None

        # Флаг наличия обновления для менеджера
        self.manager_update_available = False
        self.latest_manager_version = None
        self.latest_release_data = None

        # Для менеджера
        self.manager_updater = GitHubUpdater(
            version_url=MANAGER_CONFIG["version_url"],
            current_version=MANAGER_CONFIG["current_version"]
        )
        self.latest_manager_version = None
        self.latest_release_data = None
        self.downloaded_update_path = os.path.expanduser("~/AdGuard VPN Manager")  # Путь к скачанному обновлению

        self.setup_manager_section()  # Добавьте этот вызов

        # Загружаем сохраненный канал или используем release по умолчанию
        self.update_channel = self.load_saved_channel()
        self.setup_ui()

        # Устанавливаем начальное значение метки и радиокнопок
        self.update_channel_display()

    def setup_window_properties(self):
        """Настройка свойств окна для корректного отображения"""
        self.root.title("AdGuard VPN Manager")

        # Устанавливаем WM_CLASS (БЕЗ ПРОБЕЛОВ!)
        try:
            manager_dir = os.path.expanduser("~/AdGuard VPN Manager")
            self.root.wm_class("AdGuardVPNManager")
        except:
            pass

        # Устанавливаем иконку
        try:
            icon_path = os.path.join(manager_dir, "ico/adguard.png")
            if os.path.exists(icon_path):
                # Для PNG файлов в tkinter
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
        except Exception as e:
            print(f"Не удалось установить иконку: {e}")

    def load_saved_channel(self):
        """Загружает сохраненный канал обновления из конфига"""
        try:
            # Получаем текущую конфигурацию
            result = subprocess.run(
                ['adguardvpn-cli', 'config', 'show'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                config_output = result.stdout
                # Ищем строку с Update channel с помощью regex
                match = re.search(r'Update channel:\s*([^\n]+)', config_output, re.IGNORECASE)
                if match:
                    channel = match.group(1).strip().lower()
                    if 'beta' in channel:
                        return 'beta'
                    elif 'release' in channel:
                        return 'release'
                    return channel
        except Exception as e:
            print(f"Ошибка загрузки канала: {e}")

        return "release"  # По умолчанию

    def save_channel(self, channel):
        """Сохраняет выбранный канал только локально (не применяет в CLI)"""
        self.update_channel = channel

    def update_channel_display(self):
        """Обновляет отображение канала обновления на основе фактического значения"""
        # Устанавливаем радиокнопку
        self.channel_var.set(self.update_channel)

        # Обновляем текст метки
        if self.update_channel == "release":
            self.channel_label.config(text="Канал обновления: Release")
        else:
            self.channel_label.config(text="Канал обновления: Beta")

    def update_action_button(self):
        """Обновляет текст и команду кнопки действия в зависимости от наличия обновления"""
        if self.update_available:
            self.action_button.config(
                text="Обновиться",
                command=self.update_adguard,
                bg='#15354D'
            )
        else:
            self.action_button.config(
                text="Проверить обновление",
                command=self.check_adguard_update,
                bg='#15354D'
            )

    def setup_manager_section(self):
        """Настраивает элементы UI для обновления менеджера"""
        # Этот метод будет вызываться из setup_ui
        pass

    def get_adguard_current_version(self):
        """Получает текущую версию AdGuard VPN"""
        try:
            result = subprocess.run(
                ['adguardvpn-cli', '-v'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Очищаем вывод от ANSI кодов и лишних символов
                version_output = self.clean_ansi_codes(result.stdout).strip()

                # Ищем версию в формате vX.X.X или X.X.X
                version_match = re.search(r'v?(\d+\.\d+\.\d+)', version_output)
                if version_match:
                    return f"{version_match.group(1)}"

                # Если не нашли через regex, возвращаем как есть (очищенное)
                return version_output if version_output else "Неизвестно"

            return "Неизвестно"
        except Exception as e:
            print(f"Ошибка получения версии AdGuard VPN: {e}")
            return "Неизвестно"

    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg='#182030', padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Обновление",
                font=("Arial", 14, "bold"), fg='white', bg='#182030').pack(anchor=tk.CENTER, pady=(0, 5))


        # Создаем контейнер для двух колонок
        columns_frame = tk.Frame(main_frame, bg='#182030')
        columns_frame.pack(fill=tk.BOTH, expand=True)

        # Левая колонка - Обновление менеджера (заглушка)
        left_column = tk.Frame(columns_frame, bg='#182030', width=200, relief=tk.GROOVE, bd=0)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        left_column.pack_propagate(False)

        # Правая колонка - Обновление AdGuard VPN
        right_column = tk.Frame(columns_frame, bg='#182030', width=200, relief=tk.GROOVE, bd=0)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        right_column.pack_propagate(False)

        # === ЛЕВАЯ КОЛОНКА - ОБНОВЛЕНИЕ МЕНЕДЖЕРА ===
        left_content = tk.Frame(left_column, bg='#182030', padx=5, pady=5)
        left_content.pack(fill=tk.BOTH, expand=True)

        tk.Label(left_content, text="AdGuard VPN Manager",
                font=("Arial", 14, "bold"), fg='white', bg='#182030').pack(anchor=tk.CENTER, pady=(0, 10))

        # Текущая версия
        version_frame = tk.Frame(left_content, bg='#182030')
        version_frame.pack(anchor=tk.CENTER, pady=(0, 10))

        tk.Label(version_frame, text=f"Версия: {MANAGER_CONFIG['current_version']}",
                font=("Arial", 11), fg='#5BA06A', bg='#182030').pack(anchor=tk.CENTER)

        # Кнопка проверки и обновления менеджера
        manager_buttons_frame = tk.Frame(left_content, bg='#182030')
        manager_buttons_frame.pack(anchor=tk.CENTER, pady=(0, 18))

        self.manager_action_button = create_hover_button(
            manager_buttons_frame,
            text="Проверить обновление",
            command=self.check_manager_update,
            bg='#15354D', fg='white', font=('Arial', 10),
            width=20, bd=0, highlightthickness=0, padx=10, pady=5
        )
        self.manager_action_button.pack(side=tk.LEFT)

        # Область лога внизу основного окна
        log_frame = tk.Frame(left_content, bg='#182030')
        log_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Label(log_frame, text="Информация:",
                font=("Arial", 10), fg='white', bg='#182030').pack(anchor=tk.W, pady=(0, 10))

        self.log_text = tk.Text(log_frame, height=5, bg='#15354D',
                                highlightthickness=0,fg='white', wrap=tk.WORD, font=("Courier", 9))
        self.log_text.pack(fill=tk.X)

        # === ПРАВАЯ КОЛОНКА - ОБНОВЛЕНИЕ ADGUARD VPN ===
        right_content = tk.Frame(right_column, bg='#182030', padx=5, pady=5)
        right_content.pack(fill=tk.BOTH, expand=True)

        tk.Label(right_content, text="AdGuard VPN",
                font=("Arial", 14, "bold"), fg='white', bg='#182030').pack(anchor=tk.CENTER, pady=(0, 10))

        # Текущая версия - динамическая
        version_frame = tk.Frame(right_content, bg='#182030')
        version_frame.pack(fill=tk.X, pady=(0, 10))

        # Получаем текущую версию при инициализации
        current_version = self.get_adguard_current_version()

        self.current_version_label = tk.Label(version_frame,
                                            text=f"Версия: {current_version}",
                                            font=("Arial", 11), fg='#5BA06A', bg='#182030')
        self.current_version_label.pack(anchor=tk.CENTER)

        # Кнопка действия (проверка/обновление)
        buttons_frame = tk.Frame(right_content, bg='#182030')
        buttons_frame.pack(fill=tk.X, pady=(0, 20))


        self.action_button = create_hover_button(buttons_frame, text="Проверить обновление",
                command=self.check_adguard_update, bg='#15354D', fg='white', font=('Arial', 10),
                width=20, bd=0, highlightthickness=0, padx=10, pady=5)
        self.action_button.pack(anchor=tk.CENTER, padx=(0, 10))

        # Выбор канала обновления
        channel_frame = tk.Frame(right_content, bg='#182030')
        channel_frame.pack(fill=tk.X, pady=(0, 15))

        # Изменяемая строка с текущим каналом
        self.channel_label = tk.Label(channel_frame, text="Канал обновления: Release",
                                    font=("Arial", 11), fg='#5BA06A', bg='#182030')
        self.channel_label.pack(anchor=tk.CENTER, pady=(0, 8))

        # Фрейм для радиокнопок - на одной линии
        radio_frame = tk.Frame(channel_frame, bg='#182030')
        radio_frame.pack(side=tk.LEFT, padx=20)

        self.channel_var = tk.StringVar(value="release")

        self.release_radio = tk.Radiobutton(radio_frame, text="Release",
                                        variable=self.channel_var, value="release",
                                        font=("Arial", 10), fg='white', bg='#182030',
                                        selectcolor='#15354D', activebackground='#182030',
                                        activeforeground='white',
                                        bd=0, highlightthickness=0)
        self.release_radio.pack(side=tk.LEFT, padx=(0, 20))

        self.beta_radio = tk.Radiobutton(radio_frame, text="Beta",
                                    variable=self.channel_var, value="beta",
                                    font=("Arial", 10), fg='white', bg='#182030',
                                        selectcolor='#15354D', activebackground='#182030',
                                        activeforeground='white',
                                        bd=0, highlightthickness=0)
        self.beta_radio.pack(side=tk.LEFT)

        # Кнопка действия (проверка/обновление)
        buttons_frame = tk.Frame(right_content, bg='#182030')
        buttons_frame.pack(anchor=tk.CENTER)
        # Кнопка применения канала
        apply_btn = create_hover_button(buttons_frame, text="Применить", command=self.apply_update_channel,
                bg='#15354D', fg='white', font=('Arial', 10),
                bd=0, highlightthickness=0, padx=10, pady=5).pack(side=tk.LEFT, padx=(0, 5))


        # Кнопка закрытия
        btn_frame = tk.Frame(main_frame, bg='#182030')
        btn_frame.pack(fill=tk.X, pady=10)

        close_btn=create_hover_button(btn_frame, text="Закрыть", command=self.close_window,
                                      bg='#15354D', fg='white', font=('Arial', 10), width=15, bd=0, highlightthickness=0, padx=10, pady=5)
        close_btn.pack(anchor=tk.CENTER)

    def update_manager_action_button(self):
        """Обновляет текст и команду кнопки действия менеджера в зависимости от наличия обновления"""
        if self.manager_update_available:
            self.manager_action_button.config(
                text="Обновиться",
                command=self.download_manager_update,
                bg='#15354D'
            )
        else:
            self.manager_action_button.config(
                text="Проверить обновление",
                command=self.check_manager_update,
                bg='#15354D'
            )

    def check_manager_update(self):
        """Проверяет обновления для менеджера"""
        self.manager_action_button.config(state=tk.DISABLED, text="Проверка...")

        thread = threading.Thread(target=self._check_manager_update_thread)
        thread.daemon = True
        thread.start()

    def _check_manager_update_thread(self):
        """Поток для проверки обновлений менеджера"""
        try:
            latest_version, release_data = self.manager_updater.check_for_updates()

            if latest_version:
                self.latest_manager_version = latest_version
                self.latest_release_data = release_data
                self.manager_update_available = True

                self.root.after(0, lambda: self.log_message(f"📢 Доступно обновление AdGuard VPN Manager: {latest_version}"))
            else:
                self.manager_update_available = False
                self.root.after(0, lambda: self.log_message("✅ Установлена последняя версия AdGuard VPN Manager"))

        except Exception as e:
            self.manager_update_available = False
            self.root.after(0, lambda: self.log_message(f"❌ Ошибка проверки обновлений AdGuard VPN Manager: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.manager_action_button.config(state=tk.NORMAL))
            self.root.after(0, self.update_manager_action_button)

    def download_manager_update(self):
        """Скачивает обновление менеджера"""
        if not self.latest_release_data:
            return

        # Показываем диалог подтверждения ДО запуска потока
        if not show_question_dialog(self.root, "Обновление AdGuard VPN Manager",
                                "AdGuard VPN Manager будет обновлен. После скачивания:\n"
                                "1. Удалятся текущие файлы AdGuard VPN Manager\n"
                                "2. Будет установлена новая версия\n"
                                "3. AdGuard VPN Manager перезапустится\n\n"
                                "Продолжить?"):
            return

        self.manager_action_button.config(state=tk.DISABLED, text="Обновление...")

        thread = threading.Thread(target=self._download_manager_update_thread)
        thread.daemon = True
        thread.start()

    def _download_manager_update_thread(self):
        """Поток для скачивания и установки обновления менеджера"""
        try:
            download_url = self.manager_updater.get_download_url(self.latest_release_data)
            if not download_url:
                raise Exception("URL для скачивания не найден")

            self.root.after(0, lambda: self.log_message("📥 Начало загрузки обновления AdGuard VPN Manager..."))

            # Создаем временный файл для загрузки
            temp_dir = tempfile.gettempdir()
            filename = f"manager_update_{self.latest_manager_version}.tar.gz"
            downloaded_file_path = os.path.join(temp_dir, filename)

            # Скачиваем файл с помощью urllib (стандартная библиотека)
            import urllib.request
            urllib.request.urlretrieve(download_url, downloaded_file_path)

            self.root.after(0, lambda: self.log_message("✅ Архив скачан. Начинается установка..."))

            # Путь к папке менеджера
            manager_dir = os.path.expanduser("~/AdGuard VPN Manager")

            # Удаляем старую версию
            if os.path.exists(manager_dir):
                shutil.rmtree(manager_dir)
                self.root.after(0, lambda: self.log_message("🗑️ Старая версия удалена"))

            # Создаем папку заново
            os.makedirs(manager_dir, exist_ok=True)

            # Распаковываем tar.gz архив
            with tarfile.open(downloaded_file_path, 'r:gz') as tar_ref:
                tar_ref.extractall(manager_dir)

            self.root.after(0, lambda: self.log_message("✅ Файлы распакованы"))

            # Удаляем временный файл
            os.remove(downloaded_file_path)

            self.root.after(0, lambda: self.log_message(f"✅ Обновление AdGuard VPN Manager до версии {self.latest_manager_version} завершено!"))
            self.root.after(0, lambda: self.log_message("🔄 Перезапуск AdGuard VPN Manager..."))

            # После успешного обновления сбрасываем флаг
            self.manager_update_available = False

            # Перезапускаем менеджер через 2 секунды
            self.root.after(2000, self.restart_manager)

        except Exception as error:
            error_msg = str(error)
            self.root.after(0, lambda: self.log_message(f"❌ Ошибка установки обновления AdGuard VPN Manager: {error_msg}"))
        finally:
            self.root.after(0, lambda: self.manager_action_button.config(state=tk.NORMAL))
            self.root.after(0, self.update_manager_action_button)

    def restart_manager(self):
        """Перезапускает менеджер"""
        try:
            # Путь к основному скрипту
            manager_dir = os.path.expanduser("~/AdGuard VPN Manager")
            main_script = os.path.join(manager_dir, "main.py")

            if not os.path.exists(main_script):
                self.root.after(0, lambda: self.log_message("❌ Файл main.py не найден"))
                return

            # Закрываем текущие окна
            self.root.destroy()
            self.parent.destroy()

            # Перезапускаем менеджер
            import sys
            import subprocess

            # Запускаем main.py в новом процессе
            subprocess.Popen([sys.executable, main_script])

        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"❌ Ошибка при перезапуске: {str(e)}"))

    def update_adguard_version_display(self):
        """Обновляет отображение текущей версии AdGuard VPN"""
        current_version = self.get_adguard_current_version()
        self.current_version_label.config(text=f"Версия: {current_version}")

    def apply_update_channel(self):
        """Применяет выбранный канал обновления"""
        selected_channel = self.channel_var.get()

        # Проверяем, не пытаемся ли установить уже активный канал
        if selected_channel == self.update_channel:
            self.log_message(f"Канал {selected_channel} уже установлен")
            return

        # Логируем выбор пользователя
        self.log_message(f"🔄 Попытка установки канала: {selected_channel}")

        thread = threading.Thread(target=self._apply_channel_thread, args=(selected_channel,))
        thread.daemon = True
        thread.start()

    def _apply_channel_thread(self, channel):
        """Поток для применения канала обновления"""
        try:
            self.root.after(0, lambda: self.log_message(f"⏳ Установка канала {channel}..."))

            result = subprocess.run(
                ['adguardvpn-cli', 'config', 'set-update-channel', channel],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Успешно применили - обновляем отображение
                self.update_channel = channel
                self.root.after(0, self.update_channel_display)
                self.root.after(0, lambda: self.log_message(f"✅ Канал обновления успешно изменен на {channel}"))

                # После смены канала сбрасываем статус обновления
                self.update_available = False
                self.available_version = None
                self.root.after(0, self.update_action_button)

            else:
                error_msg = result.stderr if result.stderr else "Неизвестная ошибка"
                self.root.after(0, lambda: self.log_message(f"❌ Ошибка установки канала: {error_msg}"))

        except subprocess.TimeoutExpired:
            self.root.after(0, lambda: self.log_message("❌ Таймаут при установке канала"))
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"❌ Ошибка при установке канала: {str(e)}"))

    def check_adguard_update(self):
        """Проверяет обновления AdGuard VPN"""
        # Временно блокируем кнопку во время проверки
        self.action_button.config(state=tk.DISABLED, text="Проверка...")

        thread = threading.Thread(target=self._check_update_thread)
        thread.daemon = True
        thread.start()

    def _check_update_thread(self):
        """Поток для проверки обновлений"""
        try:
            self.root.after(0, lambda: self.log_message("🔍 Проверка обновлений AdGuard VPN..."))

            result = subprocess.run(
                ['adguardvpn-cli', 'check-update'],
                capture_output=True,
                text=True,
                timeout=15
            )

            # Очищаем вывод от ANSI кодов
            cleaned_output = self.clean_ansi_codes(result.stdout + result.stderr)

            # Анализируем вывод более точно
            output_lower = cleaned_output.lower()

            # Пытаемся извлечь версию обновления
            version = self.extract_version(cleaned_output)

            # Проверяем наличие сообщения о доступном обновления
            has_update_available = any(phrase in output_lower for phrase in [
                'is now available',
                'update available',
                'available',
                'доступно',
                'можно обновиться',
                'new version'
            ])

            # Проверяем наличие сообщения о том, что версия актуальна
            is_latest = any(phrase in output_lower for phrase in [
                'latest version',
                'up to date',
                'актуальна',
                'you are using the latest'
            ])

            if has_update_available:
                self.update_available = True
                self.available_version = version
                if version:
                    self.root.after(0, lambda: self.log_message(f"📢 Доступно обновление AdGuard VPN {version}"))
                else:
                    self.root.after(0, lambda: self.log_message("📢 Доступно обновление AdGuard VPN"))

            elif is_latest:
                # Получаем текущую версию
                current_version = self.get_adguard_current_version()
                self.root.after(0, lambda: self.log_message(f"✅ Установлена последняя версия AdGuard VPN v{current_version}"))
                self.update_available = False
                self.available_version = None
                # Возвращаем обычный вид
                self.root.after(0, lambda: self.current_version_label.config(
                    text=f"Версия: {current_version}",
                    fg='#5BA06A'  # Зеленый цвет для актуальной версии
                ))

            else:
                # Если не можем определить статус, выводим как есть
                self.root.after(0, lambda: self.log_message("⚠️ Не удалось определить статус обновления"))
                self.update_available = False
                self.available_version = None
                # Возвращаем обычный вид
                self.root.after(0, self.update_adguard_version_display)

        except subprocess.TimeoutExpired:
            self.root.after(0, lambda: self.log_message("❌ Таймаут при проверке обновлений"))
            self.update_available = False  # Добавлена эта строка
            self.available_version = None  # Добавлена эта строка
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"❌ Ошибка при проверке обновлений: {str(e)}"))
            self.update_available = False  # Добавлена эта строка
            self.available_version = None  # Добавлена эта строка
        finally:
            # Всегда разблокируем кнопку и обновляем ее текст
            self.root.after(0, lambda: self.action_button.config(state=tk.NORMAL))
            self.root.after(0, self.update_action_button)

    def get_current_version(self):
        """Получает текущую версию AdGuard VPN через adguardvpn-cli -v"""
        try:
            result = subprocess.run(
                ['adguardvpn-cli', '-v'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Очищаем вывод от ANSI кодов и лишних символов
                version_output = self.clean_ansi_codes(result.stdout).strip()

                # Ищем версию в формате vX.X.X или X.X.X
                version_match = re.search(r'v?(\d+\.\d+\.\d+)', version_output)
                if version_match:
                    return f"{version_match.group(1)}"

                # Если не нашли через regex, возвращаем как есть (очищенное)
                return version_output if version_output else None

            return None
        except Exception:
            return None

    def extract_version(self, text):
        """Извлекает версию из текста вывода"""
        try:
            # Ищем паттерны версий: v1.5.12, 1.5.12, v2.0.1 и т.д.
            version_patterns = [
                r'AdGuard VPN[^\n]*v?(\d+\.\d+\.\d+)[^\n]*is now available',
                r'v?(\d+\.\d+\.\d+)[^\n]*is now available',
                r'version[^\n]*v?(\d+\.\d+\.\d+)',
                r'v?(\d+\.\d+\.\d+)[^\n]*available',
                r'обновление[^\n]*v?(\d+\.\d+\.\d+)'
            ]

            for pattern in version_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return f"v{match.group(1)}" if not match.group(1).startswith('v') else match.group(1)

            return None
        except Exception:
            return None

    def update_adguard(self):
        """Запускает обновление AdGuard VPN"""
        if show_question_dialog(self.root, "Обновление",
                               "Вы уверены, что хотите обновиться?\n\n"
                               "Если VPN подключен, соединение будет разорвано."):

            # Блокируем кнопку во время обновления
            self.action_button.config(state=tk.DISABLED, text="Обновление...")

            thread = threading.Thread(target=self._update_thread)
            thread.daemon = True
            thread.start()

    def _update_thread(self):
        """Поток для выполнения обновления"""
        try:
            self.root.after(0, lambda: self.log_message("🔄 Запуск обновления AdGuard VPN..."))

            # Запускаем процесс обновления с автоматическим ответом 'y'
            process = subprocess.Popen(
                ['adguardvpn-cli', 'update'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Автоматически отвечаем 'y' на запрос подтверждения
            output, error = process.communicate(input='y\n', timeout=60)

            # Очищаем вывод от ANSI кодов
            cleaned_output = self.clean_ansi_codes(output + error)

            if process.returncode == 0:
                self.root.after(0, lambda: self.log_message("✅ AdGuard VPN успешно обновлен!"))
                # После успешного обновления сбрасываем флаг
                self.update_available = False
                self.available_version = None

                # ОБНОВЛЯЕМ ОТОБРАЖЕНИЕ ВЕРСИИ ПОСЛЕ ОБНОВЛЕНИЯ
                self.root.after(0, self.update_adguard_version_display)

                # Также обновляем текст кнопки
                self.root.after(0, self.update_action_button)
            else:
                self.root.after(0, lambda: self.log_message(f"❌ Ошибка при обновлении:\n{cleaned_output}"))

        except subprocess.TimeoutExpired:
            self.root.after(0, lambda: self.log_message("❌ Таймаут при выполнении обновления"))
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"❌ Ошибка при обновлении: {str(e)}"))
        finally:
            # Всегда разблокируем кнопку и обновляем ее текст
            self.root.after(0, lambda: self.action_button.config(state=tk.NORMAL))
            self.root.after(0, self.update_action_button)

    def clean_ansi_codes(self, text):
        """Очищает текст от ANSI escape sequences"""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def log_message(self, message):
        """Добавляет сообщение в лог"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def close_window(self):
        self.root.destroy()

    def run(self):
        self.root.wait_window()
