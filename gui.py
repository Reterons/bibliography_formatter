import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import font as tkfont
import json
import re
from pathlib import Path
from bibliography_manager import BibliographyManager
from citation_style import CitationStyle
from author_formatter import AuthorFormatter, AuthorFormat, AuthorFormatConfig
from author import Author
from bibliography_manager import ConferencePaper, ElectronicResource, Article, Book

class FieldSettingsDialog:
    def __init__(self, parent, field_name, style):
        self.parent = parent
        self.field_name = field_name
        self.style = style

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Настройка поля: {field_name}")
        self.dialog.geometry("450x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill='both', expand=True)

        ttk.Label(main_frame, text=f"Настройки для поля: {self.field_name}",
                 font=('Arial', 12, 'bold')).pack(pady=(0, 10))

        ttk.Label(main_frame, text="Разделитель после поля:").pack(anchor='w', pady=(5, 0))

        separator_frame = ttk.Frame(main_frame)
        separator_frame.pack(fill='x', pady=5)

        self.separator_var = tk.StringVar(value=self.style.field_separators.get(self.field_name, ". "))

        separators = {
            ". ": "Точка с пробелом",
            ". ": "Точка",
            ", ": "Запятая с пробелом",
            ", ": "Запятая",
            "; ": "Точка с запятой",
            ": ": "Двоеточие",
            " ": "Пробел",
            "": "Без разделителя"
        }

        separator_combo = ttk.Combobox(separator_frame, textvariable=self.separator_var,
                                      values=list(separators.keys()))
        separator_combo.pack(fill='x')

        self.quotes_warning = ttk.Label(main_frame, text="", foreground="blue")
        self.quotes_warning.pack(anchor='w', pady=2)

        self.prefix_var = tk.BooleanVar(value=self.style.field_prefixes.get(self.field_name, False))

        prefix_fields = ['volume', 'issue', 'pages', 'doi', 'url']
        if self.field_name in prefix_fields:
            ttk.Checkbutton(main_frame, text="Добавить префикс",
                          variable=self.prefix_var).pack(anchor='w', pady=10)

            prefix_dict = {
                'volume': 'vol.',
                'issue': 'no.',
                'pages': 'pp.',
                'doi': 'doi:',
                'url': 'URL:'
            }
            if self.field_name in prefix_dict:
                ttk.Label(main_frame, text=f"Префикс: {prefix_dict[self.field_name]}").pack(anchor='w')

        ttk.Label(main_frame, text="Форматирование текста:").pack(anchor='w', pady=(10, 0))

        format_frame = ttk.Frame(main_frame)
        format_frame.pack(fill='x', pady=5)

        self.format_var = tk.StringVar(value=self.style.field_formatters.get(self.field_name, ""))
        formats = {
            "": "Нет",
            "italic": "Курсив",
            "bold": "Жирный",
            "quotes": "В кавычках",
            "brackets": "В квадратных скобках"
        }

        format_combo = ttk.Combobox(format_frame, textvariable=self.format_var,
                                   values=list(formats.keys()))
        format_combo.pack(fill='x')
        format_combo.bind('<<ComboboxSelected>>', self.on_format_changed)

        self.quotes_example = ttk.Label(main_frame, text="", font=('Arial', 9, 'italic'))
        self.quotes_example.pack(anchor='w', pady=5)

        self.on_format_changed()

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side='bottom', fill='x', pady=(20, 0))

        ttk.Button(button_frame, text="Сохранить",
                  command=self.save_settings).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Отмена",
                  command=self.dialog.destroy).pack(side='right')

    def on_format_changed(self, event=None):
        format_type = self.format_var.get()

        if format_type in ("quotes", "brackets"):
            separator = self.separator_var.get()
            if separator.strip() in [',', ', ']:
                self.quotes_warning.config(
                    text="Запятая будет помещена внутри оформления (кавычки/скобки), после закрывающего знака будет пробел"
                )
                self.quotes_example.config(
                    text='Пример: "Заголовок," Год. Журнал'
                )
            else:
                self.quotes_warning.config(
                    text="Разделитель будет помещен снаружи кавычек"
                )
                if separator.strip() == '.':
                    self.quotes_example.config(
                        text='Пример: "Заголовок". Год. Журнал'
                    )
                elif separator.strip() == ';':
                    self.quotes_example.config(
                        text='Пример: "Заголовок"; Год. Журнал'
                    )
                else:
                    self.quotes_example.config(
                        text=f'Пример: "Заголовок"{separator}Год. Журнал'
                    )
        else:
            self.quotes_warning.config(text="")
            self.quotes_example.config(text="")

    def save_settings(self):
        separator = self.separator_var.get()
        self.style.set_field_separator(self.field_name, separator)

        self.style.set_field_prefix(self.field_name, self.prefix_var.get())

        format_value = self.format_var.get()
        if format_value:
            self.style.set_field_format(self.field_name, format_value)
        elif self.field_name in self.style.field_formatters:
            del self.style.field_formatters[self.field_name]

        self.dialog.destroy()

