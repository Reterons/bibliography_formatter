from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any
from author import Author
from author_formatter import AuthorFormatter

class ResourceType(Enum):
    ARTICLE = "Статья"
    BOOK = "Книга"
    CONFERENCE = "Конференция"
    THESIS = "Диссертация"
    REPORT = "Отчет"
    ELECTRONIC = "Электронный ресурс"
    OTHER = "Другое"

class BibliographicItem:
    def __init__(self, resource_type=ResourceType.ARTICLE,
                 authors=None,
                 title="", year=0, publisher="",
                 url="", doi="", accessed_date=""):
        self.resource_type = resource_type
        self.authors = authors if authors is not None else []
        self.title = title
        self.year = year
        self.publisher = publisher
        self.url = url
        self.doi = doi
        self.accessed_date = accessed_date

    def get_all_fields(self):
        return {
            'resource_type': self.resource_type.value,
            'authors': [f"{a.last_name} {a.first_name} {a.middle_name}".strip() for a in self.authors],
            'authors_str': self.format_authors(),
            'title': self.title,
            'year': self.year,
            'publisher': self.publisher,
            'url': self.url,
            'doi': self.doi,
            'accessed_date': self.accessed_date
        }

    def format_authors(self, author_formatter=None):
        if not self.authors:
            return ""

        if author_formatter:
            return author_formatter.format_authors(self.authors)

        if len(self.authors) == 1:
            author = self.authors[0]
            return author.format(author_formatter)

        formatted = []
        for author in self.authors:
            formatted.append(author.format(author_formatter))

        if len(formatted) == 2:
            return f"{formatted[0]} и {formatted[1]}"
        elif len(formatted) == 3:
            return f"{formatted[0]}, {formatted[1]} и {formatted[2]}"
        else:
            return f"{formatted[0]} и др."

    def get_missing_fields(self, required_fields):
        missing = []
        fields = self.get_all_fields()

        for field_name in required_fields:
            value = fields.get(field_name)
            if not value or (isinstance(value, list) and not value) or (isinstance(value, int) and value == 0):
                missing.append(field_name)

        return missing

    def __str__(self):
        return f"{self.format_authors()}. {self.title}. {self.year}."

class Article(BibliographicItem):
    def __init__(self, authors=None, title="", year=0,
                 publisher="", url="", doi="", accessed_date="",
                 journal="", volume="", issue="", pages=""):
        super().__init__(ResourceType.ARTICLE, authors, title, year, publisher, url, doi, accessed_date)
        self.journal = journal
        self.volume = volume
        self.issue = issue
        self.pages = pages

    def get_all_fields(self):
        fields = super().get_all_fields()
        fields.update({
            'journal': self.journal,
            'volume': self.volume,
            'issue': self.issue,
            'pages': self.pages
        })
        return fields

class Book(BibliographicItem):
    def __init__(self, authors=None, title="", year=0,
                 publisher="", url="", doi="", accessed_date="",
                 edition="", isbn="", city=""):
        super().__init__(ResourceType.BOOK, authors, title, year, publisher, url, doi, accessed_date)
        self.edition = edition
        self.isbn = isbn
        self.city = city

    def get_all_fields(self):
        fields = super().get_all_fields()
        fields.update({
            'edition': self.edition,
            'isbn': self.isbn,
            'city': self.city
        })
        return fields

class ConferencePaper(BibliographicItem):
    def __init__(self, authors=None, title="", year=0,
                 publisher="", url="", doi="", accessed_date="",
                 conference_name="", location="", pages=""):
        super().__init__(ResourceType.CONFERENCE, authors, title, year, publisher, url, doi, accessed_date)
        self.conference_name = conference_name
        self.location = location
        self.pages = pages

    def get_all_fields(self):
        fields = super().get_all_fields()
        fields.update({
            'conference_name': self.conference_name,
            'location': self.location,
            'pages': self.pages
        })
        return fields

class ElectronicResource(BibliographicItem):
    def __init__(self, authors=None, title="", year=0,
                 publisher="", url="", doi="", accessed_date="",
                 website=""):
        super().__init__(ResourceType.ELECTRONIC, authors, title, year, publisher, url, doi, accessed_date)
        self.website = website

    def get_all_fields(self):
        fields = super().get_all_fields()
        fields.update({
            'website': self.website
        })
        return fields