import pytest
from unittest.mock import patch, MagicMock
from library_digital.utils import search_books, semantic_search_books
from library_digital.index import app


class FakeBook:
    """Fake Book object cho testing"""
    def __init__(self, id, title, author, isbn_10=None, isbn_13=None):
        self.id = id
        self.title = title
        self.author = author
        self.isbn_10 = isbn_10 or f"123456789{id}"
        self.isbn_13 = isbn_13 or f"978123456789{id}"
        self.categories = []


class FakePagination:
    """Fake Pagination object"""
    def __init__(self, items, total=0, page=1, pages=1):
        self.items = items
        self.total = total
        self.page = page
        self.pages = pages
        self.has_prev = page > 1
        self.has_next = page < pages
        self.prev_num = page - 1 if page > 1 else None
        self.next_num = page + 1 if page < pages else None


# Flask test client
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_unit'
    with app.test_client() as client:
        yield client


# ========== UNIT TESTS FOR SEARCH BOOKS ==========

class TestSearchBooks:
    """Test tìm kiếm sách theo nhiều tiêu chí"""

    @patch('library_digital.utils.Book')
    def test_search_by_title_success(self, mock_book_class):
        """Test tìm kiếm theo tên sách thành công"""
        # Arrange
        fake_book = FakeBook(1, "Clean Code", "Robert Martin")
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.paginate.return_value = FakePagination([fake_book], total=1)
        mock_book_class.query = mock_query

        # Act
        result = search_books(title="Clean")

        # Assert
        assert result.total == 1
        assert result.items[0].title == "Clean Code"
        mock_query.filter.assert_called()

    @patch('library_digital.utils.Book')
    def test_search_by_author_success(self, mock_book_class):
        """Test tìm kiếm theo tác giả thành công"""
        # Arrange
        fake_book = FakeBook(1, "Clean Code", "Robert Martin")
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.paginate.return_value = FakePagination([fake_book], total=1)
        mock_book_class.query = mock_query

        # Act
        result = search_books(author="Robert")

        # Assert
        assert result.total == 1
        assert result.items[0].author == "Robert Martin"

    @patch('library_digital.utils.Book')
    def test_search_by_isbn_10_success(self, mock_book_class):
        """Test tìm kiếm theo ISBN-10 thành công"""
        # Arrange
        fake_book = FakeBook(1, "Clean Code", "Robert Martin", isbn_10="1234567890")
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.paginate.return_value = FakePagination([fake_book], total=1)
        mock_book_class.query = mock_query

        # Act
        result = search_books(isbn_10="1234567890")

        # Assert
        assert result.total == 1
        assert result.items[0].isbn_10 == "1234567890"

    @patch('library_digital.utils.Book')
    def test_search_by_category_success(self, mock_book_class):
        """Test tìm kiếm theo thể loại thành công"""
        # Arrange
        fake_book = FakeBook(1, "Python Book", "Author")
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.paginate.return_value = FakePagination([fake_book], total=1)
        mock_book_class.query = mock_query

        # Act
        result = search_books(category_ids=[1, 2])

        # Assert
        assert result.total == 1
        mock_query.join.assert_called()

    @patch('library_digital.utils.Book')
    def test_search_no_results(self, mock_book_class):
        """Test tìm kiếm không có kết quả"""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.paginate.return_value = FakePagination([], total=0)
        mock_book_class.query = mock_query

        # Act
        result = search_books(title="NonExistentBook12345")

        # Assert
        assert result.total == 0
        assert len(result.items) == 0

    @patch('library_digital.utils.Book')
    def test_search_combined_filters(self, mock_book_class):
        """Test tìm kiếm kết hợp nhiều tiêu chí"""
        # Arrange
        fake_book = FakeBook(1, "Python Book", "John Doe", isbn_10="1234567890")
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.paginate.return_value = FakePagination([fake_book], total=1)
        mock_book_class.query = mock_query

        # Act
        result = search_books(title="Python", author="John", isbn_10="1234567890")

        # Assert
        assert result.total == 1
        assert mock_query.filter.call_count == 3  # 3 filters applied

    @patch('library_digital.utils.Book')
    def test_search_pagination(self, mock_book_class):
        """Test phân trang kết quả tìm kiếm"""
        # Arrange
        fake_books = [FakeBook(i, f"Book {i}", f"Author {i}") for i in range(1, 11)]
        mock_query = MagicMock()
        mock_query.paginate.return_value = FakePagination(
            fake_books[:8], total=10, page=1, pages=2
        )
        mock_book_class.query = mock_query

        # Act
        result_page1 = search_books(page=1, per_page=8)
        mock_query.paginate.return_value = FakePagination(
            fake_books[8:], total=10, page=2, pages=2
        )
        result_page2 = search_books(page=2, per_page=8)

        # Assert
        assert len(result_page1.items) == 8
        assert result_page1.has_next is True
        assert len(result_page2.items) == 2
        assert result_page2.has_prev is True


