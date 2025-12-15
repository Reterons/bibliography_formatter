import re
from dataclasses import dataclass
from enum import Enum

class AuthorFormat(Enum):
    LAST_FIRST_INITIALS = "last_first_initials"
    FIRST_LAST_INITIALS = "first_last_initials"
    LAST_FIRST_FULL = "last_first_full"
    FIRST_LAST_FULL = "first_last_full"
    LAST_COMMA_FIRST = "last_comma_first"
    FIRST_INITIAL_LAST = "first_initial_last"
    LAST_ONLY = "last_only"
    CUSTOM = "custom"

@dataclass
class AuthorFormatConfig:
    format_type: AuthorFormat
    template: str = ""
    delimiter: str = ", "
    and_word: str = " и "
    et_al_limit: int = 3
    include_et_al: bool = True
    initials_dot: bool = True
    initials_space: bool = False
    parts_order: list = None

    def __post_init__(self):
        if self.parts_order is None:
            self.parts_order = self._get_default_order()

    def _get_default_order(self):
        if self.format_type == AuthorFormat.LAST_FIRST_INITIALS:
            return ["last_name", "first_initial", "middle_initial"]
        elif self.format_type == AuthorFormat.FIRST_LAST_INITIALS:
            return ["first_initial", "middle_initial", "last_name"]
        elif self.format_type == AuthorFormat.LAST_COMMA_FIRST:
            return ["last_name", "comma", "space", "first_initial", "middle_initial"]
        elif self.format_type == AuthorFormat.FIRST_INITIAL_LAST:
            return ["first_initial", "last_name"]
        elif self.format_type == AuthorFormat.LAST_ONLY:
            return ["last_name"]
        else:
            return ["last_name", "first_initial", "middle_initial"]

    @classmethod
    def get_preset(cls, format_type):
        return cls(format_type=format_type)

    def to_dict(self):
        return {
            "format_type": self.format_type.value,
            "template": self.template,
            "delimiter": self.delimiter,
            "and_word": self.and_word,
            "et_al_limit": self.et_al_limit,
            "include_et_al": self.include_et_al,
            "initials_dot": self.initials_dot,
            "initials_space": self.initials_space,
            "parts_order": self.parts_order
        }

    @classmethod
    def from_dict(cls, data):
        format_type = AuthorFormat(data.get("format_type", "last_first_initials"))
        config = cls(format_type=format_type)
        config.template = data.get("template", "")
        config.delimiter = data.get("delimiter", ", ")
        config.and_word = data.get("and_word", " и ")
        config.et_al_limit = data.get("et_al_limit", 3)
        config.include_et_al = data.get("include_et_al", True)
        config.initials_dot = data.get("initials_dot", True)
        config.initials_space = data.get("initials_space", False)
        config.parts_order = data.get("parts_order", config._get_default_order())
        return config

@dataclass
class Author:
    last_name: str = ""
    first_name: str = ""
    middle_name: str = ""

    def format(self, formatter=None):
        if formatter:
            return formatter.format_author(self)

        if self.first_name and self.middle_name:
            if '-' in self.first_name:
                parts = self.first_name.split('-')
                first_initials = '-'.join([f"{p[0]}." for p in parts if p])

                if '-' in self.middle_name:
                    middle_parts = self.middle_name.split('-')
                    middle_initials = '-'.join([f"{p[0]}." for p in middle_parts if p])
                    return f"{self.last_name} {first_initials}{middle_initials}"
                else:
                    return f"{self.last_name} {first_initials}{self.middle_name[0]}."
            else:
                return f"{self.last_name} {self.first_name[0]}.{self.middle_name[0]}."
        elif self.first_name:
            if '-' in self.first_name:
                parts = self.first_name.split('-')
                initials = '-'.join([f"{p[0]}." for p in parts if p])
                return f"{self.last_name} {initials}"
            else:
                return f"{self.last_name} {self.first_name[0]}."
        else:
            return self.last_name

    @classmethod
    def parse(cls, author_str):
        author_str = author_str.strip()
        if not author_str:
            return cls()

        hyphen_match = re.search(r'([A-Z])\.-([A-Z])\.', author_str)
        if hyphen_match:
            if ',' in author_str:
                parts = [p.strip() for p in author_str.split(',', 1)]
                if len(parts) == 2:
                    last_name = parts[0]
                    hyphen_initials = re.search(r'([A-Z])\.-([A-Z])\.', parts[1])
                    if hyphen_initials:
                        first_name = f"{hyphen_initials.group(1)}-{hyphen_initials.group(2)}"
                        return cls(last_name=last_name, first_name=first_name)

            else:
                match = re.match(r'^([A-Z])\.-([A-Z])\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$', author_str)
                if match:
                    return cls(last_name=match.group(3),
                              first_name=f"{match.group(1)}-{match.group(2)}")

        if ',' in author_str:
            parts = [p.strip() for p in author_str.split(',', 1)]
            if len(parts) == 2:
                last_name = parts[0]
                initials = parts[1].strip()
                initials_clean = re.sub(r'[.\s]', '', initials)

                if '-' in initials_clean:
                    return cls(last_name=last_name, first_name=initials_clean)
                elif len(initials_clean) >= 2:
                    return cls(last_name=last_name,
                              first_name=initials_clean[0],
                              middle_name=initials_clean[1])
                elif len(initials_clean) == 1:
                    return cls(last_name=last_name, first_name=initials_clean[0])

        match = re.match(r'^([A-Z])\.-([A-Z])\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$', author_str)
        if match:
            return cls(last_name=match.group(3),
                      first_name=f"{match.group(1)}-{match.group(2)}")

        match = re.match(r'^([A-Z])\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$', author_str)
        if match:
            return cls(last_name=match.group(2), first_name=match.group(1))

        match = re.match(r'^([A-Z])\.\s*([A-Z])\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$', author_str)
        if match:
            return cls(last_name=match.group(3),
                      first_name=match.group(1),
                      middle_name=match.group(2))

        match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+([A-Z])\.?\s*([A-Z])?\.?$', author_str)
        if match:
            last_name = match.group(1)
            first_name = match.group(2)
            middle_name = match.group(3) if match.group(3) else ""
            return cls(last_name=last_name, first_name=first_name, middle_name=middle_name)

        if re.match(r'^[A-Z][a-z]+$', author_str):
            return cls(last_name=author_str)

        match = re.match(r'^([A-Z][a-z]+)\s+([A-Z])\.-([A-Z])\.$', author_str)
        if match:
            return cls(last_name=match.group(1),
                      first_name=f"{match.group(2)}-{match.group(3)}")

        return cls(last_name=author_str)