def create_test_author():
    """Создает тестового автора."""
    from author import Author
    return Author("Иванов", "Иван", "Иванович")

def create_test_article():
    """Создает тестовую статью."""
    from bibliography import Article
    from author import Author
    
    author = Author("Иванов", "Иван", "Иванович")
    return Article(
        authors=[author],
        title="Тестовая статья",
        year=2023,
        journal="Тестовый журнал",
        volume="10",
        issue="2",
        pages="100-110"
    )

__all__ = ['test_basic']
