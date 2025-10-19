import tkinter as tk
import webbrowser
import os
from ui.components.button_styler import create_hover_button

class DonationWindow:
    def __init__(self, parent):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.setup_window_properties()
        self.create_widgets()

    def setup_window_properties(self):
        """Настройка свойств окна для корректного отображения"""
        self.root.title("Поддержать разработчика")

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
        base_width = 400
        base_height = 430

        # --- Учёт ориентации ---
        if screen_height > screen_width:
            # Портретная ориентация (например, у Steam Deck)
            screen_width, screen_height = screen_height, screen_width

        # --- Подстройка под Steam Deck / SteamOS ---
        if is_steamdeck():
            # На Steam Deck — чуть меньше, чтобы влезало в экран даже с рамкой
            width = min(base_width + 20, screen_width + 20)
            height = min(base_height + 30, screen_height + 40)
            # Без центрирования (иначе Wayland игнорирует позицию)
            self.root.geometry(f"{int(width)}x{int(height)}")
        else:
            # На обычных системах (CachyOS, Windows, etc.)
            width = base_width
            height = base_height
            self.root.geometry(f"{width}x{height}")

        self.root.configure(bg='#182030')
        self.root.transient(self.parent)

        # Устанавливаем WM_CLASS
        try:
            self.root.wm_class("AdGuardVPNManager")
        except:
            pass

        # Устанавливаем иконку
        try:
            manager_dir = os.path.expanduser("~/AdGuard VPN Manager")
            icon_path = os.path.join(manager_dir, "ico/adguard.png")
            if os.path.exists(icon_path):
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
        except Exception as e:
            print(f"Не удалось установить иконку: {e}")

    def create_widgets(self):
        """Создает элементы интерфейса"""
        # Основной фрейм
        main_frame = tk.Frame(self.root, bg='#182030', padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        title_label = tk.Label(main_frame,
                              text="Поддержать разработчика",
                              font=("Arial", 16, "bold"),
                              bg='#182030', fg='white')
        title_label.pack(pady=(0, 15))

        # Текст с благодарностью
        thank_you_text = (
            "Спасибо, что используете\nAdGuard VPN Manager!\n\n"
            "Если вам нравится проект и вы хотите поддержать его развитие, "
            "вы можете сделать это через систему донатов."
        )

        thank_you_label = tk.Label(main_frame,
                                  text=thank_you_text,
                                  font=('Arial', 11),
                                  bg='#182030',
                                  fg='white',
                                  wraplength=350,
                                  justify=tk.CENTER)
        thank_you_label.pack(pady=(0, 15))

        # Фрейм для QR кода
        qr_frame = tk.Frame(main_frame, bg='#182030')
        qr_frame.pack(pady=10)

        # Загружаем QR код
        try:
            # Путь к QR коду
            manager_dir = os.path.expanduser("~/AdGuard VPN Manager")
            qr_path = os.path.join(manager_dir, "utils/qr.png")

            if os.path.exists(qr_path):
                self.qr_image = tk.PhotoImage(file=qr_path)
                qr = tk.Label(qr_frame, image=self.qr_image, bg='#182030')
                qr.pack(side=tk.LEFT, padx=(0, 10))
            else:
                raise FileNotFoundError("QR код не найден")

        except Exception as e:
            # Если QR код не найден, показываем сообщение
            error_label = tk.Label(qr_frame,
                                  text="QR-код не найден",
                                  font=('Arial', 10),
                                  bg='#182030',
                                  fg='#ff3b30',
                                  justify=tk.CENTER)
            error_label.pack()

        # Текст под QR кодом
        qr_caption = tk.Label(main_frame,
                             text="Отсканируйте QR-код для перевода",
                             font=('Arial', 10),
                             bg='#182030',
                             fg='#5BA06A',
                             justify=tk.CENTER)
        qr_caption.pack(pady=(5, 15))

        # Кнопка закрытия
        button_frame = tk.Frame(main_frame, bg='#182030')
        button_frame.pack(fill=tk.X, pady=(10, 0))

        close_style = {
            'font': ('Arial', 10),
            'bg': '#15354D',
            'fg': 'white',
            'bd': 0,
            'padx': 20,
            'pady': 8,
            'width': 12,
            'highlightthickness': 0,
            'cursor': 'hand2'
        }

        close_btn = create_hover_button(button_frame,
                                       text="Закрыть",
                                       command=self.root.destroy,
                                       **close_style)
        close_btn.pack()

        # Обработка клавиш
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        self.root.bind('<Return>', lambda e: self.root.destroy())

    def create_donation_link(self, parent, icon, text, command_func):
        """Создает ссылку для доната"""
        link_frame = tk.Frame(parent, bg='#182030')
        link_frame.pack(anchor=tk.CENTER, pady=5)

        # Иконка
        icon_label = tk.Label(link_frame,
                             text=icon,
                             font=('Arial', 12),
                             bg='#182030',
                             fg='#3CAA3C',
                             cursor='hand2')
        icon_label.pack(side=tk.LEFT)
        icon_label.bind("<Button-1>", command_func)

        # Текст
        text_label = tk.Label(link_frame,
                             text=text,
                             font=('Arial', 11, 'underline'),
                             bg='#182030',
                             fg='#3CAA3C',
                             cursor='hand2')
        text_label.pack(side=tk.LEFT, padx=(5, 0))
        text_label.bind("<Button-1>", command_func)

        # Эффекты при наведении
        for label in [icon_label, text_label]:
            label.bind("<Enter>", lambda e, l=text_label: l.config(fg='#4d8058'))
            label.bind("<Leave>", lambda e, l=text_label: l.config(fg='#3CAA3C'))

    def run(self):
        """Запускает окно"""
        self.root.wait_window()
