import re
from typing import List, Dict, Tuple, Any
from author_formatter import AuthorFormatter, AuthorFormatConfig
from author import AuthorFormat

class CitationStyle:
    def __init__(self, name="Custom"):
        self.name = name
        self.field_order: List[str] = []
        self.field_formatters: Dict[str, str] = {}
        self.field_separators: Dict[str, str] = {}
        self.field_prefixes: Dict[str, bool] = {}
        self.required_fields: List[str] = []
        self.author_format_config = AuthorFormatConfig.get_preset(AuthorFormat.LAST_FIRST_INITIALS)
        self.author_formatter = AuthorFormatter(self.author_format_config)

    def set_field_order(self, fields):
        self.field_order = fields

    def set_field_separator(self, field_name, separator):
        self.field_separators[field_name] = separator

    def set_field_prefix(self, field_name, use_prefix):
        self.field_prefixes[field_name] = use_prefix

    def set_field_format(self, field_name, format_type):
        self.field_formatters[field_name] = format_type

    def set_required_fields(self, fields):
        self.required_fields = fields

    def set_author_format(self, config):
        self.author_format_config = config
        self.author_formatter = AuthorFormatter(config)

    def format_item(self, item):
        authors_formatted = item.format_authors(self.author_formatter)

        fields = item.get_all_fields()
        fields['authors_str'] = authors_formatted

        prefix_dict = {
            'volume': 'vol.',
            'issue': 'no.',
            'pages': 'pp.',
            'doi': 'doi:',
            'url': 'URL:'
        }

        formatted_parts = []

        for i, field_name in enumerate(self.field_order):
            if field_name in fields:
                value = fields[field_name]
                if value:
                    formatter = self.field_formatters.get(field_name, "")
                    separator = self.field_separators.get(field_name, ". ")

                    formatted_value = str(value)
                    if field_name in self.field_prefixes and self.field_prefixes[field_name]:
                        prefix = prefix_dict.get(field_name, '')
                        if prefix:
                            formatted_value = f"{prefix} {formatted_value}"

                    if formatter == "quotes":
                        if separator.strip() in [',', ', ']:
                            formatted_value = f'"{formatted_value}{separator.rstrip()}"'
                            if i < len(self.field_order) - 1:
                                formatted_value += " "
                        else:
                            formatted_value = f'"{formatted_value}"'
                    elif formatter == "brackets":
                        if separator.strip() in [",", ", "]:
                            formatted_value = f"[{formatted_value}{separator.rstrip()}]"
                            if i < len(self.field_order) - 1:
                                formatted_value += " "
                        else:
                            formatted_value = f"[{formatted_value}]"
                    else:
                        formatted_value = formatted_value

                    if formatter == "italic":
                        formatted_value = f"*{formatted_value}*"
                    elif formatter == "bold":
                        formatted_value = f"**{formatted_value}**"

                    if formatter == "quotes" and separator.strip() in [',', ', ']:
                        formatted_parts.append(formatted_value)
                    else:
                        formatted_parts.append(formatted_value + separator)

        result = "".join(filter(None, formatted_parts))
        result = self._clean_result(result)
        return result

    def _clean_result(self, result):
        if not result:
            return result

        result = re.sub(r'\s+([.,;:])', r'\1', result)
        result = re.sub(r'"\s{2,}', r'" ', result)
        result = re.sub(r'"\s+,', r'",', result)
        result = re.sub(r'"\s+\.', r'".', result)
        result = re.sub(r'",(\d{4})', r'", \1', result)
        result = re.sub(r'"\.(\d{4})', r'". \1', result)
        result = re.sub(r'\s+', ' ', result)

        if result.endswith(' .'):
            result = result[:-2] + '.'
        if result.endswith('..'):
            result = result[:-1]

        result = result.strip()

        if result and not result.endswith(('.', '!', '?')):
            result += '.'

        return result

    def validate_item(self, item):
        missing = item.get_missing_fields(self.required_fields)
        return len(missing) == 0, missing

    def to_dict(self):
        return {
            "name": self.name,
            "field_order": self.field_order,
            "field_formatters": self.field_formatters,
            "field_separators": self.field_separators,
            "field_prefixes": self.field_prefixes,
            "required_fields": self.required_fields,
            "author_format": self.author_format_config.to_dict()
        }

    @classmethod
    def from_dict(cls, data):
        style = cls(data.get("name", "Custom"))
        style.set_field_order(data.get("field_order", []))
        style.set_required_fields(data.get("required_fields", []))

        if "field_formatters" in data:
            for field_name, formatter in data["field_formatters"].items():
                style.set_field_format(field_name, formatter)

        if "field_separators" in data:
            for field_name, separator in data["field_separators"].items():
                style.set_field_separator(field_name, separator)

        if "field_prefixes" in data:
            for field_name, use_prefix in data["field_prefixes"].items():
                style.set_field_prefix(field_name, use_prefix)

        if "author_format" in data:
            author_config = AuthorFormatConfig.from_dict(data["author_format"])
            style.set_author_format(author_config)

        return style