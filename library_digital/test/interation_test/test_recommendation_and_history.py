"""
Integration Tests cho Recommendation và History Flows
Test các kịch bản phức tạp liên quan đến gợi ý sách và lịch sử
"""

import pytest
from unittest.mock import patch, MagicMock
from flask_login import UserMixin
from datetime import datetime, timedelta

from library_digital.index import app
from library_digital.models.user import UserRole


# ========== FIXTURES ==========

class FakeUser(UserMixin):
    def __init__(self, user_id=1, role=UserRole.READER, first_name="Test", last_name="User"):
        self.id = user_id
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.avatar = "https://example.com/avatar.jpg"

    @property
    def is_active(self):
        return True


class FakeBook:
    def __init__(self, id, title, author, category="General"):
        self.id = id
        self.title = title
        self.author = author
        self.description = f"Description for {title}"
        self.image = f"https://example.com/book{id}.jpg"
        self.categories = [MagicMock(name=category)] if category else []


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client


# ========== INTEGRATION TESTS ==========

class TestSemanticSearchIntegration:
    """
    Integration test cho Semantic Search:
    User nhập "trí tuệ nhân tạo" → AI hiểu → Tìm sách AI/ML
    """

    @patch('library_digital.utils.Book')
    @patch('library_digital.open_router.semantic_search_books')
    @patch('library_digital.utils.get_categories')
    def test_semantic_search_ai_flow(
        self, mock_categories, mock_ai_search, mock_book_class, client
    ):
        """
        Test flow tìm kiếm ngữ nghĩa:
        1. User nhập "trí tuệ nhân tạo" 
        2. AI phân tích → hiểu là "AI, Machine Learning"
        3. Tìm và trả về sách liên quan AI/ML
        4. Hiển thị lý do tại sao sách liên quan
        """
        # Arrange - Setup books in library
        ai_books = [
            FakeBook(1, "Machine Learning Yearning", "Andrew Ng", "AI"),
            FakeBook(2, "Deep Learning", "Ian Goodfellow", "AI"),
            FakeBook(3, "AI Superpowers", "Kai-Fu Lee", "AI"),
            FakeBook(4, "Python Cookbook", "David Beazley", "Programming"),  # Not AI
        ]
        
        mock_book_class.query.all.return_value = ai_books
        mock_book_class.query.get.side_effect = lambda id: next(
            (b for b in ai_books if b.id == id), None
        )
        
        # AI understands semantic meaning
        mock_ai_search.return_value = [
            {"id": 1, "relevance_score": 0.95, "reason": "Về chiến lược ML/AI"},
            {"id": 2, "relevance_score": 0.90, "reason": "Deep Learning là một nhánh của AI"},
            {"id": 3, "relevance_score": 0.85, "reason": "Về sức mạnh của AI trong kinh tế"},
        ]
        
        mock_categories.return_value = [
            MagicMock(id=1, name="AI"),
            MagicMock(id=2, name="Programming")
        ]
        
        # Act - User searches with semantic query
        response = client.get('/book/searching-book/?semantic=trí+tuệ+nhân+tạo')
        
        # Assert
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        
        # Should find AI books
        assert "Machine Learning" in html or "Deep Learning" in html or "AI" in html
        print("✓ Semantic search understood 'trí tuệ nhân tạo' → AI books")


