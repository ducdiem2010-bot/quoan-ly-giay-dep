"""W13 K7 — events chỉ xuất hiện nếu DB có timestamp."""
import unittest
from app.services.w13_order_timeline import build_timeline, get_timeline
from app.services.w13_reorder import OrderAccessError


class TimelineTests(unittest.TestCase):
    def row(self, status='Chờ xác nhận', **kw):
        data={'MaDonHang':20,'MaNguoiDung':7,'TrangThai':status,
              'TrangThaiGiaoHang':'Chưa giao',
              'NgayDat':'2026-11-17 02:30:00','ThoiGianXacNhan':None,
              'ThoiGianBatDauGiao':None,'ThoiGianGiaoThanhCong':None,
              'ThoiGianHoanThanh':None,'ThoiGianHuy':None}
        data.update(kw)
        return data
    def test_new_order_has_no_faked_milestones(self):
        r=build_timeline(self.row(),7)
        self.assertEqual([e['name'] for e in r['events']],['Đã đặt hàng'])
        self.assertTrue(r['has_unknown_times'])
    def test_confirmed_only_with_real_time(self):
        r=build_timeline(self.row('Đã xác nhận',ThoiGianXacNhan='2026-11-17 03:00:00'),7)
        self.assertEqual(len(r['events']),2)
    def test_shipping_without_history_is_not_faked(self):
        r=build_timeline(self.row('Đã xác nhận', TrangThaiGiaoHang='Đang giao'),7)
        self.assertEqual(len(r['events']),1)
        self.assertEqual(r['shipping_status'],'Đang giao')
    def test_completed_has_actual_timestamp(self):
        r=build_timeline(self.row('Hoàn thành',ThoiGianHoanThanh='2026-11-17 05:00:00'),7)
        self.assertEqual(r['events'][-1]['name'],'Hoàn thành')
    def test_completed_without_completion_time_is_not_faked(self):
        r=build_timeline(self.row('Hoàn thành'),7)
        self.assertEqual(len(r['events']),1)
        self.assertEqual(r['status'],'Hoàn thành')
    def test_cancelled_branch(self):
        r=build_timeline(self.row('Đã hủy',ThoiGianHuy='2026-11-17 03:10:00'),7)
        self.assertEqual(r['events'][-1]['name'],'Đã hủy')
        self.assertNotIn('Hoàn thành',[e['name'] for e in r['events']])
    def test_missing_cancel_time_is_explicit(self):
        r=build_timeline(self.row('Đã hủy'),7)
        self.assertIsNone(r['events'][-1]['timestamp'])
    def test_cannot_read_other_customer(self):
        with self.assertRaises(OrderAccessError): build_timeline(self.row(),8)
    def test_missing_order_404(self):
        with self.assertRaises(OrderAccessError) as e:
            get_timeline(99,7,lambda sql,params:None)
        self.assertEqual(e.exception.status_code,404)

if __name__=='__main__':unittest.main()
