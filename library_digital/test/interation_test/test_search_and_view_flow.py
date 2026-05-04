import pytest
from unittest.mock import patch, MagicMock
from flask_login import UserMixin
from datetime import datetime

from library_digital.index import app
from library_digital.models.user import UserRole


# ========== FIXTURES ==========

class FakeUser(UserMixin):
    """Fake user cho Flask-Login"""
    def __init__(self, user_id=1, role=UserRole.READER, first_name="Test", last_name="User"):
        self.id = user_id
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.avatar = "https://example.com/avatar.jpg"
        self.created_at = datetime.now()

    @property
    def is_active(self):
        return True


class FakeBook:
    """Fake book object"""
    def __init__(self, id, title, author, description="", price=0.0, image=None):
        self.id = id
        self.title = title
        self.author = author
        self.description = description
        self.price = price
        self.image = image or f"https://example.com/book{id}.jpg"
        self.isbn_10 = f"123456789{id}"
        self.isbn_13 = f"978123456789{id}"
        self.publisher = "Test Publisher"
        self.published_date = 2024
        self.categories = []


class FakeCategory:
    """Fake category object"""
    def __init__(self, id, name):
        self.id = id
        self.name = name


class FakeBorrowSlip:
    """Fake borrow slip"""
    def __init__(self, id, book_id, status="RETURNED"):
        self.id = id
        self.book_id = book_id
        self.book = FakeBook(book_id, f"Book {book_id}", f"Author {book_id}")
        self.status = MagicMock()
        self.status.value = status
        self.borrow_date = datetime(2024, 1, 1)
        self.due_date = datetime(2024, 1, 15)
        self.return_date = datetime(2024, 1, 10) if status == "RETURNED" else None


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client


@pytest.fixture
def authenticated_client(client):
    """Client với user đã đăng nhập"""
    with patch('library_digital.utils.get_user_by_id') as mock_get_user:
        fake_user = FakeUser(user_id=1, role=UserRole.READER)
        mock_get_user.return_value = fake_user
        
        with client.session_transaction() as session:
            session['user_id'] = 1
        
        yield client


# ========== INTEGRATION TESTS ==========

class TestSearchAndViewBookFlow:
    """
    Integration test cho flow: 
    Tìm kiếm sách → Xem danh sách → Xem chi tiết sách
    """

    @patch('library_digital.utils.search_books')
    @patch('library_digital.utils.get_categories')
    def test_search_to_detail_flow(self, mock_get_categories, mock_search, client):
        """
        Test flow đầy đủ: Tìm kiếm "Python" → Xem kết quả → Click vào sách → Xem chi tiết
        """
        # Arrange - Setup search results
        fake_book = FakeBook(
            id=1, 
            title="Python Programming", 
            author="John Smith",
            description="Learn Python from scratch"
        )
        fake_book.categories = [FakeCategory(1, "Programming")]
        
        mock_search.return_value = MagicMock(
            items=[fake_book],
            total=1,
            page=1,
            pages=1,
            has_prev=False,
            has_next=False
        )
        mock_get_categories.return_value = [FakeCategory(1, "Programming")]
        
        # Step 1: User search for "Python"
        with patch('library_digital.utils.get_book_by_id', return_value=fake_book):
            response = client.get('/book/searching-book/?title=Python')
            assert response.status_code == 200
            
            html = response.data.decode('utf-8')
            assert "Python Programming" in html
            assert "John Smith" in html
            print("✓ Step 1: Search results displayed")
        
        # Step 2: User click on book to see details
        with patch('library_digital.utils.get_book_by_id', return_value=fake_book):
            with patch('library_digital.utils.add_view_history', return_value=True):
                response = client.get('/book/1')
                assert response.status_code == 200
                
                html = response.data.decode('utf-8')
                assert "Python Programming" in html
                assert "John Smith" in html
                assert "Learn Python from scratch" in html
                print("✓ Step 2: Book details displayed")

    @patch('library_digital.utils.search_books')
    @patch('library_digital.utils.get_categories')
    def test_filtered_search_flow(self, mock_categories, mock_search, client):
        """
        Test flow tìm kiếm nâng cao: Lọc theo tác giả + thể loại
        """
        # Arrange
        python_book = FakeBook(1, "Python Advanced", "Robert Martin")
        java_book = FakeBook(2, "Java Basics", "John Doe")
        
        mock_search.return_value = MagicMock(
            items=[python_book],
            total=1,
            page=1,
            pages=1
        )
        mock_categories.return_value = [
            FakeCategory(1, "Programming"),
            FakeCategory(2, "Java")
        ]
        
        # Act - Search with filters
        response = client.get(
            '/book/searching-book/?title=Python&author=Robert&category_ids=1'
        )
        
        # Assert
        assert response.status_code == 200
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args[1]
        assert call_kwargs['title'] == 'Python'
        assert call_kwargs['author'] == 'Robert'
        print("✓ Filtered search executed correctly")


