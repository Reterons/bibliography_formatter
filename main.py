import argparse
import json
import sys
from pathlib import Path
from bibliography_manager import BibliographyManager
from citation_style import CitationStyle
from gui import TkinterGUI

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("Графический интерфейс недоступен. Установите tkinter (GUI будет отключен).")

def main():
    parser = argparse.ArgumentParser(description='Программа форматирования библиографии')
    parser.add_argument('--input', type=str, help='Путь к входному DOCX файлу')
    parser.add_argument('--output', type=str, help='Путь для сохранения результата')
    parser.add_argument('--style', type=str, help='JSON файл со стилем форматирования')

    args = parser.parse_args()

    if not GUI_AVAILABLE:
        print("Ошибка: графический интерфейс недоступен")
        return

    manager = BibliographyManager()

    if args.style and Path(args.style).exists():
        try:
            with open(args.style, 'r', encoding='utf-8') as f:
                style_data = json.load(f)
                style = CitationStyle.from_dict(style_data)
                manager.current_style = style
        except Exception as e:
            print(f"Ошибка загрузки стиля: {e}")

    if args.input and Path(args.input).exists():
        try:
            items = manager.parse_docx(args.input)
            for item in items:
                manager.add_item(item)
            print(f"Загружено {len(items)} записей из {args.input}")
        except Exception as e:
            print(f"Ошибка загрузки файла: {e}")

    if args.input and args.output and manager.current_style:
        try:
            manager.save_to_docx(args.output, highlight_missing=True)
            print(f"Сохранено в {args.output}")
            return
        except Exception as e:
            print(f"Ошибка экспорта: {e}")

    if not GUI_AVAILABLE:
        print("GUI недоступен: tkinter не установлен. Используйте CLI-режим или установите tkinter.")
        return
    gui = TkinterGUI(manager)
    gui.run()

if __name__ == "__main__":
    main()