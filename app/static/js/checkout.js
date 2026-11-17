(() => {
  const delivery = document.getElementById('delivery-fields');
  const address = document.getElementById('address');
  const ship = document.getElementById('shipping-summary');
  const explain = document.getElementById('payment-explain');
  if (!delivery || !address || !ship || !explain) return;
  function refresh() {
    const fulfillment = document.querySelector('input[name="fulfillment"]:checked')?.value || 'delivery';
    const payment = document.querySelector('input[name="payment_method"]:checked')?.value || 'cod';
    const isDelivery = fulfillment === 'delivery';
    delivery.hidden = !isDelivery;
    address.required = isDelivery;
    ship.textContent = isDelivery ? 'Chờ xác nhận' : '0 ₫';
    explain.textContent = payment === 'bank_transfer'
      ? 'Chỉ tạo đơn chờ xác nhận chuyển khoản. Chưa có thông tin nhận tiền và không ghi nhận đã thanh toán.'
      : (isDelivery ? 'Bạn thanh toán khi nhận hàng; cửa hàng sẽ xác nhận phí giao.' : 'Bạn thanh toán khi đến nhận hàng tại cửa hàng.');
  }
  document.querySelectorAll('input[name="fulfillment"], input[name="payment_method"]').forEach(el => el.addEventListener('change', refresh));
  refresh();
})();