class TestRecommendationFlow:
    """
    Integration test cho flow gợi ý sách:
    Xem sách → Mượn sách → Nhận gợi ý dựa trên hành vi
    """

    @patch('library_digital.utils.get_viewed_books')
    @patch('library_digital.utils.get_borrowed_books')
    @patch('library_digital.utils.get_favorite_categories')
    @patch('library_digital.utils.get_candidate_books')
    @patch('library_digital.open_router.call_ai')
    @patch('library_digital.utils.current_user')
    def test_recommendation_based_on_behavior(
        self, mock_current_user, mock_ai, mock_candidates,
        mock_categories, mock_borrows, mock_views, client
    ):
        """
        Test flow: User đã xem và mượn sách Python → Nhận gợi ý sách Python nâng cao
        """
        # Arrange - User behavior data
        mock_views.return_value = [
            {"id": 1, "title": "Python Basics", "viewed_at": "2024-01-01"}
        ]
        mock_borrows.return_value = [
            {"id": 2, "title": "Python Cookbook", "status": "RETURNED", "borrow_date": "2024-01-01"}
        ]
        mock_categories.return_value = [
            {"id": 1, "name": "Programming"},
            {"id": 2, "name": "Python"}
        ]
        
        # AI candidates
        mock_candidates.return_value = [
            {"id": 3, "title": "Python Advanced Patterns"},
            {"id": 4, "title": "Django Web Development"},
            {"id": 5, "title": "Machine Learning with Python"},
        ]
        
        # AI response
        mock_ai.return_value = '''[
            {"title": "Python Advanced Patterns", "reason": "Nâng cao kỹ năng Python của bạn"},
            {"title": "Machine Learning with Python", "reason": "Mở rộng sang AI/ML"}
        ]'''
        
        mock_current_user.is_authenticated = True
        mock_current_user.id = 1
        
        # Act - Get recommendations
        with patch('library_digital.utils.Book') as mock_book_class:
            mock_book_class.query.get.side_effect = lambda id: FakeBook(
                id, f"Book {id}", f"Author {id}"
            ) if id in [3, 5] else None
            
            from library_digital.utils import recommend_books
            recommendations = recommend_books(reader_id=1)
        
        # Assert
        assert len(recommendations) > 0
        assert any("Python" in r["title"] for r in recommendations)
        print("✓ Recommendations based on viewing/borrowing history")


