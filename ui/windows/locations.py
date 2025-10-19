import tkinter as tk
from tkinter import ttk
import subprocess
import re
import os
from ui.components.dialogs import show_message_dialog
from ui.components.button_styler import create_hover_button, apply_hover_effect


class LocationSelectionWindow:
    def __init__(self, parent):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.setup_window_properties()
        self.root.title("Выбор локации")
        self.root.geometry("520x400")
        self.root.configure(bg='#182030')
        self.root.transient(parent)
        self.root.grab_set()

        try:
            from tkinter import ttk
            style = ttk.Style()
            style.theme_use('clam')  # или 'alt', 'classic' - простые темы
        except:
            pass

        self.selected_location = None
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

        title_label = tk.Label(main_frame, text="Выберите локацию для подключения",
                              font=("Arial", 16, "bold"), fg='white', bg='#182030')
        title_label.pack(pady=(0, 20))

        # Фрейм для списка локаций
        list_frame = tk.Frame(main_frame, bg='#182030')
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Создаем Treeview для отображения локаций
        columns = ("ISO", "Country", "City", "Ping")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)

        # Основной стиль таблицы
        style = ttk.Style()
        style.configure("Treeview",
                       background="#182030",
                       fieldbackground="#182030",
                       foreground="white",
                       font=('Arial', 11),
                       borderwidth=0,
                       relief='flat')

        # Стиль заголовка таблицы
        style.configure("Treeview.Heading",
                       background="#15354D",
                       foreground="white",
                       font=('Arial', 11, 'bold'),
                       borderwidth=0,
                       relief='flat')

        # Отключаем hover эффекты для заголовков
        style.map("Treeview.Heading",
            background=[('active', '#15354D')],
            foreground=[('active', 'white')])

        # Стилизация скроллбара
        style.configure("Custom.Vertical.TScrollbar",
                       background="#2A4466",  # Цвет ползунка
                       troughcolor="#0F1A2F",  # Цвет фона (дорожки)
                       bordercolor="#182030",
                       arrowcolor="white",
                       gripcount=0)

        style.map("Custom.Vertical.TScrollbar",
                 background=[('active', '#3A5A88'),  # Цвет при наведении
                           ('pressed', '#4A6AA0')])  # Цвет при нажатии

        # Стиль для выделенной строки
        style.map("Treeview",
                background=[('selected', '#5BA06A')],  # ← Цвет выделения
                foreground=[('selected', 'white')])

        # Создаем Treeview для отображения локаций
        columns = ("ISO", "Country", "City", "Ping")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10,
                                selectmode="browse")  # ← Режим выбора одной строки

        # Настраиваем заголовки
        self.tree.heading("ISO", text="ISO")
        self.tree.heading("Country", text="Страна")
        self.tree.heading("City", text="Город")
        self.tree.heading("Ping", text="Пинг")

        # Настраиваем ширину колонок
        self.tree.column("ISO", width=50, anchor="center")
        self.tree.column("Country", width=150)
        self.tree.column("City", width=150)
        self.tree.column("Ping", width=50, anchor="center")

        # Кастомный скроллбар с измененным цветом
        scrollbar = ttk.Scrollbar(list_frame,
                                 orient="vertical",
                                 command=self.tree.yview,
                                 style="Custom.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

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

        choose_btn = create_hover_button(btn_frame, text="Выбрать",
                                         command=self.select_location, **button_style)
        choose_btn.grid(row=0, column=1, padx=(0, 10))

        back_btn = create_hover_button(btn_frame, text="Назад",
                                       command=self.close_window, **button_style)
        back_btn.grid(row=0, column=2)

        # Центрируем весь фрейм с кнопками
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)
        btn_frame.grid_columnconfigure(3, weight=1)

    def load_locations(self):
        """Загружает список локаций через adguardvpn-cli list-locations"""
        try:
            # Очищаем таблицу
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Получаем список локаций
            result = subprocess.run(
                ['adguardvpn-cli', 'list-locations'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                self.parse_locations_output(result.stdout)
            else:
                self.root.after(0, lambda: show_message_dialog(self.root, "Ошибка", "Не удалось получить список локаций", "error"))

        except Exception as e:
            self.root.after(0, lambda: show_message_dialog(self.root, "Ошибка", f"Ошибка при получении локаций: {str(e)}", "error"))

    def parse_locations_output(self, output):
        """Парсит вывод команды list-locations"""
        # Очищаем вывод от ANSI escape sequences
        clean_output = self.clean_ansi_codes(output)

        lines = clean_output.strip().split('\n')
        header_found = False

        for line in lines:
            line = line.strip()

            # Пропускаем пустые строки
            if not line:
                continue

            # Ищем заголовок таблицы
            if 'ISO' in line and 'COUNTRY' in line and 'CITY' in line:
                header_found = True
                continue

            # Если нашли заголовок, парсим данные до конца таблицы
            if header_found:
                # Останавливаем парсинг когда начинаются инструкции
                if 'You can connect to a location by running' in line:
                    break
                if 'You are using a FREE version' in line:
                    break
                if line.startswith('===') or line.startswith('---'):
                    continue

                # Парсим строку с локацией
                location_data = self.parse_table_line(line)
                if location_data:
                    iso, country, city, ping = location_data
                    self.tree.insert("", "end", values=(iso, country, city, ping))

    def clean_ansi_codes(self, text):
        """Очищает текст от ANSI escape sequences"""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def parse_table_line(self, line):
        """Парсит строку таблицы с фиксированными колонками"""
        try:
            # Сначала очищаем от ANSI кодов на всякий случай
            line = self.clean_ansi_codes(line)

            # Убираем лишние пробелы
            line = ' '.join(line.split())

            # Разбиваем на части
            parts = line.split()
            if len(parts) < 4:
                return None

            # ISO код - первые 2 символа
            iso = parts[0]

            # Пинг - последнее число
            ping = parts[-1]
            if not ping.isdigit():
                return None

            # Все что между ISO и ping - это страна и город
            middle_parts = parts[1:-1]

            if len(middle_parts) < 2:
                return None

            # Город - последнее слово в middle_parts
            city = middle_parts[-1]
            # Страна - все остальное
            country = ' '.join(middle_parts[:-1])

            return (iso, country, city, ping)

        except Exception as e:
            print(f"Ошибка парсинга строки: '{line}' - {e}")
            return None

    def select_location(self):
        selected_item = self.tree.selection()
        if not selected_item:
            return

        item = self.tree.item(selected_item[0])
        location_data = item['values']

        # Используем город как локацию для подключения
        self.selected_location = location_data[2]  # Город
        self.root.destroy()

    def close_window(self):
        self.selected_location = None
        self.root.destroy()

    def run(self):
        self.load_locations()
        self.root.wait_window()
        return self.selected_location