class AuthorTab(ttk.Frame):
    def __init__(self, parent, manager, config_callback=None):
        super().__init__(parent)
        self.manager = manager
        self.config_callback = config_callback

        self.current_config = AuthorFormatConfig.get_preset(AuthorFormat.LAST_FIRST_INITIALS)
        self.author_formatter = AuthorFormatter(self.current_config)

        self.test_authors = [
            Author("Иванов", "Иван", "Иванович"),
            Author("Петров", "Петр", "Петрович"),
            Author("Сидоров", "Сидор", "Сидорович"),
            Author("Кузнецов", "Алексей", "Николаевич")
        ]

        self.format_options = [
            (AuthorFormat.LAST_FIRST_INITIALS, "Фамилия И.О. (Иванов И.И.)"),
            (AuthorFormat.FIRST_LAST_INITIALS, "И.О. Фамилия (И.И. Иванов)"),
            (AuthorFormat.LAST_COMMA_FIRST, "Фамилия, И.О. (Иванов, И.И.)"),
            (AuthorFormat.FIRST_INITIAL_LAST, "И. Фамилия (И. Иванов)"),
            (AuthorFormat.LAST_ONLY, "Только фамилия (Иванов)"),
            (AuthorFormat.CUSTOM, "Пользовательский формат")
        ]

        self.format_display_to_value = {desc: value for value, desc in self.format_options}
        self.format_value_to_display = {value: desc for value, desc in self.format_options}

        self.setup_ui()
        self.update_preview()

    def setup_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        left_frame = ttk.LabelFrame(main_frame, text="Настройка формата авторов", padding=10)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        self.setup_format_settings(left_frame)

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))

        preview_frame = ttk.LabelFrame(right_frame, text="Предпросмотр", padding=10)
        preview_frame.pack(fill='both', expand=True, pady=(0, 10))

        self.setup_preview(preview_frame)

        order_frame = ttk.LabelFrame(right_frame, text="Порядок частей имени", padding=10)
        order_frame.pack(fill='both', expand=True)

        self.setup_order_editor(order_frame)

    def setup_format_settings(self, parent):
        ttk.Label(parent, text="Предустановленный формат:").grid(row=0, column=0, sticky='w', pady=(0, 5))

        self.format_var = tk.StringVar(value=self.format_value_to_display[AuthorFormat.LAST_FIRST_INITIALS])
        format_combo = ttk.Combobox(parent, textvariable=self.format_var, state='readonly')
        format_combo['values'] = [desc for _, desc in self.format_options]
        format_combo.grid(row=0, column=1, sticky='ew', pady=(0, 5))
        format_combo.bind('<<ComboboxSelected>>', self.on_format_changed)

        ttk.Label(parent, text="Разделитель авторов:").grid(row=1, column=0, sticky='w', pady=5)
        self.delimiter_var = tk.StringVar(value=", ")
        ttk.Entry(parent, textvariable=self.delimiter_var, width=10).grid(row=1, column=1, sticky='w', pady=5)

        ttk.Label(parent, text='"И" для последнего:').grid(row=2, column=0, sticky='w', pady=5)
        self.and_word_var = tk.StringVar(value=" и ")
        ttk.Entry(parent, textvariable=self.and_word_var, width=10).grid(row=2, column=1, sticky='w', pady=5)

        ttk.Label(parent, text="Лимит авторов (и др.):").grid(row=3, column=0, sticky='w', pady=5)
        self.et_al_var = tk.IntVar(value=3)
        ttk.Spinbox(parent, from_=1, to=10, textvariable=self.et_al_var, width=5).grid(row=3, column=1, sticky='w', pady=5)

        self.include_et_al_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="Включать 'и др.'",
                      variable=self.include_et_al_var).grid(row=4, column=0, columnspan=2, sticky='w', pady=5)

        ttk.Label(parent, text="Формат инициалов:").grid(row=5, column=0, sticky='w', pady=(10, 5))

        init_frame = ttk.Frame(parent)
        init_frame.grid(row=5, column=1, sticky='w', pady=(10, 5))

        self.initials_dot_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(init_frame, text="Точки", variable=self.initials_dot_var).pack(side='left', padx=(0, 10))

        self.initials_space_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(init_frame, text="Пробелы", variable=self.initials_space_var).pack(side='left')

        self.template_frame = ttk.LabelFrame(parent, text="Пользовательский шаблон", padding=5)
        self.template_frame.grid(row=6, column=0, columnspan=2, sticky='ew', pady=10)
        self.template_frame.grid_remove()

        ttk.Label(self.template_frame,
                 text="Используйте: {last} {first} {middle} {fi} {mi} {f} {m} {l}").pack(anchor='w')

        self.template_var = tk.StringVar()
        ttk.Entry(self.template_frame, textvariable=self.template_var, width=40).pack(fill='x', pady=5)

        ttk.Label(self.template_frame,
                 text="Пример: {last} {fi}.{mi}. = Иванов И.И.").pack(anchor='w')

        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(btn_frame, text="Применить",
                  command=self.apply_format).pack(side='left', padx=(0, 10))
        ttk.Button(btn_frame, text="Сбросить",
                  command=self.reset_format).pack(side='left')

        self.delimiter_var.trace('w', self.on_setting_changed)
        self.and_word_var.trace('w', self.on_setting_changed)
        self.et_al_var.trace('w', self.on_setting_changed)
        self.initials_dot_var.trace('w', self.on_setting_changed)
        self.initials_space_var.trace('w', self.on_setting_changed)
        self.template_var.trace('w', self.on_template_changed)

    def setup_preview(self, parent):
        ttk.Label(parent, text="Один автор:").pack(anchor='w', pady=(0, 5))

        self.single_preview_frame = ttk.Frame(parent, relief='sunken', borderwidth=1)
        self.single_preview_frame.pack(fill='x', pady=(0, 10))

        self.single_preview_label = ttk.Label(self.single_preview_frame,
                                             font=('Courier', 10), padding=5)
        self.single_preview_label.pack()

        ttk.Label(parent, text="Несколько авторов:").pack(anchor='w', pady=(0, 5))

        self.multi_preview_frame = ttk.Frame(parent, relief='sunken', borderwidth=1)
        self.multi_preview_frame.pack(fill='both', expand=True)

        self.multi_preview_label = ttk.Label(self.multi_preview_frame,
                                            font=('Courier', 10), padding=5,
                                            wraplength=300)
        self.multi_preview_label.pack()

    def setup_order_editor(self, parent):
        available_frame = ttk.LabelFrame(parent, text="Доступные части", padding=5)
        available_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        ttk.Label(available_frame, text="Дважды щелкните для добавления:").pack(anchor='w', pady=(0, 5))

        self.available_listbox = tk.Listbox(available_frame, height=8, selectmode='single')
        self.available_listbox.pack(fill='both', expand=True)
        self.available_listbox.bind('<Double-Button-1>', self.on_double_click_available)

        parts = self.author_formatter.get_available_parts()
        for part in parts:
            self.available_listbox.insert('end', f"{part['name']} ({part['example']})")

        order_frame = ttk.LabelFrame(parent, text="Текущий порядок", padding=5)
        order_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))

        control_frame = ttk.Frame(order_frame)
        control_frame.pack(fill='x', pady=(0, 5))

        ttk.Button(control_frame, text="↑", width=3,
                  command=self.move_part_up).pack(side='left', padx=2)
        ttk.Button(control_frame, text="↓", width=3,
                  command=self.move_part_down).pack(side='left', padx=2)
        ttk.Button(control_frame, text="Удалить",
                  command=self.remove_part).pack(side='left', padx=2)

        self.order_listbox = tk.Listbox(order_frame, height=8, selectmode='single')
        self.order_listbox.pack(fill='both', expand=True)
        self.order_listbox.bind('<Double-Button-1>', self.on_double_click_order)

        self.update_order_listbox()

    def on_format_changed(self, event=None):
        display_value = self.format_var.get()
        if display_value in self.format_display_to_value:
            format_type = self.format_display_to_value[display_value]

            if format_type == AuthorFormat.CUSTOM:
                self.template_frame.grid()
            else:
                self.template_frame.grid_remove()

                self.current_config = AuthorFormatConfig.get_preset(format_type)
                self.author_formatter = AuthorFormatter(self.current_config)

                self.delimiter_var.set(self.current_config.delimiter)
                self.and_word_var.set(self.current_config.and_word)
                self.et_al_var.set(self.current_config.et_al_limit)
                self.include_et_al_var.set(self.current_config.include_et_al)
                self.initials_dot_var.set(self.current_config.initials_dot)
                self.initials_space_var.set(self.current_config.initials_space)

                self.update_order_listbox()

            self.update_preview()

    def on_setting_changed(self, *args):
        self.update_config_from_ui()
        self.update_preview()

    def on_template_changed(self, *args):
        if self.current_config.format_type == AuthorFormat.CUSTOM:
            self.current_config.template = self.template_var.get()
            self.update_preview()

    def on_double_click_available(self, event):
        selection = self.available_listbox.curselection()
        if selection:
            index = selection[0]
            parts = self.author_formatter.get_available_parts()
            if index < len(parts):
                part_id = parts[index]["id"]
                if part_id not in self.current_config.parts_order:
                    self.current_config.parts_order.append(part_id)
                    self.update_order_listbox()
                    self.update_preview()

    def on_double_click_order(self, event):
        self.remove_part()

    def move_part_up(self):
        selection = self.order_listbox.curselection()
        if selection:
            index = selection[0]
            if index > 0:
                parts = self.current_config.parts_order
                parts[index], parts[index-1] = parts[index-1], parts[index]
                self.update_order_listbox()
                self.order_listbox.selection_set(index-1)
                self.update_preview()

    def move_part_down(self):
        selection = self.order_listbox.curselection()
        if selection:
            index = selection[0]
            parts = self.current_config.parts_order
            if index < len(parts) - 1:
                parts[index], parts[index+1] = parts[index+1], parts[index]
                self.update_order_listbox()
                self.order_listbox.selection_set(index+1)
                self.update_preview()

    def remove_part(self):
        selection = self.order_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.current_config.parts_order):
                self.current_config.parts_order.pop(index)
                self.update_order_listbox()
                self.update_preview()

    def update_order_listbox(self):
        self.order_listbox.delete(0, tk.END)

        parts_info = {p["id"]: p for p in self.author_formatter.get_available_parts()}

        for part_id in self.current_config.parts_order:
            if part_id in parts_info:
                part = parts_info[part_id]
                self.order_listbox.insert('end', f"{part['name']} ({part['example']})")
            else:
                self.order_listbox.insert('end', part_id)

    def update_config_from_ui(self):
        display_value = self.format_var.get()
        if display_value in self.format_display_to_value:
            self.current_config.format_type = self.format_display_to_value[display_value]
        self.current_config.delimiter = self.delimiter_var.get()
        self.current_config.and_word = self.and_word_var.get()
        self.current_config.et_al_limit = self.et_al_var.get()
        self.current_config.include_et_al = self.include_et_al_var.get()
        self.current_config.initials_dot = self.initials_dot_var.get()
        self.current_config.initials_space = self.initials_space_var.get()
        self.current_config.template = self.template_var.get()

        self.author_formatter = AuthorFormatter(self.current_config)

    def update_preview(self):
        try:
            self.update_config_from_ui()

            if self.test_authors:
                author_preview = self.author_formatter.format_author(self.test_authors[0])
                self.single_preview_label.config(text=author_preview)

            authors_preview = self.author_formatter.format_authors(self.test_authors)
            self.multi_preview_label.config(text=authors_preview)

        except Exception as e:
            self.single_preview_label.config(text=f"Ошибка: {e}")
            self.multi_preview_label.config(text=f"Ошибка: {e}")

    def apply_format(self):
        if self.manager.current_style:
            self.update_config_from_ui()
            self.manager.current_style.set_author_format(self.current_config)

            if self.config_callback:
                self.config_callback()

            messagebox.showinfo("Успех", "Формат авторов применен к текущему стилю")
        else:
            messagebox.showwarning("Предупреждение", "Сначала создайте стиль")

    def reset_format(self):
        self.current_config = AuthorFormatConfig.get_preset(AuthorFormat.LAST_FIRST_INITIALS)
        self.author_formatter = AuthorFormatter(self.current_config)

        self.format_var.set(self.format_value_to_display[self.current_config.format_type])
        self.delimiter_var.set(self.current_config.delimiter)
        self.and_word_var.set(self.current_config.and_word)
        self.et_al_var.set(self.current_config.et_al_limit)
        self.include_et_al_var.set(self.current_config.include_et_al)
        self.initials_dot_var.set(self.current_config.initials_dot)
        self.initials_space_var.set(self.current_config.initials_space)
        self.template_var.set(self.current_config.template)

        self.update_order_listbox()
        self.update_preview()

        messagebox.showinfo("Сброс", "Формат сброшен к значениям по умолчанию")