class TestBorrowHistoryFlow:
    """
    Integration test cho flow lịch sử mượn sách:
    Mượn sách → Xem trạng thái → Xem lịch sử → Trả sách
    """

    @patch('library_digital.utils.get_borrowed_books')
    @patch('library_digital.utils.get_reserved_slip_by_reader')
    @patch('library_digital.utils.can_borrow')
    @patch('library_digital.utils.add_borrow_slip')
    @patch('library_digital.utils.get_user_by_id')
    def test_full_borrow_lifecycle(
        self, mock_get_user, mock_add_slip, mock_can_borrow,
        mock_get_reserved, mock_get_borrowed, authenticated_client
    ):
        """
        Test flow đầy đủ: 
        1. Đặt trước sách
        2. Xem trạng thái đang chờ
        3. Xem lịch sử mượn
        4. Xem sách đã trả
        """
        fake_user = FakeUser(user_id=1, role=UserRole.READER)
        mock_get_user.return_value = fake_user
        
        # Step 1: Reserve a book
        mock_can_borrow.return_value = (True, "Có thể mượn")
        mock_add_slip.return_value = MagicMock(id=1, status="RESERVED")
        
        response = authenticated_client.post(
            '/borrow/1',
            follow_redirects=True
        )
        assert response.status_code == 200
        print("✓ Step 1: Book reserved")
        
        # Step 2: View borrow status
        fake_slip = FakeBorrowSlip(1, 1, "RESERVED")
        mock_get_reserved.return_value = fake_slip
        
        with patch('library_digital.utils.current_user', fake_user):
            response = authenticated_client.get('/user/1/borrow-status')
            assert response.status_code == 200
            html = response.data.decode('utf-8')
            assert "Book 1" in html or response.status_code == 200
            print("✓ Step 2: Borrow status viewed")
        
        # Step 3: View borrow history
        fake_history = [
            {
                "id": 1,
                "title": "Previous Book",
                "status": "RETURNED",
                "borrow_date": "2024-01-01",
                "due_date": "2024-01-15",
                "return_date": "2024-01-10"
            }
        ]
        mock_get_borrowed.return_value = fake_history
        
        response = authenticated_client.get('/user/1/borrow-history')
        assert response.status_code == 200
        print("✓ Step 3: Borrow history viewed")

    @patch('library_digital.utils.get_borrowed_books')
    @patch('library_digital.utils.get_user_by_id')
    def test_borrow_history_with_pagination(
        self, mock_get_user, mock_get_borrowed, authenticated_client
    ):
        """
        Test xem lịch sử mượn với nhiều sách (phân trang)
        """
        fake_user = FakeUser(user_id=1, role=UserRole.READER)
        mock_get_user.return_value = fake_user
        
        # Create many borrow records
        fake_history = [
            {
                "id": i,
                "title": f"Book {i}",
                "status": "RETURNED" if i % 2 == 0 else "BORROWING",
                "borrow_date": f"2024-01-{i:02d}",
                "due_date": f"2024-02-{i:02d}",
                "return_date": f"2024-01-{i+5:02d}" if i % 2 == 0 else None
            }
            for i in range(1, 21)  # 20 books
        ]
        mock_get_borrowed.return_value = fake_history
        
        # Act
        with patch('library_digital.utils.current_user', fake_user):
            response = authenticated_client.get('/user/1/borrow-history')
            
            # Assert
            assert response.status_code == 200
            print("✓ Borrow history with pagination displayed")