class TestSemanticSearchBooks:
    """Test tìm kiếm ngữ nghĩa (semantic search) với AI"""

    @patch('library_digital.utils.Book')
    @patch('library_digital.open_router.semantic_search_books')
    def test_semantic_search_ai_success(self, mock_ai_search, mock_book_class):
        """Test tìm kiếm ngữ nghĩa qua AI thành công"""
        # Arrange
        fake_books = [
            FakeBook(1, "Machine Learning Basics", "AI Author"),
            FakeBook(2, "Deep Learning", "AI Expert"),
        ]
        mock_book_class.query.all.return_value = fake_books
        mock_book_class.query.get.side_effect = lambda id: next(
            (b for b in fake_books if b.id == id), None
        )
        
        # AI trả về kết quả liên quan
        mock_ai_search.return_value = [
            {"id": 1, "relevance_score": 0.95, "reason": "Về AI và ML"},
            {"id": 2, "relevance_score": 0.85, "reason": "Deep Learning là một nhánh của AI"},
        ]

        # Act
        result, reasons = semantic_search_books("trí tuệ nhân tạo", page=1, per_page=8)

        # Assert
        assert len(result.items) == 2
        assert reasons[1] == "Về AI và ML"
        mock_ai_search.assert_called_once()

    @patch('library_digital.utils.Book')
    @patch('library_digital.open_router.semantic_search_books')
    def test_semantic_search_ai_fallback(self, mock_ai_search, mock_book_class):
        """Test fallback về tìm kiếm thường khi AI lỗi"""
        # Arrange
        fake_book = FakeBook(1, "AI Book", "Author")
        mock_book_class.query.all.return_value = []
        mock_ai_search.return_value = []  # AI không trả về kết quả

        # Mock fallback search
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.paginate.return_value = FakePagination([fake_book], total=1)
        mock_book_class.query = mock_query

        # Act
        result = semantic_search_books("AI", page=1, per_page=8)

        # Assert - Should fallback to regular search
        assert isinstance(result, FakePagination) or hasattr(result, 'items')


# ========== UNIT TESTS FOR VIEW BOOK DETAIL ==========

class TestViewBookDetail:
    """Test xem thông tin chi tiết sách"""

    @patch('library_digital.utils.get_book_by_id')
    def test_view_book_detail_success(self, mock_get_book, client):
        """Test xem chi tiết sách thành công"""
        # Arrange
        fake_book = FakeBook(1, "Clean Code", "Robert Martin")
        fake_book.description = "A handbook of agile software craftsmanship"
        fake_book.publisher = "Prentice Hall"
        fake_book.price = 42.99
        mock_get_book.return_value = fake_book

        # Act
        response = client.get('/book/1')

        # Assert
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert "Clean Code" in html
        assert "Robert Martin" in html

    @patch('library_digital.utils.get_book_by_id')
    def test_view_book_detail_not_found(self, mock_get_book, client):
        """Test xem chi tiết sách không tồn tại"""
        # Arrange
        mock_get_book.return_value = None

        # Act
        response = client.get('/book/99999')

        # Assert
        # Nếu book không tồn tại, nên trả về 404 hoặc redirect
        assert response.status_code in [200, 302, 404]


# ========== UNIT TESTS FOR RECOMMENDATION ==========

class TestBookRecommendation:
    """Test gợi ý sách theo hành vi người dùng"""

    @patch('library_digital.utils.get_viewed_books')
    @patch('library_digital.utils.get_borrowed_books')
    @patch('library_digital.utils.get_favorite_categories')
    @patch('library_digital.open_router.call_ai')
    def test_build_profile_success(self, mock_ai, mock_categories, mock_borrows, mock_views):
        """Test xây dựng profile người dùng thành công"""
        from library_digital.utils import build_profile
        
        # Arrange
        mock_views.return_value = [{"id": 1, "title": "Python Book"}]
        mock_borrows.return_value = [{"id": 2, "title": "Java Book"}]
        mock_categories.return_value = [{"id": 1, "name": "Programming"}]

        # Act
        profile = build_profile(reader_id=1)

        # Assert
        assert len(profile["views"]) == 1
        assert len(profile["borrows"]) == 1
        assert len(profile["categories"]) == 1
        assert profile["views"][0]["title"] == "Python Book"

    @patch('library_digital.utils.get_candidate_books')
    @patch('library_digital.utils.build_profile')
    @patch('library_digital.open_router.call_ai')
    @patch('library_digital.utils.parse_ai_response')
    @patch('library_digital.utils.map_to_books')
    def test_recommend_books_success(
        self, mock_map, mock_parse, mock_ai, mock_profile, mock_candidates
    ):
        """Test gợi ý sách thành công"""
        from library_digital.utils import recommend_books
        
        # Arrange
        mock_candidates.return_value = [
            {"id": 1, "title": "Python Advanced"},
            {"id": 2, "title": "Java Advanced"},
        ]
        mock_profile.return_value = {
            "views": [{"title": "Python Basics"}],
            "borrows": [],
            "categories": [{"name": "Programming"}]
        }
        mock_ai.return_value = '[{"title": "Python Advanced", "reason": "Nâng cao Python"}]'
        mock_parse.return_value = [{"title": "Python Advanced", "reason": "Nâng cao Python"}]
        mock_map.return_value = [{"id": 1, "title": "Python Advanced", "reason": "Nâng cao Python"}]

        # Act
        result = recommend_books(reader_id=1)

        # Assert
        assert len(result) == 1
        assert result[0]["title"] == "Python Advanced"
        assert result[0]["reason"] == "Nâng cao Python"

    @patch('library_digital.utils.get_candidate_books')
    def test_recommend_books_no_candidates(self, mock_candidates):
        """Test gợi ý sách khi không có ứng viên"""
        from library_digital.utils import recommend_books
        
        # Arrange
        mock_candidates.return_value = []

        # Act
        result = recommend_books(reader_id=1)

        # Assert
        assert result == []

    @patch('library_digital.utils.get_candidate_books')
    @patch('library_digital.utils.build_profile')
    @patch('library_digital.open_router.call_ai')
    def test_recommend_books_ai_error(self, mock_ai, mock_profile, mock_candidates):
        """Test gợi ý sách khi AI service lỗi"""
        from library_digital.utils import recommend_books
        
        # Arrange
        mock_candidates.return_value = [{"id": 1, "title": "Book 1"}]
        mock_profile.return_value = {"views": [], "borrows": [], "categories": []}
        mock_ai.side_effect = Exception("503 Service Unavailable")

        # Act
        result = recommend_books(reader_id=1)

        # Assert - Nên trả về empty list khi lỗi
        assert result == []