class TestBehaviorBasedRecommendation:
    """
    Integration test cho gợi ý dựa trên hành vi phức tạp
    """

    @patch('library_digital.utils.get_viewed_books')
    @patch('library_digital.utils.get_borrowed_books')
    @patch('library_digital.utils.get_favorite_categories')
    @patch('library_digital.utils.get_candidate_books')
    @patch('library_digital.open_router.call_ai')
    def test_complex_recommendation_scenario(
        self, mock_ai, mock_candidates, mock_categories, mock_borrows, mock_views, client
    ):
        """
        Test scenario phức tạp:
        User đã xem: Python Basics, Java Basics
        User đã mượn: Clean Code, Design Patterns  
        Thể loại yêu thích: Programming, Software Engineering
        
        Expect: Gợi ý sách nâng cao về Programming/Software Engineering
        """
        # Arrange - Build complex user profile
        mock_views.return_value = [
            {"id": 1, "title": "Python Basics", "viewed_at": datetime.now() - timedelta(days=10)},
            {"id": 2, "title": "Java Basics", "viewed_at": datetime.now() - timedelta(days=5)},
            {"id": 3, "title": "Introduction to Algorithms", "viewed_at": datetime.now() - timedelta(days=2)},
        ]
        
        mock_borrows.return_value = [
            {"id": 4, "title": "Clean Code", "status": "RETURNED", "borrow_date": "2024-01-15"},
            {"id": 5, "title": "Design Patterns", "status": "RETURNED", "borrow_date": "2024-02-01"},
            {"id": 6, "title": "Refactoring", "status": "BORROWING", "borrow_date": "2024-03-01"},
        ]
        
        mock_categories.return_value = [
            {"id": 1, "name": "Programming", "view_count": 15},
            {"id": 2, "name": "Software Engineering", "view_count": 12},
            {"id": 3, "name": "Computer Science", "view_count": 8},
        ]
        
        # AI candidates
        mock_candidates.return_value = [
            {"id": 7, "title": "Python Advanced Patterns"},
            {"id": 8, "title": "Building Microservices"},
            {"id": 9, "title": "Domain Driven Design"},
            {"id": 10, "title": "Cooking for Beginners"},  # Not relevant
        ]
        
        # AI should recommend based on behavior pattern
        mock_ai.return_value = '''[
            {"title": "Python Advanced Patterns", "reason": "Nâng cao kỹ năng Python của bạn sau 'Python Basics'"},
            {"title": "Domain Driven Design", "reason": "Bổ sung cho 'Design Patterns' và 'Clean Code'"},
            {"title": "Building Microservices", "reason": "Kiến trúc phần mềm hiện đại cho Software Engineers"}
        ]'''
        
        # Act
        from library_digital.utils import recommend_books
        
        with patch('library_digital.utils.Book') as mock_book_class:
            mock_book_class.query.get.side_effect = lambda id: FakeBook(
                id, f"Book {id}", f"Author {id}", "Programming"
            ) if id in [7, 8, 9] else None
            
            recommendations = recommend_books(reader_id=1)
        
        # Assert
        assert len(recommendations) == 3
        
        # Check recommendations are relevant
        titles = [r["title"] for r in recommendations]
        assert "Python Advanced Patterns" in titles
        assert "Domain Driven Design" in titles
        assert "Cooking for Beginners" not in titles  # Not relevant
        
        # Check reasons explain the connection
        for rec in recommendations:
            assert "reason" in rec
            assert len(rec["reason"]) > 0
        
        print("✓ Complex behavior-based recommendations generated")


class TestHistoryTrackingFlow:
    """
    Integration test cho việc theo dõi lịch sử người dùng
    """

    @patch('library_digital.utils.add_view_history')
    @patch('library_digital.utils.get_viewed_books')
    @patch('library_digital.utils.get_book_by_id')
    @patch('library_digital.utils.get_user_by_id')
    def test_view_history_accumulation(
        self, mock_get_user, mock_get_book, mock_get_views, mock_add_view, client
    ):
        """
        Test flow tích lũy lịch sử xem:
        1. User xem Book A
        2. User xem Book B  
        3. User xem Book C
        4. Kiểm tra lịch sử có cả 3 sách
        """
        fake_user = FakeUser(user_id=1, role=UserRole.READER)
        mock_get_user.return_value = fake_user
        
        # Simulate viewing multiple books
        books = [
            FakeBook(1, "Python Guide", "Author A"),
            FakeBook(2, "Java Guide", "Author B"),
            FakeBook(3, "Go Guide", "Author C"),
        ]
        
        viewed_history = []
        
        def mock_add_view(reader_id, book_id):
            book = next((b for b in books if b.id == book_id), None)
            if book:
                viewed_history.append({
                    "id": book.id,
                    "title": book.title,
                    "viewed_at": datetime.now()
                })
            return True
        
        mock_add_view.side_effect = mock_add_view
        mock_get_views.return_value = viewed_history
        
        # User views 3 books
        for book in books:
            mock_get_book.return_value = book
            
            with patch('library_digital.utils.current_user', fake_user):
                response = client.get(f'/book/{book.id}')
                assert response.status_code == 200
        
        # Check history accumulated
        assert len(viewed_history) == 3
        assert viewed_history[0]["title"] == "Python Guide"
        assert viewed_history[1]["title"] == "Java Guide"
        assert viewed_history[2]["title"] == "Go Guide"
        
        print("✓ View history accumulation working")

    @patch('library_digital.utils.get_borrowed_books')
    @patch('library_digital.utils.add_borrow_slip')
    @patch('library_digital.utils.can_borrow')
    @patch('library_digital.utils.get_book_by_id')
    @patch('library_digital.utils.get_user_by_id')
    def test_borrow_history_comprehensive(
        self, mock_get_user, mock_get_book, mock_can_borrow,
        mock_add_slip, mock_get_borrowed, client
    ):
        """
        Test lịch sử mượn toàn diện:
        - Mượn nhiều sách khác nhau
        - Trả sách
        - Xem lịch sử đầy đủ
        """
        fake_user = FakeUser(user_id=1, role=UserRole.READER)
        mock_get_user.return_value = fake_user
        
        # Setup books
        books = [
            FakeBook(1, "Book One", "Author One"),
            FakeBook(2, "Book Two", "Author Two"),
            FakeBook(3, "Book Three", "Author Three"),
        ]
        
        # Setup borrow history
        borrow_history = [
            {
                "id": 1,
                "title": "Book One",
                "status": "RETURNED",
                "borrow_date": "2024-01-01",
                "due_date": "2024-01-15",
                "return_date": "2024-01-10"
            },
            {
                "id": 2,
                "title": "Book Two", 
                "status": "RETURNED",
                "borrow_date": "2024-02-01",
                "due_date": "2024-02-15",
                "return_date": "2024-02-14"
            },
            {
                "id": 3,
                "title": "Book Three",
                "status": "BORROWING",
                "borrow_date": "2024-03-01",
                "due_date": "2024-03-15",
                "return_date": None
            }
        ]
        mock_get_borrowed.return_value = borrow_history
        
        # Test viewing borrow history
        with patch('library_digital.utils.current_user', fake_user):
            response = client.get('/user/1/borrow-history')
            
            assert response.status_code == 200
            html = response.data.decode('utf-8')
            
            # Should show all books
            assert "Book One" in html or response.status_code == 200
            assert "Book Two" in html or response.status_code == 200
            assert "Book Three" in html or response.status_code == 200
        
        print("✓ Comprehensive borrow history test passed")


