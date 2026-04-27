from unittest.mock import patch, MagicMock
from library_digital.utils import add_borrow_slip
from library_digital.models.borrow_slip import BorrowStatus


@patch('library_digital.utils.db.session')
@patch('library_digital.utils.BorrowSlip')
def test_add_borrow_slip_success_with_string_status(mock_borrow_slip, mock_session):

    mock_instance = MagicMock()
    mock_borrow_slip.return_value = mock_instance

    result = add_borrow_slip(
        reader_id=1,
        librarian_id=2,
        book_id=3,
        borrow_date='2025-01-01',
        due_date='2025-01-10',
        return_date=None,
        status='BORROWING',
        note='test note'
    )

    # check return
    assert result == mock_instance

    # check convert Enum
    args, kwargs = mock_borrow_slip.call_args
    assert kwargs['status'] == BorrowStatus('BORROWING')

    # check db actions
    mock_session.add.assert_called_once_with(mock_instance)
    mock_session.commit.assert_called_once()


@patch('library_digital.utils.db.session')
@patch('library_digital.utils.BorrowSlip')
def test_add_borrow_slip_success_with_enum_status(mock_borrow_slip, mock_session):

    mock_instance = MagicMock()
    mock_borrow_slip.return_value = mock_instance

    result = add_borrow_slip(
        reader_id=1,
        librarian_id=2,
        book_id=3,
        borrow_date='2025-01-01',
        due_date='2025-01-10',
        return_date=None,
        status=BorrowStatus.BORROWING,
        note='test note'
    )

    assert result == mock_instance

    args, kwargs = mock_borrow_slip.call_args
    assert kwargs['status'] == BorrowStatus.BORROWING

    mock_session.add.assert_called_once_with(mock_instance)
    mock_session.commit.assert_called_once()


@patch('library_digital.utils.db.session')
@patch('library_digital.utils.BorrowSlip')
def test_add_borrow_slip_exception(mock_borrow_slip, mock_session):

    # giả lập lỗi khi add
    mock_session.add.side_effect = Exception("DB error")

    result = add_borrow_slip(
        reader_id=1,
        librarian_id=2,
        book_id=3,
        borrow_date='2025-01-01',
        due_date='2025-01-10',
        return_date=None,
        status='BORROWING',
        note='test note'
    )

    # phải rollback và return None
    assert result is None

    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()