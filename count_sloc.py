import os
import openpyxl
from pathlib import Path

def is_code_line(line: str) -> bool:
    """Возвращает True, если строка считается строкой кода."""
    stripped = line.strip()
    # Пустая строка или только комментарий — не код
    if not stripped or stripped.startswith('#'):
        return False
    return True

def count_code_lines(filepath: Path) -> int:
    """Считает количество строк кода в .py файле."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return sum(1 for line in lines if is_code_line(line))
    except (UnicodeDecodeError, OSError) as e:
        print(f"⚠️ Не удалось прочитать файл {filepath}: {e}")
        return 0

def main():
    current_dir = Path('.')
    py_files = list(current_dir.rglob('*.py'))

    if not py_files:
        print("❌ В проекте не найдено .py файлов.")
        return

    # Создаём Excel-книгу
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Python SLOC"
    sheet.append(["Папка", "Файл", "Строки кода"])

    total_lines = 0
    for file_path in py_files:
        lines = count_code_lines(file_path)
        folder = str(file_path.parent)
        filename = file_path.name
        sheet.append([folder, filename, lines])
        total_lines += lines

    # Добавим итоговую строку
    sheet.append([])
    sheet.append(["ИТОГО", "", total_lines])

    # Сохраняем
    output_file = "code_lines.xlsx"
    workbook.save(output_file)
    print(f"✅ Результат сохранён в {output_file}")
    print(f"📊 Всего строк кода: {total_lines}")

if __name__ == "__main__":
    main()