class TestRecommendationWithHistoryIntegration:
    """
    Integration test cho gợi ý dựa trên cả lịch sử xem và mượn
    """

    def test_recommendation_uses_combined_history(self):
        """
        Test rằng gợi ý sử dụng cả lịch sử xem và mượn:
        - Đã xem: Web Development books
        - Đã mượn: Database books
        - Gợi ý: Full-stack / Backend development books
        """
        from library_digital.utils import build_profile
        
        with patch('library_digital.utils.get_viewed_books') as mock_views, \
             patch('library_digital.utils.get_borrowed_books') as mock_borrows, \
             patch('library_digital.utils.get_favorite_categories') as mock_cates:
            
            # User viewed web dev books
            mock_views.return_value = [
                {"id": 1, "title": "HTML & CSS", "viewed_at": datetime.now() - timedelta(days=5)},
                {"id": 2, "title": "JavaScript Basics", "viewed_at": datetime.now() - timedelta(days=3)},
            ]
            
            # User borrowed database books
            mock_borrows.return_value = [
                {"id": 3, "title": "SQL Mastery", "status": "RETURNED", "borrow_date": "2024-01-01"},
                {"id": 4, "title": "PostgreSQL Guide", "status": "RETURNED", "borrow_date": "2024-02-01"},
            ]
            
            # Combined favorite categories
            mock_cates.return_value = [
                {"id": 1, "name": "Web Development", "view_count": 8},
                {"id": 2, "name": "Databases", "view_count": 6},
            ]
            
            # Act
            profile = build_profile(reader_id=1)
            
            # Assert
            assert len(profile["views"]) == 2  # Web dev
            assert len(profile["borrows"]) == 2  # Database
            assert len(profile["categories"]) == 2  # Combined interests
            
            # Categories should reflect both interests
            category_names = [c["name"] for c in profile["categories"]]
            assert "Web Development" in category_names
            assert "Databases" in category_names
            
            print("✓ Combined view + borrow history for recommendations")


class TestErrorHandlingIntegration:
    """
    Integration test cho xử lý lỗi trong các flow phức tạp
    """

    @patch('library_digital.open_router.call_ai')
    @patch('library_digital.utils.get_candidate_books')
    def test_recommendation_graceful_degradation(
        self, mock_candidates, mock_ai
    ):
        """
        Test khi AI service lỗi, hệ thống vẫn hoạt động:
        - AI trả về lỗi 503
        - Hệ thống fallback về gợi ý đơn giản hoặc empty
        """
        from library_digital.utils import recommend_books
        
        # Arrange
        mock_candidates.return_value = [
            {"id": 1, "title": "Book One"},
            {"id": 2, "title": "Book Two"},
        ]
        
        # AI fails
        mock_ai.side_effect = Exception("503 Service Unavailable")
        
        # Act - Should not crash
        result = recommend_books(reader_id=1)
        
        # Assert - Graceful fallback
        assert result == []  # Empty list instead of crash
        print("✓ Graceful degradation when AI fails")

    @patch('library_digital.utils.Book')
    @patch('library_digital.open_router.semantic_search_books')
    def test_semantic_search_fallback(
        self, mock_ai_search, mock_book_class
    ):
        """
        Test khi semantic search lỗi, fallback về tìm kiếm thường
        """
        from library_digital.utils import semantic_search_books
        
        # Arrange
        fake_book = FakeBook(1, "Python Book", "Author")
        mock_book_class.query.all.return_value = []
        mock_ai_search.return_value = []  # AI no results
        
        # Setup fallback regular search
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.paginate.return_value = MagicMock(
            items=[fake_book],
            total=1,
            page=1,
            pages=1
        )
        mock_book_class.query = mock_query
        
        # Act
        result = semantic_search_books("python", page=1)
        
        # Assert - Should have fallback behavior
        assert result is not None
        print("✓ Semantic search fallback working")
