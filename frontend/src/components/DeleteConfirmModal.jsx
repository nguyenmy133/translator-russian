import React from 'react'

export default function DeleteConfirmModal({ count, onConfirm, onCancel }) {
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-icon">🗑️</div>
        <h3 className="modal-title">Xác nhận xóa</h3>
        <p className="modal-desc">
          Bạn có chắc muốn xóa <strong>{count} bài dịch</strong> đã chọn?
          <br />
          <span className="text-danger" style={{ fontSize: 12 }}>
            File gốc và file đã dịch cũng sẽ bị xóa vĩnh viễn.
          </span>
        </p>
        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={onCancel}>
            Hủy
          </button>
          <button className="btn btn-danger" onClick={onConfirm}>
            🗑️ Xóa {count} bài
          </button>
        </div>
      </div>
    </div>
  )
}
