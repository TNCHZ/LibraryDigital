from unittest.mock import patch, MagicMock
from library_digital.utils import approve_borrow_slip
from library_digital.models.borrow_slip import BorrowStatus


# =========================
# ✅ SUCCESS CASE
# =========================
@patch('library_digital.utils.db.session')
@patch('library_digital.utils.get_borrow_slip_by_id')
def test_approve_borrow_slip_success(mock_get_slip, mock_session):

    mock_slip = MagicMock()
    mock_slip.status = BorrowStatus.RESERVED

    mock_get_slip.return_value = mock_slip

    success, message = approve_borrow_slip(
        slip_id=1,
        librarian_id=99
    )

    assert success is True
    assert message == "Duyệt đơn mượn thành công"

    # check cập nhật dữ liệu
    assert mock_slip.status == BorrowStatus.BORROWING
    assert mock_slip.librarian_id == 99
    assert mock_slip.borrow_date is not None
    assert mock_slip.due_date is not None

    # check commit
    mock_session.commit.assert_called_once()

    # check đúng hạn 30 ngày
    assert (mock_slip.due_date - mock_slip.borrow_date).days == 30


# =========================
# ❌ NOT FOUND CASE
# =========================
@patch('library_digital.utils.get_borrow_slip_by_id')
def test_approve_borrow_slip_not_found(mock_get_slip):

    mock_get_slip.return_value = None

    success, message = approve_borrow_slip(
        slip_id=1,
        librarian_id=99
    )

    assert success is False
    assert message == "Không tìm thấy đơn mượn"


# =========================
# ❌ INVALID STATUS CASE
# =========================
@patch('library_digital.utils.get_borrow_slip_by_id')
def test_approve_borrow_slip_invalid_status(mock_get_slip):

    mock_slip = MagicMock()
    mock_slip.status = BorrowStatus.BORROWING  # không phải RESERVED

    mock_get_slip.return_value = mock_slip

    success, message = approve_borrow_slip(
        slip_id=1,
        librarian_id=99
    )

    assert success is False
    assert message == "Đơn mượn không ở trạng thái chờ duyệt"


# =========================
# ❌ EXCEPTION CASE
# =========================
@patch('library_digital.utils.db.session')
@patch('library_digital.utils.get_borrow_slip_by_id')
def test_approve_borrow_slip_exception(mock_get_slip, mock_session):

    mock_slip = MagicMock()
    mock_slip.status = BorrowStatus.RESERVED

    mock_get_slip.return_value = mock_slip

    # giả lập lỗi khi commit
    mock_session.commit.side_effect = Exception("DB error")

    success, message = approve_borrow_slip(
        slip_id=1,
        librarian_id=99
    )

    assert success is False
    assert "Lỗi" in message

    # phải rollback
    mock_session.rollback.assert_called_once()