import tkinter as tk

def create_hover_button(parent, text, command, **kwargs):
    """
    Создает кнопку с hover-эффектом

    Args:
        parent: родительский виджет
        text: текст кнопки
        command: функция-обработчик
        **kwargs: дополнительные параметры для Button

    Returns:
        tk.Button: кнопка с hover-эффектом
    """

    # Стандартные стили для кнопок AdGuard VPN Manager
    default_style = {
        'font': ('Arial', 11),
        'bg': '#15354D',
        'fg': 'white',
        'bd': 0,
        'relief': tk.FLAT,
        'padx': 12,
        'pady': 12,
        'width': 15,
        'anchor': 'center',
        'highlightthickness': 0,
        'cursor': 'hand2',
        'activebackground': '#5BA06A',  # Важно: цвет при нажатии
        'activeforeground': 'white',     # Важно: цвет текста при нажатии
    }

    # Объединяем стандартные стили с переданными параметрами
    final_style = default_style.copy()
    final_style.update(kwargs)

    # Создаем кнопку
    btn = tk.Button(parent, text=text, command=command, **final_style)

    # Hover-эффект - меняем на #5BA06A при наведении
    def on_enter(e):
        btn.config(bg='#5BA06A', fg='white', activebackground='#5BA06A')

    def on_leave(e):
        btn.config(bg=final_style['bg'], fg=final_style['fg'], activebackground='#5BA06A')

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

    return btn

def create_hover_button_for_manager(parent, text, command, **kwargs):
    """
    Создает кнопку с hover-эффектом

    Args:
        parent: родительский виджет
        text: текст кнопки
        command: функция-обработчик
        **kwargs: дополнительные параметры для Button

    Returns:
        tk.Button: кнопка с hover-эффектом
    """

    # Стандартные стили для кнопок AdGuard VPN Manager
    default_style = {
        'font': ('Arial', 11),
        'bg': '#15354D',
        'fg': 'white',
        'bd': 0,
        'relief': tk.FLAT,
        'padx': 12,
        'pady': 12,
        'width': 17,
        'anchor': 'center',
        'highlightthickness': 0,
        'cursor': 'hand2',
        'width': 18,
        'activebackground': '#5BA06A',  # Важно: цвет при нажатии
        'activeforeground': 'white',     # Важно: цвет текста при нажатии
    }

    # Объединяем стандартные стили с переданными параметрами
    final_style = default_style.copy()
    final_style.update(kwargs)

    # Создаем кнопку
    btn = tk.Button(parent, text=text, command=command, **final_style)

    # Hover-эффект - меняем на #5BA06A при наведении
    def on_enter(e):
        btn.config(bg='#5BA06A', fg='white', activebackground='#5BA06A')

    def on_leave(e):
        btn.config(bg=final_style['bg'], fg=final_style['fg'], activebackground='#5BA06A')

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

    return btn

def apply_hover_effect(button, hover_bg='#5BA06A', hover_fg='white'):
    """
    Применяет hover-эффект к существующей кнопке

    Args:
        button: кнопка tk.Button
        hover_bg: цвет фона при наведении (#5BA06A)
        hover_fg: цвет текста при наведении
    """
    original_bg = button.cget('bg')
    original_fg = button.cget('fg')

    def on_enter(e):
        button.config(bg=hover_bg, fg=hover_fg, activebackground=hover_bg)

    def on_leave(e):
        button.config(bg=original_bg, fg=original_fg, activebackground=hover_bg)

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    button.config(
        cursor='hand2',
        activebackground=hover_bg,
        activeforeground=hover_fg
    )

def lighten_color(hex_color, percent):
    """
    Осветляет hex-цвет на указанный процент
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    r = min(255, r + int(r * percent / 100))
    g = min(255, g + int(g * percent / 100))
    b = min(255, b + int(b * percent / 100))

    return f'#{r:02x}{g:02x}{b:02x}'
