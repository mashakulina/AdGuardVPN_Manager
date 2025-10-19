import tkinter as tk
from ui.components.button_styler import create_hover_button, apply_hover_effect

def show_message_dialog(parent, title, message, message_type="info"):
    import platform, subprocess, os
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.configure(bg='#182030')
    dialog.transient(parent)
    dialog.grab_set()

    def is_steamdeck():
        """Проверяет, запущено ли приложение на Steam Deck или SteamOS"""
        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    os_info = f.read().lower()
                    if "steamos" in os_info or "steam deck" in os_info:
                        return True
            sys_name = platform.uname().machine.lower()
            if "steam" in sys_name or "deck" in sys_name:
                return True
            result = subprocess.run(["ps", "-A"], capture_output=True, text=True)
            if "gamescope" in result.stdout.lower():
                return True
        except:
            pass
        return False

    # Определяем размеры экрана
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()

    # Рассчитываем параметры текста
    lines = message.count('\n') + 1
    max_line_length = max(len(line) for line in message.split('\n'))

    # Минимальные размеры
    min_width = 350
    min_height = 110

    # Автоувеличение в зависимости от длины
    if max_line_length <= 40:
        base_width = min_width
    else:
        extra_chars = max_line_length - 40
        base_width = min(600, min_width + extra_chars * 10)

    base_height = min_height + (lines - 1) * 20

    # Если экран в портретной ориентации — поменяем местами
    if screen_height > screen_width:
        screen_width, screen_height = screen_height, screen_width

    # Сохраняем размеры в переменные, но применим позже
    if is_steamdeck():
        # На Steam Deck — чуть меньше, чтобы влезало в экран даже с рамкой
        width = min(base_width + 30, screen_width + 20)
        height = min(base_height + 40, screen_height + 40)
        # Без центрирования (иначе Wayland игнорирует позицию)
        dialog.geometry(f"{int(width)}x{int(height)}")
    else:
        # На обычных системах (CachyOS, Windows, etc.)
        width = base_width
        height = base_height
        dialog.geometry(f"{width}x{height}")

    # Иконка и цвет в зависимости от типа
    if message_type == "error":
        color = "#ff3b30"
    elif message_type == "warning":
        color = "#ff9500"
    elif message_type == "success":
        color = "#30d158"
    else:  # info
        color = "#0a84ff"

    # # Заголовок
    # title_frame = tk.Frame(dialog, bg='#182030', pady=10)
    # title_frame.pack(fill=tk.X)
    #
    # tk.Label(title_frame, text=title, font=("Arial", 12, "bold"),
    #         bg='#182030', fg='white').pack()

    # Сообщение
    message_frame = tk.Frame(dialog, bg='#182030', pady=10)
    message_frame.pack(fill=tk.BOTH, expand=True, padx=20)

    # Динамический wraplength в зависимости от ширины окна
    wraplength = int(width) - 60  # Отступы по 30px с каждой стороны

    message_label = tk.Label(message_frame, text=message, font=("Arial", 11),
                            bg='#182030', fg='white', wraplength=wraplength,
                            justify=tk.LEFT)
    message_label.pack(anchor=tk.W, fill=tk.BOTH, expand=True, pady=(10, 0))

    # Кнопка OK
    button_style = {
        'font': ('Arial', 10),
        'bg': '#15354D',
        'fg': 'white',
        'bd': 0,
        'padx': 20,
        'pady': 8,
        'width': 10,
        'highlightthickness': 0,
        'cursor': 'hand2'
    }

    button_frame = tk.Frame(dialog, bg='#182030', pady=10)
    button_frame.pack(fill=tk.X)

    ok_button = create_hover_button(button_frame, text="OK", command=dialog.destroy, **button_style)
    ok_button.pack(pady=(0, 10))

    # Закрытие по Enter
    dialog.bind('<Return>', lambda e: dialog.destroy())
    ok_button.focus_set()


def show_question_dialog(parent, title, message):
    """Показывает кастомный вопрос с Yes/No"""
    result = [False]

    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.configure(bg='#182030')
    dialog.transient(parent)
    dialog.grab_set()

    # Рассчитываем параметры текста
    lines = message.count('\n') + 1
    max_line_length = max(len(line) for line in message.split('\n'))

    # Минимальные размеры
    min_width = 350
    min_height = 95

    # Ширина: увеличиваем только если текст действительно длинный
    if max_line_length <= 40:
        width = min_width  # 350
    else:
        # Плавное увеличение для очень длинных строк
        extra_chars = max_line_length - 40
        width = min(600, min_width + extra_chars * 10)  # +4px за каждый лишний символ

    # Высота: увеличиваем только при многострочном тексте
    height = min_height + (lines - 1) * 25  # +25px за каждую дополнительную строку

    dialog.geometry(f"{int(width)}x{int(height)}")
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    dialog.maxsize(screen_width + 30, screen_height + 30)

    # Сообщение
    message_frame = tk.Frame(dialog, bg='#182030', pady=5)
    message_frame.pack(fill=tk.BOTH, expand=True, padx=5)

    message_label = tk.Label(message_frame, text=message, font=("Arial", 11),
                            bg='#182030', fg='white', justify=tk.CENTER, anchor=tk.CENTER)
    message_label.pack(expand=True, fill=tk.BOTH)

    # Кнопки
    button_frame = tk.Frame(dialog, bg='#182030', pady=15)
    button_frame.pack(fill=tk.X)

    def on_yes():
        result[0] = True
        dialog.destroy()

    def on_no():
        result[0] = False
        dialog.destroy()

    button_style = {
        'font': ('Arial', 10),
        'bg': '#15354D',
        'fg': 'white',
        'bd': 0,
        'padx': 10,
        'pady': 6,
        'width': 8,
        'highlightthickness':0,
        'cursor': 'hand2'
    }

    yes_btn = create_hover_button(button_frame, text="Да",
                                  command=on_yes, **button_style)
    yes_btn.grid(row=0, column=1, padx=(0, 10))

    no_btn = create_hover_button(button_frame, text="Нет",
                                 command=on_no, **button_style)
    no_btn.grid(row=0, column=2)

    # Центрируем весь фрейм с кнопками
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)
    button_frame.grid_columnconfigure(2, weight=1)
    button_frame.grid_columnconfigure(3, weight=1)

    # Закрытие по клавишам
    dialog.bind('<Return>', lambda e: on_yes())
    dialog.bind('<Escape>', lambda e: on_no())

    dialog.wait_window()
    return result[0]
