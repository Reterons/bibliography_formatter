from typing import List, Dict
from author import Author, AuthorFormat, AuthorFormatConfig

class AuthorFormatter:
    def __init__(self, config=None):
        self.config = config or AuthorFormatConfig.get_preset(AuthorFormat.LAST_FIRST_INITIALS)

    def format_author(self, author):
        if self.config.format_type == AuthorFormat.CUSTOM and self.config.template:
            return self._format_custom(author)

        if self.config.format_type == AuthorFormat.LAST_FIRST_INITIALS:
            return self._format_last_first_initials(author)
        elif self.config.format_type == AuthorFormat.FIRST_LAST_INITIALS:
            return self._format_first_last_initials(author)
        elif self.config.format_type == AuthorFormat.LAST_COMMA_FIRST:
            return self._format_last_comma_first(author)
        elif self.config.format_type == AuthorFormat.FIRST_INITIAL_LAST:
            return self._format_first_initial_last(author)
        elif self.config.format_type == AuthorFormat.LAST_ONLY:
            return self._format_last_only(author)
        else:
            return self._format_general(author)

    def _format_last_first_initials(self, author):
        initials = self._get_initials(author)
        if initials:
            return f"{author.last_name} {initials}"
        else:
            return author.last_name

    def _format_first_last_initials(self, author):
        initials = self._get_initials(author)
        if initials:
            return f"{initials} {author.last_name}"
        else:
            return author.last_name

    def _format_last_comma_first(self, author):
        initials = self._get_initials(author)
        if initials:
            return f"{author.last_name}, {initials}"
        else:
            return author.last_name

    def _format_first_initial_last(self, author):
        if author.first_name:
            return f"{self._format_initial(author.first_name[0])} {author.last_name}"
        else:
            return author.last_name

    def _format_last_only(self, author):
        return author.last_name

    def _format_general(self, author):
        parts = []
        for part_type in self.config.parts_order:
            part = self._get_author_part(author, part_type)
            if part:
                parts.append(part)

        result = ""
        for i, part in enumerate(parts):
            if part in [",", " "]:
                result += part
            else:
                if i > 0 and parts[i-1] not in [",", " "]:
                    result += " "
                result += part

        return result.strip()

    def _get_initials(self, author):
        initials = ""

        if author.first_name:
            if '-' in author.first_name:
                parts = author.first_name.split('-')
                formatted_parts = []
                for part in parts:
                    if part:
                        formatted_parts.append(self._format_initial(part[0]))
                initials += '-'.join(formatted_parts)
            else:
                initials += self._format_initial(author.first_name[0])

        if author.middle_name:
            if '-' in author.middle_name:
                parts = author.middle_name.split('-')
                formatted_parts = []
                for part in parts:
                    if part:
                        formatted_parts.append(self._format_initial(part[0]))
                initials += '-'.join(formatted_parts)
            else:
                initials += self._format_initial(author.middle_name[0])

        return initials

    def _get_author_part(self, author, part_type):
        if part_type == "last_name":
            return author.last_name
        elif part_type == "first_name":
            return author.first_name
        elif part_type == "middle_name":
            return author.middle_name
        elif part_type == "first_initial":
            if author.first_name:
                if '-' in author.first_name:
                    parts = author.first_name.split('-')
                    formatted_parts = []
                    for part in parts:
                        if part:
                            formatted_parts.append(self._format_initial(part[0]))
                    return '-'.join(formatted_parts)
                else:
                    return self._format_initial(author.first_name[0])
        elif part_type == "middle_initial":
            if author.middle_name:
                if '-' in author.middle_name:
                    parts = author.middle_name.split('-')
                    formatted_parts = []
                    for part in parts:
                        if part:
                            formatted_parts.append(self._format_initial(part[0]))
                    return '-'.join(formatted_parts)
                else:
                    return self._format_initial(author.middle_name[0])
        elif part_type == "initials":
            return self._get_initials(author)
        elif part_type == "comma":
            return ","
        elif part_type == "space":
            return " "
        return ""

    def _format_initial(self, initial):
        result = initial.upper()
        if self.config.initials_dot:
            result += "."
        if self.config.initials_space and self.config.initials_dot:
            result += " "
        return result

    def _format_custom(self, author):
        template = self.config.template

        initials = self._get_initials(author)

        if author.first_name and '-' in author.first_name:
            parts = author.first_name.split('-')
            fi_parts = [self._format_initial(p[0]) for p in parts if p]
            fi_formatted = '-'.join(fi_parts)
            f_parts = [p[0].upper() for p in parts if p]
            f_formatted = '-'.join(f_parts)
        else:
            fi_formatted = self._format_initial(author.first_name[0]) if author.first_name else ""
            f_formatted = author.first_name[0].upper() if author.first_name else ""

        if author.middle_name and '-' in author.middle_name:
            parts = author.middle_name.split('-')
            mi_parts = [self._format_initial(p[0]) for p in parts if p]
            mi_formatted = '-'.join(mi_parts)
            m_parts = [p[0].upper() for p in parts if p]
            m_formatted = '-'.join(m_parts)
        else:
            mi_formatted = self._format_initial(author.middle_name[0]) if author.middle_name else ""
            m_formatted = author.middle_name[0].upper() if author.middle_name else ""

        replacements = {
            "{last}": author.last_name,
            "{first}": author.first_name,
            "{middle}": author.middle_name,
            "{fi}": fi_formatted,
            "{mi}": mi_formatted,
            "{f}": f_formatted,
            "{m}": m_formatted,
            "{l}": author.last_name,
            "{initials}": initials
        }

        for key, value in replacements.items():
            if value:
                template = template.replace(key, value)

        return template.strip()

    def format_authors(self, authors):
        if not authors:
            return ""

        if len(authors) == 1:
            return self.format_author(authors[0])

        formatted_authors = [self.format_author(author) for author in authors]

        if self.config.include_et_al and len(formatted_authors) > self.config.et_al_limit:
            main_authors = formatted_authors[:self.config.et_al_limit]
            return self._join_authors(main_authors) + self.config.and_word + "др."

        return self._join_authors(formatted_authors)

    def _join_authors(self, authors):
        if len(authors) == 1:
            return authors[0]
        elif len(authors) == 2:
            return f"{authors[0]}{self.config.and_word}{authors[1]}"
        else:
            result = self.config.delimiter.join(authors[:-1])
            if result.endswith(','):
                result = result.rstrip(',')
            result += f"{self.config.and_word}{authors[-1]}"
            return result

    def get_available_parts(self):
        return [
            {"id": "last_name", "name": "Фамилия", "example": "Иванов"},
            {"id": "first_name", "name": "Имя", "example": "Иван"},
            {"id": "middle_name", "name": "Отчество", "example": "Иванович"},
            {"id": "first_initial", "name": "Инициал имени", "example": "И."},
            {"id": "middle_initial", "name": "Инициал отчества", "example": "И."},
            {"id": "initials", "name": "Инициалы (имя+отчество)", "example": "И.И."},
            {"id": "comma", "name": "Запятая", "example": ","},
            {"id": "space", "name": "Пробел", "example": " "}
        ]