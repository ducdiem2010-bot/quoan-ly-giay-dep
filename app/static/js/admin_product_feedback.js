(() => {
  'use strict';

  const toast = (message, kind = 'warning') => {
    document.querySelector('.w3-feedback-toast')?.remove();
    const node = document.createElement('div');
    node.className = 'w3-feedback-toast';
    node.dataset.kind = kind;
    node.setAttribute('role', kind === 'error' ? 'alert' : 'status');
    node.setAttribute('aria-live', 'polite');
    node.textContent = message;
    document.body.append(node);
    window.setTimeout(() => node.remove(), 4800);
  };

  const confirmAction = (message, acceptText = 'Tiếp tục', danger = false) => new Promise(resolve => {
    const backdrop = document.createElement('div');
    backdrop.className = 'w3-confirm-backdrop';
    backdrop.innerHTML = `<section class="w3-confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="w3-confirm-title">
      <h2 id="w3-confirm-title">Xác nhận thao tác</h2><p></p>
      <div class="w3-confirm-actions"><button type="button" data-choice="cancel">Hủy</button><button type="button" class="${danger ? 'w3-confirm-danger' : 'w3-confirm-accept'}" data-choice="yes"></button></div>
    </section>`;
    backdrop.querySelector('p').textContent = message;
    backdrop.querySelector('[data-choice="yes"]').textContent = acceptText;
    document.body.append(backdrop);
    const finish = value => { backdrop.remove(); resolve(value); };
    backdrop.querySelector('[data-choice="cancel"]').addEventListener('click', () => finish(false));
    backdrop.querySelector('[data-choice="yes"]').addEventListener('click', () => finish(true));
    backdrop.addEventListener('click', event => { if (event.target === backdrop) finish(false); });
    backdrop.addEventListener('keydown', event => { if (event.key === 'Escape') finish(false); });
    backdrop.querySelector('[data-choice="cancel"]').focus();
  });

  const validateIntegerStock = field => {
    const value = field.value.trim();
    const valid = /^[0-9]+$/.test(value) && Number.isSafeInteger(Number(value)) && Number(value) <= 2147483647;
    field.setCustomValidity(valid ? '' : 'Tồn kho phải là số nguyên không âm, tối đa 2.147.483.647.');
    return valid;
  };

  document.addEventListener('DOMContentLoaded', () => {
    // Cảnh báo tồn kho bằng 0 (tổng tồn trên bảng SP và tồn của từng biến thể).
    document.querySelectorAll('[data-stock-value]').forEach(cell => {
      const value = Number(cell.dataset.stockValue);
      if (Number.isFinite(value) && value <= 0 && !cell.querySelector('.w3-stock-zero')) {
        const badge = document.createElement('span');
        badge.className = 'w3-stock-zero';
        badge.textContent = 'Hết hàng · tồn 0';
        cell.append(badge);
      }
    });

    // Chỉ hỏi xác nhận khi form hoặc nút submit có data-w3-confirm.
    // Hỗ trợ cả nút formaction trong form sửa sản phẩm (ví dụ xóa ảnh).
    document.addEventListener('submit', async event => {
      const form = event.target;
      if (!(form instanceof HTMLFormElement) || form.dataset.confirmed === 'true') return;
      const submitter = event.submitter;
      const message = submitter?.dataset.w3Confirm || form.dataset.w3Confirm;
      if (!message) return;
      event.preventDefault();
      const ok = await confirmAction(
        message,
        submitter?.dataset.confirmLabel || form.dataset.confirmLabel || 'Xác nhận',
        (submitter?.dataset.confirmDanger || form.dataset.confirmDanger) === 'true'
      );
      if (ok) {
        form.dataset.confirmed = 'true';
        if (submitter) form.requestSubmit(submitter);
        else form.requestSubmit(); // giữ nguyên hidden csrf_token và phương thức POST
      }
    });

    // Kiểm tra form sản phẩm/biến thể. form.elements bao gồm cả input gắn bằng thuộc tính form="...".
    document.querySelectorAll('form[data-w3-feedback-form]').forEach(form => {
      const controls = Array.from(form.elements).filter(el => el.matches?.('input,select,textarea'));
      const feedback = form.querySelector('[data-form-feedback]');

      // Với form dùng native validation, vẫn bổ sung thông báo dễ hiểu.
      if (!form.noValidate) {
        form.addEventListener('invalid', event => {
          const field = event.target;
          field.setAttribute('aria-invalid', 'true');
          const label = field.getAttribute('aria-label') || field.closest('label')?.childNodes?.[0]?.textContent?.trim() || 'Trường dữ liệu';
          toast(`${label}: ${field.validationMessage || 'Vui lòng kiểm tra dữ liệu.'}`, 'error');
        }, true);
      }

      controls.forEach(field => {
        const clearError = () => {
          if (field.matches('[data-integer-stock]')) validateIntegerStock(field);
          if (field.checkValidity()) field.removeAttribute('aria-invalid');
          else field.setAttribute('aria-invalid', 'true');
          if (feedback && form.checkValidity()) feedback.textContent = '';
        };
        field.addEventListener('input', clearError);
        field.addEventListener('change', clearError);
      });

      form.addEventListener('submit', event => {
        controls.filter(field => field.matches('[data-integer-stock]')).forEach(validateIntegerStock);
        if (!form.checkValidity()) {
          event.preventDefault();
          const invalid = controls.find(field => !field.checkValidity());
          if (invalid) {
            invalid.setAttribute('aria-invalid', 'true');
            invalid.focus();
            const label = invalid.getAttribute('aria-label') || invalid.closest('label')?.childNodes?.[0]?.textContent?.trim() || 'Trường dữ liệu';
            const message = `${label}: ${invalid.validationMessage || 'Vui lòng kiểm tra dữ liệu.'}`;
            if (feedback) feedback.textContent = message;
            if (form.noValidate) toast(message, 'error');
          }
          return;
        }
        const submit = event.submitter;
        if (submit && !submit.disabled) {
          submit.disabled = true;
          submit.dataset.originalText = submit.textContent;
          submit.textContent = 'Đang lưu…';
        }
      });
    });
  });
})();
