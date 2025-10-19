import tkinter as tk
import subprocess
import re
from datetime import datetime
from ui.components.dialogs import show_message_dialog

class LicenseWindow:
    def __init__(self, parent):
        self.parent = parent

    def clean_license_output(self, text):
        """Удаляет escape-символы из вывода"""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        cleaned = ansi_escape.sub('', text)
        return cleaned.strip()

    def parse_license_info(self, text):
        """Парсит и форматирует информацию о лицензии"""
        cleaned = self.clean_license_output(text)
        lines = cleaned.split('\n')

        # Извлекаем информацию
        email = None
        license_type = "Free"
        devices = "2"
        traffic_left = None
        expiry_date = None

        for line in lines:
            line = line.strip()

            # Email пользователя
            if "Logged in as" in line:
                email_match = re.search(r'Logged in as (.+)$', line)
                if email_match:
                    email = email_match.group(1).strip()

            # Тип лицензии
            if "FREE version" in line:
                license_type = "Free"
            elif "PREMIUM" in line.upper():
                license_type = "Premium"

            # Количество устройств
            if "devices simultaneously" in line:
                devices_match = re.search(r'Up to (\d+) devices', line)
                if devices_match:
                    devices = devices_match.group(1)

            # Оставшийся трафик
            if "GB left" in line or "MB left" in line:
                traffic_match = re.search(r'You have (\d+\.?\d*)\s*(GB|MB) left', line)
                if traffic_match:
                    amount = traffic_match.group(1)
                    unit = traffic_match.group(2)
                    traffic_left = f"{amount} {unit}"

            # Дата окончания
            if "renewed on" in line or "expires on" in line:
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
                if date_match:
                    expiry_date = date_match.group(1)

        # Форматируем вывод в зависимости от типа лицензии
        if license_type == "Premium":
            return self.format_premium_info(email, devices, expiry_date)
        else:
            return self.format_free_info(email, devices, traffic_left)

    def format_free_info(self, email, devices, traffic_left):
        """Форматирует информацию для Free версии"""
        info_lines = [
            "🎫 БЕСПЛАТНАЯ ВЕРСИЯ",
            "",
            f"👤 Пользователь: {email}" if email else "👤 Пользователь: Не указан",
            f"📱 До {devices} устройств одновременно",
            ""
        ]

        if traffic_left:
            info_lines.append(f"📊 Осталось трафика: {traffic_left}")
        else:
            info_lines.append("📊 Лимит трафика: 3 ГБ в месяц")

        return '\n'.join(info_lines)

    def format_premium_info(self, email, devices, expiry_date):
        """Форматирует информацию для Premium версии"""
        info_lines = [
            "🌟 ПРЕМИУМ ВЕРСИЯ",
            "",
            f"👤 Пользователь: {email}" if email else "👤 Пользователь: Не указан",
            f"📱 До {devices} устройств одновременно",
            ""
        ]

        if expiry_date:
            days_left = self.get_days_until_expiry(expiry_date)
            try:
                if days_left > 0:
                    info_lines.append(f"📅 Подписка активна до: {expiry_date}")
                    info_lines.append(f"⏳ Осталось дней: {days_left}")
                else:
                    info_lines.append(f"⚠️ Подписка истекла: {expiry_date}")
            except:
                info_lines.append(f"📅 Дата окончания: {expiry_date}")
        else:
            info_lines.append("📅 Подписка активна")

        return '\n'.join(info_lines)

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

    def get_license_info(self):
        """Получает информацию о лицензии"""
        try:
            result = subprocess.run(
                ['adguardvpn-cli', 'license'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return self.parse_license_info(result.stdout)
            else:
                return "❌ Не удалось получить информацию о лицензии\n\n" \
                       "Возможные причины:\n" \
                       "• Вы не авторизованы\n" \
                       "• AdGuard VPN не установлен\n" \
                       "• Проблема с подключением"

        except subprocess.TimeoutExpired:
            return "⏰ Таймаут при получении информации о лицензии\n\n" \
                   "Попробуйте позже или проверьте подключение."
        except Exception as e:
            return f"❌ Ошибка: {str(e)}\n\n" \
                   "Проверьте установлен ли AdGuard VPN."

    def run(self):
        """Запускает окно с информацией о лицензии"""
        license_info = self.get_license_info()
        show_message_dialog(self.parent, "Информация о лицензии", license_info, "info")
