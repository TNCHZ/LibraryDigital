from unittest.mock import patch, MagicMock
from library_digital.utils import delete_book

# TEST XÓA SÁCH THÀNH CÔNG
@patch('library_digital.utils.db.session.commit')
@patch('library_digital.utils.db.session.delete')
@patch('library_digital.utils.get_book_by_id')
def test_delete_book_success(mock_get_book, mock_delete, mock_commit):

    fake_book = MagicMock()
    mock_get_book.return_value = fake_book

    result = delete_book(book_id=1)

    assert result is True

    mock_get_book.assert_called_once_with(1)
    mock_delete.assert_called_once_with(fake_book)
    mock_commit.assert_called_once()

# TEST XÓA SÁCH THẤT BẠI
@patch('library_digital.utils.db.session.commit')
@patch('library_digital.utils.db.session.delete')
@patch('library_digital.utils.get_book_by_id')
def test_delete_book_not_found(mock_get_book, mock_delete, mock_commit):

    mock_get_book.return_value = None

    result = delete_book(book_id=999)

    assert result is False

    mock_delete.assert_not_called()
    mock_commit.assert_not_called()