class TkinterGUI:
    def __init__(self, manager):
        self.manager = manager
        self.root = tk.Tk()
        self.root.title("Форматирование библиографии")
        self.root.geometry("1200x800")

        self.style = ttk.Style()
        self.style.theme_use('clam')

        try:
            self.root.iconbitmap('app_icon.ico')
        except:
            pass

        self.setup_ui()

    def setup_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)

        self.setup_load_tab(notebook)
        self.setup_manual_tab(notebook)
        self.setup_style_tab(notebook)
        self.setup_author_tab(notebook)
        self.setup_view_tab(notebook)

        self.setup_control_buttons()

    def setup_load_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Загрузка из DOCX")

        title_label = ttk.Label(frame, text="Загрузка библиографии из DOCX файла",
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Выбрать файл",
                  command=self.load_docx, width=20).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Очистить список",
                  command=self.clear_items, width=20).pack(side='left', padx=5)

        self.load_status = ttk.Label(frame, text="Файл не выбран", font=('Arial', 10))
        self.load_status.pack(pady=5)

        preview_frame = ttk.LabelFrame(frame, text="Предпросмотр загруженных записей", padding=10)
        preview_frame.pack(fill='both', expand=True, padx=10, pady=10)

        text_frame = ttk.Frame(preview_frame)
        text_frame.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')

        self.preview_text = tk.Text(text_frame, height=15, width=80, yscrollcommand=scrollbar.set)
        self.preview_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.preview_text.yview)

        self.load_info = ttk.Label(frame, text="")
        self.load_info.pack(pady=5)

    def setup_manual_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Ручной ввод")

        type_frame = ttk.Frame(frame)
        type_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(type_frame, text="Тип ресурса:", font=('Arial', 10)).pack(side='left', padx=5)

        self.resource_type_var = tk.StringVar(value="Статья")
        type_combo = ttk.Combobox(type_frame, textvariable=self.resource_type_var,
                                 values=["Статья", "Книга", "Конференция", "Электронный ресурс"], width=20)
        type_combo.pack(side='left', padx=5)
        type_combo.bind('<<ComboboxSelected>>', self.update_input_fields)

        input_frame = ttk.LabelFrame(frame, text="Данные записи", padding=10)
        input_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        self.input_fields_frame = ttk.Frame(input_frame)
        self.input_fields_frame.pack(fill='both', expand=True)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="➕ Добавить запись",
                  command=self.add_manual_item_gui, width=20).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🧹 Очистить поля",
                  command=self.clear_input_fields, width=20).pack(side='left', padx=5)

        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self.update_input_fields()

    def setup_style_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Настройка стиля")

        main_frame = ttk.Frame(frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        left_frame = ttk.LabelFrame(main_frame, text="Доступные поля", padding=10)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        ttk.Label(left_frame, text="Выберите поля для форматирования:").pack(anchor='w', pady=(0, 5))

        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')

        self.available_fields_listbox = tk.Listbox(list_frame, selectmode='multiple',
                                                  yscrollcommand=scrollbar.set, height=12)
        self.available_fields_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.available_fields_listbox.yview)

        for field in self.manager.available_fields:
            self.available_fields_listbox.insert(tk.END, field)

        center_frame = ttk.Frame(main_frame)
        center_frame.pack(side='left', fill='y', padx=5)

        ttk.Button(center_frame, text="Добавить →",
                  command=self.add_field_to_order, width=15).pack(pady=5)
        ttk.Button(center_frame, text="← Удалить",
                  command=self.remove_field_from_order, width=15).pack(pady=5)
        ttk.Button(center_frame, text="↑ Вверх",
                  command=self.move_field_up, width=15).pack(pady=5)
        ttk.Button(center_frame, text="↓ Вниз",
                  command=self.move_field_down, width=15).pack(pady=5)
        ttk.Button(center_frame, text="Настройка поля",
                  command=self.open_field_settings, width=15).pack(pady=5)
        ttk.Button(center_frame, text="Очистить",
                  command=self.clear_field_order, width=15).pack(pady=20)

        right_frame = ttk.LabelFrame(main_frame, text="Порядок полей", padding=10)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))

        ttk.Label(right_frame, text="Текущий порядок форматирования:").pack(anchor='w', pady=(0, 5))

        order_list_frame = ttk.Frame(right_frame)
        order_list_frame.pack(fill='both', expand=True)

        order_scrollbar = ttk.Scrollbar(order_list_frame)
        order_scrollbar.pack(side='right', fill='y')

        self.field_order_listbox = tk.Listbox(order_list_frame, selectmode='multiple',
                                             yscrollcommand=order_scrollbar.set, height=12)
        self.field_order_listbox.pack(side='left', fill='both', expand=True)
        order_scrollbar.config(command=self.field_order_listbox.yview)

        required_frame = ttk.LabelFrame(right_frame, text="Обязательные поля", padding=10)
        required_frame.pack(fill='x', pady=(10, 0))

        required_list_frame = ttk.Frame(required_frame)
        required_list_frame.pack(fill='x')

        required_scrollbar = ttk.Scrollbar(required_list_frame, orient='horizontal')
        required_scrollbar.pack(side='bottom', fill='x')

        self.required_fields_listbox = tk.Listbox(required_list_frame,
                                                 selectmode='multiple',
                                                 xscrollcommand=required_scrollbar.set,
                                                 height=3)
        self.required_fields_listbox.pack(fill='x')
        required_scrollbar.config(command=self.required_fields_listbox.xview)

        required_btn_frame = ttk.Frame(required_frame)
        required_btn_frame.pack(fill='x', pady=(5, 0))

        ttk.Button(required_btn_frame, text="Добавить выбранное",
                  command=self.add_to_required, width=15).pack(side='left', padx=2)
        ttk.Button(required_btn_frame, text="Удалить выбранное",
                  command=self.remove_from_required, width=15).pack(side='left', padx=2)

        preview_frame = ttk.LabelFrame(frame, text="Предпросмотр стиля", padding=10)
        preview_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        self.preview_text = tk.Text(preview_frame, height=5, width=80, wrap='word')
        self.preview_text.pack(fill='both', expand=True)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Сохранить стиль",
                  command=self.save_style, width=20).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Загрузить стиль",
                  command=self.load_style, width=20).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Экспорт стиля",
                  command=self.export_style, width=20).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Обновить предпросмотр",
                  command=self.update_preview, width=20).pack(side='left', padx=5)

    def open_field_settings(self):
        selection = self.field_order_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите поле для настройки")
            return

        index = selection[0]
        field_name = self.field_order_listbox.get(index)

        if not self.manager.current_style:
            self.manager.current_style = CitationStyle("Пользовательский")

        dialog = FieldSettingsDialog(self.root, field_name, self.manager.current_style)
        self.root.wait_window(dialog.dialog)

        self.update_preview()

    def add_to_required(self):
        selection = self.field_order_listbox.curselection()
        for index in selection:
            field = self.field_order_listbox.get(index)
            if field not in self.required_fields_listbox.get(0, tk.END):
                self.required_fields_listbox.insert(tk.END, field)

    def remove_from_required(self):
        selection = self.required_fields_listbox.curselection()
        for index in reversed(selection):
            self.required_fields_listbox.delete(index)

    def update_preview(self):
        if not self.manager.current_style or not self.manager.items:
            return

        preview_item = self.manager.items[0]
        formatted = self.manager.current_style.format_item(preview_item)

        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, formatted)

    def setup_author_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Формат авторов")

        self.author_tab = AuthorTab(frame, self.manager, self.on_author_config_changed)
        self.author_tab.pack(fill='both', expand=True)

    def setup_view_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Просмотр и экспорт")

        toolbar = ttk.Frame(frame)
        toolbar.pack(fill='x', padx=10, pady=10)

        ttk.Button(toolbar, text="Обновить",
                  command=self.update_items_view).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Проверить",
                  command=self.validate_items_gui).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Экспорт DOCX",
                  command=self.export_to_docx).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Копировать",
                  command=self.copy_to_clipboard).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Удалить выбранное",
                  command=self.delete_selected_item).pack(side='left', padx=2)

        self.view_status = ttk.Label(toolbar, text="")
        self.view_status.pack(side='right', padx=10)

        list_frame = ttk.LabelFrame(frame, text="Записи библиографии", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        text_frame = ttk.Frame(list_frame)
        text_frame.pack(fill='both', expand=True)

        y_scrollbar = ttk.Scrollbar(text_frame)
        y_scrollbar.pack(side='right', fill='y')

        x_scrollbar = ttk.Scrollbar(text_frame, orient='horizontal')
        x_scrollbar.pack(side='bottom', fill='x')

        self.items_text = tk.Text(text_frame,
                                 height=20,
                                 width=80,
                                 wrap='none',
                                 yscrollcommand=y_scrollbar.set,
                                 xscrollcommand=x_scrollbar.set)
        self.items_text.pack(side='left', fill='both', expand=True)

        y_scrollbar.config(command=self.items_text.yview)
        x_scrollbar.config(command=self.items_text.xview)

        fixed_font = tkfont.Font(family="Courier", size=10)
        self.items_text.configure(font=fixed_font)

    def setup_control_buttons(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(frame, text="О программе",
                  command=self.show_about).pack(side='left', padx=5)

        ttk.Button(frame, text="Выход",
                  command=self.root.quit).pack(side='right', padx=5)

    def on_author_config_changed(self):
        if hasattr(self, 'items_text'):
            self.update_items_view()

    def load_docx(self):
        filepath = filedialog.askopenfilename(
            title="Выберите DOCX файл",
            filetypes=[("DOCX files", "*.docx"), ("Все файлы", "*.*")]
        )

        if filepath:
            try:
                items = self.manager.parse_docx(filepath)
                for item in items:
                    self.manager.add_item(item)

                filename = Path(filepath).name
                self.load_status.config(text=f"Загружено из: {filename}")
                self.load_info.config(text=f"Загружено {len(items)} записей")

                self.preview_text.delete(1.0, tk.END)
                for i, item in enumerate(items[:10], 1):
                    self.preview_text.insert(tk.END, f"{i}. {item}\n")

                if len(items) > 10:
                    self.preview_text.insert(tk.END, f"... и еще {len(items) - 10} записей\n")

                self.update_items_view()

                messagebox.showinfo("Успех", f"Загружено {len(items)} записей из {filename}")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{str(e)}")

    def clear_items(self):
        if not self.manager.items:
            messagebox.showinfo("Информация", "Нет записей для очистки")
            return

        if messagebox.askyesno("Подтверждение",
                              f"Удалить все {len(self.manager.items)} записей?"):
            self.manager.items.clear()
            self.preview_text.delete(1.0, tk.END)
            self.load_status.config(text="Файл не выбран")
            self.load_info.config(text="Записи очищены")
            self.update_items_view()
            messagebox.showinfo("Успех", "Все записи удалены")

    def update_input_fields(self, event=None):
        for widget in self.input_fields_frame.winfo_children():
            widget.destroy()

        rt_value = self.resource_type_var.get()

        row = 0

        ttk.Label(self.input_fields_frame, text="Авторы (через точку с запятой или запятую):").grid(
            row=row, column=0, sticky='w', padx=5, pady=2)
        self.authors_entry = ttk.Entry(self.input_fields_frame, width=50)
        self.authors_entry.grid(row=row, column=1, padx=5, pady=2)
        ttk.Label(self.input_fields_frame, text="Пример: Abdelfattah, M.S.; Bitar, A.; Betz, V.").grid(
            row=row, column=2, sticky='w', padx=5, pady=2)
        row += 1

        ttk.Label(self.input_fields_frame, text="Название:").grid(
            row=row, column=0, sticky='w', padx=5, pady=2)
        self.title_entry = ttk.Entry(self.input_fields_frame, width=50)
        self.title_entry.grid(row=row, column=1, padx=5, pady=2)
        row += 1

        ttk.Label(self.input_fields_frame, text="Год:").grid(
            row=row, column=0, sticky='w', padx=5, pady=2)
        self.year_entry = ttk.Entry(self.input_fields_frame, width=50)
        self.year_entry.grid(row=row, column=1, padx=5, pady=2)
        row += 1

        if rt_value == "Статья":
            ttk.Label(self.input_fields_frame, text="Журнал:").grid(
                row=row, column=0, sticky='w', padx=5, pady=2)
            self.journal_entry = ttk.Entry(self.input_fields_frame, width=50)
            self.journal_entry.grid(row=row, column=1, padx=5, pady=2)
            row += 1

            ttk.Label(self.input_fields_frame, text="Том:").grid(
                row=row, column=0, sticky='w', padx=5, pady=2)
            self.volume_entry = ttk.Entry(self.input_fields_frame, width=50)
            self.volume_entry.grid(row=row, column=1, padx=5, pady=2)
            row += 1

            ttk.Label(self.input_fields_frame, text="Номер:").grid(
                row=row, column=0, sticky='w', padx=5, pady=2)
            self.issue_entry = ttk.Entry(self.input_fields_frame, width=50)
            self.issue_entry.grid(row=row, column=1, padx=5, pady=2)
            row += 1

            ttk.Label(self.input_fields_frame, text="Страницы:").grid(
                row=row, column=0, sticky='w', padx=5, pady=2)
            self.pages_entry = ttk.Entry(self.input_fields_frame, width=50)
            self.pages_entry.grid(row=row, column=1, padx=5, pady=2)

        elif rt_value == "Книга":
            ttk.Label(self.input_fields_frame, text="Издательство:").grid(
                row=row, column=0, sticky='w', padx=5, pady=2)
            self.publisher_entry = ttk.Entry(self.input_fields_frame, width=50)
            self.publisher_entry.grid(row=row, column=1, padx=5, pady=2)
            row += 1

            ttk.Label(self.input_fields_frame, text="Издание:").grid(
                row=row, column=0, sticky='w', padx=5, pady=2)
            self.edition_entry = ttk.Entry(self.input_fields_frame, width=50)
            self.edition_entry.grid(row=row, column=1, padx=5, pady=2)
            row += 1

            ttk.Label(self.input_fields_frame, text="ISBN:").grid(
                row=row, column=0, sticky='w', padx=5, pady=2)
            self.isbn_entry = ttk.Entry(self.input_fields_frame, width=50)
            self.isbn_entry.grid(row=row, column=1, padx=5, pady=2)
            row += 1

            ttk.Label(self.input_fields_frame, text="Город:").grid(
                row=row, column=0, sticky='w', padx=5, pady=2)
            self.city_entry = ttk.Entry(self.input_fields_frame, width=50)
            self.city_entry.grid(row=row, column=1, padx=5, pady=2)

        elif rt_value == "Конференция":
            ttk.Label(self.input_fields_frame, text="Конференция:").grid(
                row=row, column=0, sticky='w', padx=5, pady=2)
            self.conference_entry = ttk.Entry(self.input_fields_frame, width=50)
            self.conference_entry.grid(row=row, column=1, padx=5, pady=2)
            row += 1

            ttk.Label(self.input_fields_frame, text="Место проведения:").grid(
                row=row, column=0, sticky='w', padx=5, pady=2)
            self.location_entry = ttk.Entry(self.input_fields_frame, width=50)
            self.location_entry.grid(row=row, column=1, padx=5, pady=2)
            row += 1

            ttk.Label(self.input_fields_frame, text="Страницы:").grid(
                row=row, column=0, sticky='w', padx=5, pady=2)
            self.pages_entry = ttk.Entry(self.input_fields_frame, width=50)
            self.pages_entry.grid(row=row, column=1, padx=5, pady=2)

        elif rt_value == "Электронный ресурс":
            ttk.Label(self.input_fields_frame, text="Веб-сайт:").grid(
                row=row, column=0, sticky='w', padx=5, pady=2)
            self.website_entry = ttk.Entry(self.input_fields_frame, width=50)
            self.website_entry.grid(row=row, column=1, padx=5, pady=2)
            row += 1

            ttk.Label(self.input_fields_frame, text="Дата обращения:").grid(
                row=row, column=0, sticky='w', padx=5, pady=2)
            self.accessed_date_entry = ttk.Entry(self.input_fields_frame, width=50)
            self.accessed_date_entry.grid(row=row, column=1, padx=5, pady=2)

        row += 1
        ttk.Label(self.input_fields_frame, text="URL (опционально):").grid(
            row=row, column=0, sticky='w', padx=5, pady=2)
        self.url_entry = ttk.Entry(self.input_fields_frame, width=50)
        self.url_entry.grid(row=row, column=1, padx=5, pady=2)
        row += 1

        ttk.Label(self.input_fields_frame, text="DOI (опционально):").grid(
            row=row, column=0, sticky='w', padx=5, pady=2)
        self.doi_entry = ttk.Entry(self.input_fields_frame, width=50)
        self.doi_entry.grid(row=row, column=1, padx=5, pady=2)

    def clear_input_fields(self):
        for widget in self.input_fields_frame.winfo_children():
            if isinstance(widget, ttk.Entry):
                widget.delete(0, tk.END)

    def add_manual_item_gui(self):
        try:
            rt_value = self.resource_type_var.get()

            if rt_value == "Статья":
                item = Article()
                if hasattr(self, 'journal_entry'):
                    item.journal = self._clean_extracted_value(self.journal_entry.get(), field_name="journal")
                if hasattr(self, 'volume_entry'):
                    item.volume = self._clean_extracted_value(self.volume_entry.get(), field_name="volume")
                if hasattr(self, 'issue_entry'):
                    item.issue = self._clean_extracted_value(self.issue_entry.get(), field_name="issue")
                if hasattr(self, 'pages_entry'):
                    item.pages = self._clean_extracted_value(self.pages_entry.get(), field_name="pages")

            elif rt_value == "Книга":
                item = Book()
                if hasattr(self, 'publisher_entry'):
                    item.publisher = self._clean_extracted_value(self.publisher_entry.get(), field_name="publisher")
                if hasattr(self, 'edition_entry'):
                    item.edition = self._clean_extracted_value(self.edition_entry.get(), field_name="edition")
                if hasattr(self, 'isbn_entry'):
                    item.isbn = self._clean_extracted_value(self.isbn_entry.get(), field_name="isbn")
                if hasattr(self, 'city_entry'):
                    item.city = self._clean_extracted_value(self.city_entry.get(), field_name="city")

            elif rt_value == "Конференция":
                item = ConferencePaper()
                if hasattr(self, 'conference_entry'):
                    item.conference_name = self._clean_extracted_value(self.conference_entry.get(), field_name="conference_name")
                if hasattr(self, 'location_entry'):
                    item.location = self._clean_extracted_value(self.location_entry.get(), field_name="location")
                if hasattr(self, 'pages_entry'):
                    item.pages = self._clean_extracted_value(self.pages_entry.get(), field_name="pages")

            elif rt_value == "Электронный ресурс":
                item = ElectronicResource()
                if hasattr(self, 'website_entry'):
                    item.website = self._clean_extracted_value(self.website_entry.get(), field_name="website")
                if hasattr(self, 'accessed_date_entry'):
                    item.accessed_date = self._clean_extracted_value(self.accessed_date_entry.get(), field_name="accessed_date")

            else:
                return

            authors_str = self.authors_entry.get()
            if authors_str:
                authors_list = re.split(r'[;,]', authors_str)
                for author_str in authors_list:
                    if author_str.strip():
                        item.authors.append(Author.parse(author_str.strip()))

            item.title = self.title_entry.get()

            year_str = self.year_entry.get()
            if year_str and year_str.isdigit():
                item.year = int(year_str)

            if hasattr(self, 'url_entry'):
                item.url = self._clean_extracted_value(self.url_entry.get(), field_name="url")
            if hasattr(self, 'doi_entry'):
                item.doi = self._clean_extracted_value(self.doi_entry.get(), field_name="doi")

            if not item.authors and rt_value not in ["Электронный ресурс", "Другое"]:
                messagebox.showwarning("Предупреждение", "Укажите хотя бы одного автора")
                return

            if not item.title:
                messagebox.showwarning("Предупреждение", "Укажите название")
                return

            self.manager.add_item(item)

            self.clear_input_fields()

            self.update_items_view()

            messagebox.showinfo("Успех", "Запись успешно добавлена")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить запись:\n{str(e)}")

    def _clean_extracted_value(self, value, field_name=""):
        return self.manager._clean_extracted_value(value, field_name)

    def add_field_to_order(self):
        selection = self.available_fields_listbox.curselection()
        for index in selection:
            field = self.available_fields_listbox.get(index)
            if field not in self.field_order_listbox.get(0, tk.END):
                self.field_order_listbox.insert(tk.END, field)

    def remove_field_from_order(self):
        selection = self.field_order_listbox.curselection()
        for index in reversed(selection):
            self.field_order_listbox.delete(index)

    def move_field_up(self):
        selection = self.field_order_listbox.curselection()
        if selection:
            index = selection[0]
            if index > 0:
                field = self.field_order_listbox.get(index)
                self.field_order_listbox.delete(index)
                self.field_order_listbox.insert(index - 1, field)
                self.field_order_listbox.selection_set(index - 1)

    def move_field_down(self):
        selection = self.field_order_listbox.curselection()
        if selection:
            index = selection[0]
            if index < self.field_order_listbox.size() - 1:
                field = self.field_order_listbox.get(index)
                self.field_order_listbox.delete(index)
                self.field_order_listbox.insert(index + 1, field)
                self.field_order_listbox.selection_set(index + 1)

    def clear_field_order(self):
        if messagebox.askyesno("Подтверждение", "Очистить весь порядок полей?"):
            self.field_order_listbox.delete(0, tk.END)

    def save_style(self):
        field_order = list(self.field_order_listbox.get(0, tk.END))
        required_fields = list(self.required_fields_listbox.get(0, tk.END))

        if not field_order:
            messagebox.showwarning("Предупреждение", "Укажите порядок полей")
            return

        author_config = None
        if hasattr(self, 'author_tab'):
            author_config = self.author_tab.current_config

        if not self.manager.current_style:
            style = CitationStyle("Пользовательский")
            self.manager.current_style = style

        self.manager.current_style.set_field_order(field_order)
        self.manager.current_style.set_required_fields(required_fields)

        if author_config:
            self.manager.current_style.set_author_format(author_config)

        self.update_preview()

        if messagebox.askyesno("Сохранение", "Сохранить стиль в файл?"):
            self.export_style()
        else:
            messagebox.showinfo("Успех", f"Стиль '{self.manager.current_style.name}' сохранен")

    def load_style(self):
        filepath = filedialog.askopenfilename(
            title="Выберите файл стиля",
            filetypes=[("JSON files", "*.json"), ("Все файлы", "*.*")]
        )

        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    style_data = json.load(f)

                style = CitationStyle.from_dict(style_data)
                self.manager.current_style = style

                self.field_order_listbox.delete(0, tk.END)
                for field in style.field_order:
                    self.field_order_listbox.insert(tk.END, field)

                self.required_fields_listbox.delete(0, tk.END)
                for field in style.required_fields:
                    self.required_fields_listbox.insert(tk.END, field)

                if hasattr(self, 'author_tab'):
                    self.author_tab.current_config = style.author_format_config
                    self.author_tab.update_config_from_ui()
                    self.author_tab.update_preview()

                messagebox.showinfo("Успех", f"Стиль '{style.name}' загружен")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить стиль:\n{str(e)}")

    def export_style(self):
        if not self.manager.current_style:
            messagebox.showwarning("Предупреждение", "Сначала создайте стиль")
            return

        filepath = filedialog.asksaveasfilename(
            title="Сохранить стиль",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Все файлы", "*.*")]
        )

        if filepath:
            try:
                style_dict = self.manager.current_style.to_dict()

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(style_dict, f, ensure_ascii=False, indent=2)

                messagebox.showinfo("Успех", f"Стиль сохранен в {filepath}")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить стиль:\n{str(e)}")

    def update_items_view(self):
        self.items_text.delete(1.0, tk.END)

        if not self.manager.items:
            self.items_text.insert(tk.END, "Нет записей в библиографии")
            self.view_status.config(text="Записей: 0")
            return

        self.view_status.config(text=f"Записей: {len(self.manager.items)}")

        for i, item in enumerate(self.manager.items, 1):
            if self.manager.current_style:
                authors_formatted = item.format_authors(self.manager.current_style.author_formatter)
            else:
                authors_formatted = item.format_authors()

            self.items_text.insert(tk.END, f"{i}. {authors_formatted}\n")
            self.items_text.insert(tk.END, f"   Название: {item.title}\n")

            if item.year:
                self.items_text.insert(tk.END, f"   Год: {item.year}\n")

            if isinstance(item, Article) and item.journal:
                self.items_text.insert(tk.END, f"   Журнал: {item.journal}\n")
            elif isinstance(item, Book) and item.publisher:
                self.items_text.insert(tk.END, f"   Издательство: {item.publisher}\n")
            elif isinstance(item, ConferencePaper) and item.conference_name:
                self.items_text.insert(tk.END, f"   Конференция: {item.conference_name}\n")
            elif isinstance(item, ElectronicResource) and item.website:
                self.items_text.insert(tk.END, f"   Веб-сайт: {item.website}\n")

            if self.manager.current_style:
                formatted = self.manager.current_style.format_item(item)
                self.items_text.insert(tk.END, f"   Формат: {formatted}\n")

            self.items_text.insert(tk.END, "-" * 80 + "\n\n")

        self.items_text.see(1.0)

    def validate_items_gui(self):
        if not self.manager.current_style:
            messagebox.showwarning("Предупреждение", "Сначала настройте стиль")
            return

        results = self.manager.validate_all_items()

        valid_count = sum(1 for _, is_valid, _ in results if is_valid)
        total_count = len(results)

        dialog = tk.Toplevel(self.root)
        dialog.title("Результаты проверки")
        dialog.geometry("600x400")

        ttk.Label(dialog, text=f"Проверено {total_count} записей",
                 font=('Arial', 12, 'bold')).pack(pady=10)

        if valid_count == total_count:
            color = "green"
            status_text = "✓ Все записи корректны"
        else:
            color = "orange"
            status_text = f"⚠ {valid_count} из {total_count} записей корректны"

        ttk.Label(dialog, text=status_text, foreground=color,
                 font=('Arial', 11, 'bold')).pack(pady=5)

        if valid_count < total_count:
            frame = ttk.LabelFrame(dialog, text="Проблемные записи", padding=10)
            frame.pack(fill='both', expand=True, padx=10, pady=10)

            text_frame = ttk.Frame(frame)
            text_frame.pack(fill='both', expand=True)

            scrollbar = ttk.Scrollbar(text_frame)
            scrollbar.pack(side='right', fill='y')

            text_widget = tk.Text(text_frame, height=15, width=70,
                                 yscrollcommand=scrollbar.set)
            text_widget.pack(side='left', fill='both', expand=True)
            scrollbar.config(command=text_widget.yview)

            for i, (item, is_valid, missing) in enumerate(results, 1):
                if not is_valid:
                    text_widget.insert(tk.END, f"{i}. {item.title[:50]}...\n")
                    text_widget.insert(tk.END, f"   Авторы: {item.format_authors()}\n")
                    text_widget.insert(tk.END, f"   Отсутствуют: {', '.join(missing)}\n")
                    text_widget.insert(tk.END, "-" * 50 + "\n")

        ttk.Button(dialog, text="Закрыть", command=dialog.destroy).pack(pady=10)

    def export_to_docx(self):
        if not self.manager.items:
            messagebox.showwarning("Предупреждение", "Нет записей для экспорта")
            return

        if not self.manager.current_style:
            messagebox.showwarning("Предупреждение", "Сначала настройте стиль")
            return

        filepath = filedialog.asksaveasfilename(
            title="Сохранить как DOCX",
            defaultextension=".docx",
            filetypes=[("DOCX files", "*.docx"), ("Все файлы", "*.*")]
        )

        if filepath:
            try:
                highlight = messagebox.askyesno("Подсветка",
                                               "Подсвечивать отсутствующие поля в документе?")

                self.manager.save_to_docx(filepath, highlight)

                messagebox.showinfo("Успех", f"Документ сохранен в:\n{filepath}")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить документ:\n{str(e)}")

    def copy_to_clipboard(self):
        if not self.manager.items:
            messagebox.showwarning("Предупреждение", "Нет записей для копирования")
            return

        if not self.manager.current_style:
            messagebox.showwarning("Предупреждение", "Сначала настройте стиль")
            return

        try:
            formatted_items = self.manager.format_all_items()
            text_to_copy = "\n".join([f"{i+1}. {item}" for i, item in enumerate(formatted_items)])

            self.root.clipboard_clear()
            self.root.clipboard_append(text_to_copy)

            messagebox.showinfo("Успех", "Текст скопирован в буфер обмена")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скопировать текст:\n{str(e)}")

    def delete_selected_item(self):
        if not self.manager.items:
            messagebox.showwarning("Предупреждение", "Нет записей для удаления")
            return

        try:
            selection = self.items_text.get("sel.first", "sel.last")
            if selection:
                lines = selection.split('\n')
                for line in lines:
                    if line.strip() and line.strip()[0].isdigit():
                        match = re.match(r'(\d+)\.', line.strip())
                        if match:
                            index = int(match.group(1)) - 1
                            if 0 <= index < len(self.manager.items):
                                item = self.manager.items[index]
                                if messagebox.askyesno("Подтверждение",
                                                      f"Удалить запись:\n{item.title[:50]}...?"):
                                    self.manager.items.pop(index)
                                    self.update_items_view()
                                    messagebox.showinfo("Успех", "Запись удалена")
                                    return

        except tk.TclError:
            pass

        messagebox.showwarning("Предупреждение", "Выделите запись для удаления")

    def show_about(self):
        about_text = """
        Программа форматирования библиографии

        Функции:
        • Загрузка библиографии из DOCX файлов
        • Ручной ввод записей с разбивкой на части
        • Настройка пользовательского стиля форматирования
        • Тонкая настройка формата авторов (порядок ФИО)
        • Проверка наличия обязательных полей
        • Экспорт в DOCX с подсветкой отсутствующих полей
        • Поддержка разных типов ресурсов
        """

        dialog = tk.Toplevel(self.root)
        dialog.title("О программе")
        dialog.geometry("500x400")

        text_widget = tk.Text(dialog, wrap='word', height=20, width=60)
        text_widget.pack(padx=10, pady=10, fill='both', expand=True)
        text_widget.insert(1.0, about_text)
        text_widget.config(state='disabled')

        ttk.Button(dialog, text="Закрыть", command=dialog.destroy).pack(pady=10)

    def run(self):
        self.root.mainloop()