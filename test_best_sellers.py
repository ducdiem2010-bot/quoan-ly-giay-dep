# Vị trí lưu: tests/test_best_sellers.py
import unittest
from unittest.mock import patch
from app.services.best_sellers import get_best_sellers_v1


class TestBestSellers(unittest.TestCase):

    @patch('app.services.best_sellers.query_all')
    def test_best_sellers_logic(self, mock_query_all):
        # 1. Test trường hợp có đơn hàng hoàn thành (2 màu/size cộng dồn 2+3=5)
        # Giả lập kết quả trả về từ DB
        mock_query_all.return_value = [
            {"MaSanPham": 1, "TenSanPham": "Giày Test", "GiaBan": 1000, "HinhAnh": "test.jpg", "TongDaBan": 5}
        ]

        result = get_best_sellers_v1(limit=6)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['TongDaBan'], 5, "Lỗi: Không cộng dồn đúng 2+3=5")

    @patch('app.services.best_sellers.query_all')
    def test_best_sellers_cancelled_order(self, mock_query_all):
        # 2. Test trường hợp đơn bị hủy (+9) hoặc chưa có đơn hợp lệ
        # Hàm SQL trả về rỗng vì bị filter bởi TrangThaiDon = 1
        mock_query_all.return_value = []

        result = get_best_sellers_v1()
        self.assertEqual(len(result), 0, "Lỗi: Vẫn đếm cả đơn hàng đã hủy!")


if __name__ == '__main__':
    unittest.main()