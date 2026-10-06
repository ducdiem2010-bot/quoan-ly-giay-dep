from flask import Flask, session, request, jsonify

app = Flask(__name__)

# BẮT BUỘC: Cần có secret_key để Flask có thể sử dụng Session Cookie
app.secret_key = 'chuoi_bao_mat_bat_ky_cua_nghia' 

# 1. Hàm Hỗ Trợ: Route xem giỏ hàng hiện tại trong Session
@app.route('/cart', methods=['GET'])
def view_cart():
    # Lấy giỏ hàng từ session. Nếu session chưa có 'cart', trả về một dict rỗng {}
    cart = session.get('cart', {})
    
    # Tính tổng số lượng và tổng tiền (tùy chọn thêm để logic hoàn thiện)
    total_quantity = sum(item['quantity'] for item in cart.values())
    total_price = sum(item['price'] * item['quantity'] for item in cart.values())

    return jsonify({
        'cart_data': cart,
        'total_quantity': total_quantity,
        'total_price': total_price
    })

# 2. Hàm Chính: Route thêm sản phẩm vào giỏ hàng (sử dụng Session)
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    # Giả lập nhận dữ liệu ID, tên, giá, số lượng từ frontend gửi lên (qua Form hoặc Ajax)
    product_id = request.form.get('product_id')
    product_name = request.form.get('product_name')
    # Xử lý an toàn dữ liệu đầu vào
    product_price = float(request.form.get('product_price', 0))
    quantity = int(request.form.get('quantity', 1))

    # Nếu người dùng chưa có giỏ hàng trong session, tạo mới một dictionary rỗng
    if 'cart' not in session:
        session['cart'] = {}

    # Lấy giỏ hàng hiện tại ra biến để xử lý
    cart = session['cart']

    # Nếu sản phẩm đã tồn tại trong giỏ -> cộng dồn số lượng
    if product_id in cart:
        cart[product_id]['quantity'] += quantity
    # Nếu sản phẩm chưa có trong giỏ -> thêm mới vào từ điển
    else:
        cart[product_id] = {
            'name': product_name,
            'price': product_price,
            'quantity': quantity
        }

    # Cập nhật lại giỏ hàng vào session
    session['cart'] = cart
    # Báo cho Flask biết session đã bị thay đổi (để lưu dữ liệu vào cookie)
    session.modified = True 

    return jsonify({
        'status': 'success',
        'message': f'Đã thêm {product_name} vào giỏ hàng!',
        'cart': session['cart']
    })

# (Tùy chọn) Hàm xóa giỏ hàng để dễ test
@app.route('/cart/clear', methods=['POST'])
def clear_cart():
    session.pop('cart', None) # Xóa key 'cart' khỏi session
    return jsonify({'status': 'success', 'message': 'Đã xóa toàn bộ giỏ hàng'})

if __name__ == '__main__':
    app.run(debug=True)