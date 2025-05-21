import re
import pdfplumber
from datetime import datetime

def parse_pdf(file_path):
    try:
        with pdfplumber.open(file_path) as pdf:
            full_text = "\n".join([page.extract_text() or "" for page in pdf.pages])

            # Универсальные регулярные выражения
            patterns = {
                "date": {
                    "regex": r"(Дата[\s\S]*?)(\d{2}[\.\/]\d{2}[\.\/]\d{4}[\s,]+?\d{2}:\d{2})",
                    "group": 2
                },
                "amount": {
                    "regex": r"(Сумма[\s\S]*?)([\d\s,]+\.?\d*)\s*(KGS|сом)",
                    "group": 2
                },
                "recipient": {
                    "regex": r"(Получатель|Отправитель|Получателя)[\s:]*([^\n]+)",
                    "group": 2
                },
                "serial": {
                    "regex": r"(Номер квитанции|Квитанция №|Серийный номер)[\s:]*([A-Z0-9-]+)",
                    "group": 2
                }
            }

            parsed_data = {}
            for key, config in patterns.items():
                match = re.search(config["regex"], full_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    parsed_data[key] = match.group(config["group"]).strip()
                else:
                    return None

            # Нормализация данных
            try:
                # Дата
                date_formats = [
                    "%d.%m.%Y %H:%M", 
                    "%d/%m/%Y %H:%M", 
                    "%Y-%m-%d %H:%M"
                ]
                parsed_date = None
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(parsed_data["date"], fmt)
                        break
                    except ValueError:
                        continue
                if not parsed_date:
                    return None
                parsed_data["date"] = parsed_date.strftime("%Y-%m-%d %H:%M")

                # Сумма
                amount_str = (
                    parsed_data["amount"]
                    .replace(" ", "")
                    .replace(",", ".")
                )
                parsed_data["amount"] = float(amount_str)

                # Получатель
                parsed_data["recipient"] = parsed_data["recipient"].title()

                return parsed_data

            except Exception as e:
                print(f"Ошибка нормализации: {str(e)}")
                return None

    except Exception as e:
        print(f"Ошибка парсинга PDF: {str(e)}")
        return None