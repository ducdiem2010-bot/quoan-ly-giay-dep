// Trang tài khoản: mặc định khóa ô nhập, bấm "Chỉnh sửa" để sửa, "Hủy" để khôi phục dữ liệu đã lưu.
(function () {
  const form = document.getElementById('profile-form');
  if (!form) return;
  const toggle = document.getElementById('edit-toggle');
  const save = document.getElementById('save-profile');
  const fields = form.querySelectorAll('[data-editable]');
  let editing = form.dataset.startEditing === '1';
  function render() {
    fields.forEach(f => { f.disabled = !editing; });
    save.disabled = !editing;
    form.classList.toggle('is-editing', editing);
    toggle.textContent = editing ? 'Hủy chỉnh sửa' : 'Chỉnh sửa';
  }
  toggle.addEventListener('click', () => {
    if (editing) form.reset();
    editing = !editing;
    render();
  });
  render();
})();