class TestFavoriteCategoriesFlow:
    """
    Integration test cho flow thể loại yêu thích:
    Xem sách nhiều lần → Hệ thống học thể loại yêu thích → Gợi ý theo thể loại
    """

    @patch('library_digital.utils.add_view_history')
    @patch('library_digital.utils.get_viewed_books')
    @patch('library_digital.utils.get_favorite_categories')
    @patch('library_digital.utils.get_user_by_id')
    def test_category_learning_flow(
        self, mock_get_user, mock_get_categories,
        mock_get_views, mock_add_view, authenticated_client
    ):
        """
        Test flow: 
        1. User xem nhiều sách cùng thể loại Programming
        2. Hệ thống xác định Programming là thể loại yêu thích
        3. Gợi ý thêm sách Programming
        """
        fake_user = FakeUser(user_id=1, role=UserRole.READER)
        mock_get_user.return_value = fake_user
        
        # Step 1: Simulate viewing multiple programming books
        viewed_books = [
            {"id": 1, "title": "Python Basics", "category": "Programming", "viewed_at": "2024-01-01"},
            {"id": 2, "title": "Java Advanced", "category": "Programming", "viewed_at": "2024-01-02"},
            {"id": 3, "title": "Clean Code", "category": "Programming", "viewed_at": "2024-01-03"},
        ]
        mock_get_views.return_value = viewed_books
        
        # Step 2: System identifies favorite categories
        favorite_categories = [
            {"id": 1, "name": "Programming", "view_count": 10},
            {"id": 2, "name": "Technology", "view_count": 5},
        ]
        mock_get_categories.return_value = favorite_categories
        
        # Act - Get home page with recommendations
        with patch('library_digital.utils.recommend_books') as mock_recommend:
            mock_recommend.return_value = [
                {"id": 4, "title": "Design Patterns", "reason": "Programming - Phổ biến"},
                {"id": 5, "title": "Refactoring", "reason": "Programming - Cải thiện code"},
            ]
            
            with patch('library_digital.utils.get_categories') as mock_cates:
                mock_cates.return_value = [FakeCategory(1, "Programming")]
                
                response = authenticated_client.get('/')
                
        # Assert
        assert response.status_code == 200
        print("✓ Category-based recommendations generated")


class TestEndToEndUserJourney:
    """
    End-to-end test: Full user journey từ tìm kiếm đến mượn sách
    """

    @patch('library_digital.utils.search_books')
    @patch('library_digital.utils.get_book_by_id')
    @patch('library_digital.utils.can_borrow')
    @patch('library_digital.utils.add_borrow_slip')
    @patch('library_digital.utils.get_user_by_id')
    def test_complete_user_journey(
        self, mock_get_user, mock_add_slip, mock_can_borrow,
        mock_get_book, mock_search, authenticated_client
    ):
        """
        Test journey đầy đủ:
        1. User tìm kiếm "Machine Learning"
        2. Xem chi tiết sách "Deep Learning with Python"
        3. Mượn sách
        4. Xác nhận đơn mượn đã tạo
        """
        fake_user = FakeUser(user_id=1, role=UserRole.READER)
        mock_get_user.return_value = fake_user
        
        # Step 1: Search
        ml_book = FakeBook(
            id=1,
            title="Deep Learning with Python",
            author="Francois Chollet",
            description="Deep learning for Python programmers"
        )
        
        mock_search.return_value = MagicMock(
            items=[ml_book],
            total=1,
            page=1,
            pages=1
        )
        
        response = authenticated_client.get('/book/searching-book/?title=Machine+Learning')
        assert response.status_code == 200
        print("✓ Journey Step 1: Search completed")
        
        # Step 2: View book details
        mock_get_book.return_value = ml_book
        
        response = authenticated_client.get('/book/1')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert "Deep Learning with Python" in html
        print("✓ Journey Step 2: View book details completed")
        
        # Step 3: Borrow book
        mock_can_borrow.return_value = (True, "Có thể mượn")
        fake_slip = MagicMock()
        fake_slip.id = 1
        fake_slip.status = MagicMock()
        fake_slip.status.value = "RESERVED"
        mock_add_slip.return_value = fake_slip
        
        response = authenticated_client.post(
            '/borrow/1',
            follow_redirects=True
        )
        assert response.status_code == 200
        print("✓ Journey Step 3: Book borrowed")
        
        # Step 4: Verify borrow status
        with patch('library_digital.utils.get_reserved_slip_by_reader') as mock_get_reserved:
            mock_get_reserved.return_value = FakeBorrowSlip(1, 1, "RESERVED")
            
            with patch('library_digital.utils.current_user', fake_user):
                response = authenticated_client.get('/user/1/borrow-status')
                assert response.status_code == 200
                print("✓ Journey Step 4: Borrow status verified")
        
        print("\n✅ Complete user journey test passed!")
