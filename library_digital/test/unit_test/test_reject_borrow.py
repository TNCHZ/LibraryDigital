from unittest.mock import patch, MagicMock
import pytest
from library_digital.utils import reject_borrow_slip
from library_digital.models.borrow_slip import BorrowStatus


@patch('library_digital.utils.db.session')
@patch('library_digital.utils.get_borrow_slip_by_id')
def test_reject_borrow_slip_success_with_note(mock_get_slip, mock_session):

    mock_slip = MagicMock()
    mock_slip.status = BorrowStatus.RESERVED
    mock_slip.note = None

    mock_get_slip.return_value = mock_slip

    success, message = reject_borrow_slip(
        slip_id=1,
        librarian_id=10,
        note="Sách đã hết"
    )

    assert success is True
    assert message == "Từ chối đơn mượn thành công"

    assert mock_slip.status == BorrowStatus.REJECT
    assert mock_slip.librarian_id == 10
    assert mock_slip.note == "Sách đã hết"

    mock_session.commit.assert_called_once()


# =========================
# ✅ SUCCESS CASE (append note)
# =========================
@patch('library_digital.utils.db.session')
@patch('library_digital.utils.get_borrow_slip_by_id')
def test_reject_borrow_slip_append_note(mock_get_slip, mock_session):

    mock_slip = MagicMock()
    mock_slip.status = BorrowStatus.RESERVED
    mock_slip.note = "Ghi chú cũ"

    mock_get_slip.return_value = mock_slip

    success, message = reject_borrow_slip(
        slip_id=1,
        librarian_id=10,
        note="Không đủ điều kiện"
    )

    assert success is True
    assert "[Từ chối]" in mock_slip.note
    assert "Không đủ điều kiện" in mock_slip.note

    mock_session.commit.assert_called_once()


# =========================
# ✅ SUCCESS CASE (status BORROWING vẫn reject được)
# =========================
@patch('library_digital.utils.db.session')
@patch('library_digital.utils.get_borrow_slip_by_id')
def test_reject_borrow_slip_from_borrowing(mock_get_slip, mock_session):

    mock_slip = MagicMock()
    mock_slip.status = BorrowStatus.BORROWING
    mock_slip.note = None

    mock_get_slip.return_value = mock_slip

    success, message = reject_borrow_slip(
        slip_id=1,
        librarian_id=10
    )

    assert success is True
    assert mock_slip.status == BorrowStatus.REJECT

    mock_session.commit.assert_called_once()


# =========================
# ❌ NOT FOUND
# =========================
@patch('library_digital.utils.get_borrow_slip_by_id')
def test_reject_borrow_slip_not_found(mock_get_slip):

    mock_get_slip.return_value = None

    success, message = reject_borrow_slip(
        slip_id=1,
        librarian_id=10
    )

    assert success is False
    assert message == "Không tìm thấy đơn mượn"


# =========================
# ❌ INVALID STATUS
# =========================
@patch('library_digital.utils.get_borrow_slip_by_id')
def test_reject_borrow_slip_invalid_status(mock_get_slip):

    mock_slip = MagicMock()
    mock_slip.status = BorrowStatus.RETURNED  # không hợp lệ

    mock_get_slip.return_value = mock_slip

    success, message = reject_borrow_slip(
        slip_id=1,
        librarian_id=10
    )

    assert success is False
    assert message == "Không thể từ chối đơn mượn này"


# =========================
# ❌ EXCEPTION → ROLLBACK
# =========================
@patch('library_digital.utils.db.session')
@patch('library_digital.utils.get_borrow_slip_by_id')
def test_reject_borrow_slip_exception(mock_get_slip, mock_session):

    mock_slip = MagicMock()
    mock_slip.status = BorrowStatus.RESERVED

    mock_get_slip.return_value = mock_slip

    # giả lập lỗi DB
    mock_session.commit.side_effect = Exception("DB error")

    success, message = reject_borrow_slip(
        slip_id=1,
        librarian_id=10,
        note="test"
    )

    assert success is False
    assert "Lỗi" in message

    mock_session.rollback.assert_called_once()