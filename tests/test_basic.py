import sys
import os
import pytest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Тест импортов основных модулей"""
    try:
        from author import Author, AuthorFormat, AuthorFormatConfig
        from bibliography import BibliographicItem, Article, Book, ConferencePaper
        from author_formatter import AuthorFormatter
        from citation_style import CitationStyle
        from bibliography_manager import BibliographyManager
        from gui import TkinterGUI
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

def test_author_creation():
    """Тест создания автора"""
    from author import Author
    
    author = Author("Иванов", "Иван", "Иванович")
    assert author.last_name == "Иванов"
    assert author.first_name == "Иван"
    assert author.middle_name == "Иванович"

def test_author_parse():
    """Тест парсинга строки с автором"""
    from author import Author
    
    author = Author.parse("Иванов, И.И.")
    assert author.last_name == "Иванов"
    assert author.first_name == "И"
    assert author.middle_name == "И"
    
    author = Author.parse("I.I. Ivanov")
    assert author.last_name == "Ivanov"
    assert author.first_name == "I"
    assert author.middle_name == "I"

def test_bibliographic_item():
    """Тест создания библиографической записи"""
    from bibliography import BibliographicItem
    from author import Author
    
    author = Author("Иванов", "И", "И")
    item = BibliographicItem(
        authors=[author],
        title="Название книги",
        year=2023
    )
    
    assert item.title == "Название книги"
    assert item.year == 2023
    assert len(item.authors) == 1

def test_citation_style():
    """Тест стиля цитирования"""
    from citation_style import CitationStyle
    from bibliography import BibliographicItem
    from author import Author
    
    style = CitationStyle("Test Style")
    style.set_field_order(['authors_str', 'title', 'year'])
    
    author = Author("Иванов", "И", "И")
    item = BibliographicItem(
        authors=[author],
        title="Тестовая книга",
        year=2023
    )
    
    formatted = style.format_item(item)
    assert "Иванов И.И." in formatted
    assert "Тестовая книга" in formatted
    assert "2023" in formatted

@patch('bibliography_manager.Document')
def test_bibliography_manager(mock_docx):
    """Тест менеджера библиографии"""
    from bibliography_manager import BibliographyManager
    
    manager = BibliographyManager()
    assert len(manager.items) == 0
    
    # Тест добавления элемента
    from bibliography import Article
    from author import Author
    
    author = Author("Иванов", "И", "И")
    article = Article(
        authors=[author],
        title="Тестовая статья",
        year=2023,
        journal="Тестовый журнал"
    )
    
    manager.add_item(article)
    assert len(manager.items) == 1

def test_author_formatter():
    """Тест форматирования авторов"""
    from author_formatter import AuthorFormatter
    from author import Author, AuthorFormat, AuthorFormatConfig
    
    config = AuthorFormatConfig.get_preset(AuthorFormat.LAST_FIRST_INITIALS)
    formatter = AuthorFormatter(config)
    
    author = Author("Иванов", "Иван", "Иванович")
    formatted = formatter.format_author(author)
    
    assert formatted == "Иванов И.И."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])