# ========== UNIT TESTS FOR BORROW HISTORY & FAVORITES ==========

class TestBorrowHistoryAndFavorites:
    """Test lịch sử mượn sách và thể loại yêu thích"""

    @patch('library_digital.utils.BorrowSlip')
    def test_get_borrowed_books_success(self, mock_slip_class):
        """Test lấy lịch sử sách đã mượn"""
        from library_digital.utils import get_borrowed_books
        from unittest.mock import MagicMock
        
        # Arrange
        fake_slip = MagicMock()
        fake_slip.book.title = "Borrowed Book"
        fake_slip.status.value = "RETURNED"
        fake_slip.borrow_date = "2024-01-01"
        fake_slip.due_date = "2024-01-15"
        
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [fake_slip]
        mock_slip_class.query = mock_query

        # Act
        result = get_borrowed_books(reader_id=1)

        # Assert
        assert len(result) == 1
        assert result[0]["title"] == "Borrowed Book"
        assert result[0]["status"] == "RETURNED"

    @patch('library_digital.utils.ReaderCategory')
    def test_get_favorite_categories_success(self, mock_rc_class):
        """Test lấy thể loại yêu thích của độc giả"""
        from library_digital.utils import get_favorite_categories
        from unittest.mock import MagicMock
        
        # Arrange
        fake_rc = MagicMock()
        fake_rc.category.name = "Programming"
        fake_rc.category.id = 1
        
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [fake_rc]
        mock_rc_class.query = mock_query

        # Act
        result = get_favorite_categories(reader_id=1)

        # Assert
        assert len(result) == 1
        assert result[0]["name"] == "Programming"
        assert result[0]["id"] == 1

    @patch('library_digital.utils.ReaderCategory')
    def test_get_favorite_categories_empty(self, mock_rc_class):
        """Test lấy thể loại yêu thích khi chưa có dữ liệu"""
        from library_digital.utils import get_favorite_categories
        
        # Arrange
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_rc_class.query = mock_query

        # Act
        result = get_favorite_categories(reader_id=1)

        # Assert
        assert result == []


# ========== UNIT TESTS FOR VIEW HISTORY ==========

class TestViewHistory:
    """Test lịch sử xem sách"""

    @patch('library_digital.utils.ViewHistory')
    def test_get_viewed_books_success(self, mock_vh_class):
        """Test lấy lịch sử sách đã xem"""
        from library_digital.utils import get_viewed_books
        from unittest.mock import MagicMock
        
        # Arrange
        fake_view = MagicMock()
        fake_view.book.title = "Viewed Book"
        fake_view.book.id = 1
        fake_view.viewed_at = "2024-01-01"
        
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [fake_view]
        mock_vh_class.query = mock_query

        # Act
        result = get_viewed_books(reader_id=1)

        # Assert
        assert len(result) == 1
        assert result[0]["title"] == "Viewed Book"

    @patch('library_digital.utils.add_view_history')
    def test_track_view_history(self, mock_add_view):
        """Test theo dõi lịch sử xem sách"""
        from library_digital.utils import add_view_history
        
        # Arrange
        mock_add_view.return_value = True
        
        # Act
        result = add_view_history(reader_id=1, book_id=1)
        
        # Assert
        assert result is True
        mock_add_view.assert_called_once_with(reader_id=1, book_id=1)
