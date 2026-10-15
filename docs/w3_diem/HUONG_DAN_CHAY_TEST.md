# HƯỚNG DẪN THỰC THI KIỂM THỬ KỸ THUẬT VÀ NGHIỆM THU TUẦN 3
**Người thực hiện:** Điểm – Nhóm trưởng Nhóm 6
**Dự án:** Website Quản lý cửa hàng bán giày dép (Flask - SQL Server)

---

## 1. HƯỚNG DẪN MỞ DỰ ÁN TRÊN VS CODE VÀ TERMINAL

1. **Thư mục mở trong VS Code:**
   - Mở chính xác thư mục: `Nhom6_Tuan2_DaGhep`
   - Đường dẫn đầy đủ: `c:\Users\Admin\Downloads\Nhom6_WebGiayDep_Tuan2_DaGhep_NghiemThu (1)\Nhom6_Tuan2_DaGhep`
   *(Tuyệt đối không mở thư mục `app` ngoài cùng vì đó là thư mục phụ)*.

2. **Mở Terminal (PowerShell):**
   - Trong VS Code, bấm tổ hợp phím: `Ctrl + ~` (hoặc vào menu `Terminal` -> `New Terminal`).
   - Đảm bảo dấu nhắc lệnh hiển thị tại thư mục `Nhom6_Tuan2_DaGhep`:
     ```powershell
     PS C:\Users\Admin\Downloads\Nhom6_WebGiayDep_Tuan2_DaGhep_NghiemThu (1)\Nhom6_Tuan2_DaGhep>
     ```

3. **Kích hoạt môi trường ảo (Virtualenv) & Cài đặt thư viện:**
   ```powershell
   # Kích hoạt virtualenv ở thư mục ngoài nếu có:
   ..\.venv\Scripts\Activate.ps1

   # Cài đặt các gói phụ thuộc:
   pip install -r requirements.txt
   ```

---

## 2. CÁC LỆNH CHẠY BỘ TEST TỰ ĐỘNG

### 2.1. Chạy Smoke Test nền tảng Tuần 2 (10 bài test gốc)
```powershell
python -m unittest tests/test_smoke.py -v
```

### 2.2. Chạy từng bộ Test Tuần 3 độc lập (Do Điểm xây dựng)
- **W3-016 (SQL Server & Public Product):**
  ```powershell
  python -m unittest tests/w3_diem/test_w3_016_sql_public.py -v
  ```
- **W3-029 (12 Kịch bản kiểm thử chéo bắt buộc):**
  ```powershell
  python -m unittest tests/w3_diem/test_w3_029_cross.py -v
  ```
- **W3-030 (Chính sách ảnh và Yêu thích):**
  ```powershell
  python -m unittest tests/w3_diem/test_w3_030_image_favorite.py -v
  ```
- **W3-043 (Luồng E2E Khách hàng & Case SP101/SP102 cùng biến thể):**
  ```powershell
  python -m unittest tests/w3_diem/test_w3_043_customer_e2e.py -v
  ```
- **W3-044 (Bảo mật Admin, Phân quyền RBAC & Rollback Giao dịch):**
  ```powershell
  python -m unittest tests/w3_diem/test_w3_044_admin_security.py -v
  ```

### 2.3. Chạy toàn bộ tất cả các bài test (Tuần 2 + Tuần 3)
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 3. CÁC CÔNG CỤ KIỂM TOÁN VÀ NGHIỆM THU

### 3.1. [W3-001] Kiểm kê kỹ thuật và môi trường
Kiểm tra phiên bản Python, Flask, các file bắt buộc, cấu hình database không lộ pass và quét code demo cũ:
```powershell
python tools/w3_diem/check_environment.py
```

### 3.2. [W3-015] Kiểm toán đối chiếu hợp đồng API - SQL - ERD
Quét tham số URL, bảng/cột, ràng buộc giá > 0, phát hiện thiếu sót của Minh, Nghĩa, Khải:
```powershell
python tools/w3_diem/audit_contract.py
```

### 3.3. [W3-058] Bộ chạy kiểm thử hồi quy tự động (Regression Runner)
Chạy lại toàn bộ test, ghi commit hash và xuất báo cáo CSV/JSON:
```powershell
python tools/w3_diem/run_regression.py
```

### 3.4. [W3-059] Kiểm toán độ bao phủ 86 chức năng (Coverage Audit)
Đối chiếu ma trận chức năng, phát hiện tính năng chưa có code/test:
```powershell
python tools/w3_diem/audit_coverage.py
```

### 3.5. [W3-060] Kiểm tra độ sẵn sàng Demo & 5 máy
```powershell
python tools/w3_diem/check_demo_readiness.py
```

### 3.6. [W3-069] LỆNH TỔNG HỢP TOÀN BỘ NGHIỆM THU (KHUYÊN DÙNG)
Chạy toàn bộ 5 bước trên chỉ với 1 câu lệnh duy nhất:
```powershell
python tools/w3_diem/run_all_checks.py
```

---

## 4. VỊ TRÍ LƯU TRỮ MINH CHỨNG VÀ KẾT QUẢ

Mọi kết quả tự động xuất ra thư mục: `docs/w3_diem/`:
- `BAO_CAO_KIEM_KE_MOI_TRUONG.json`: Báo cáo chi tiết môi trường.
- `BIEN_BAN_DOI_CHIEU_HOP_DONG.md`: Báo cáo đối chiếu API/SQL và lỗi cần sửa.
- `KET_QUA_REGRESSION_LATEST.csv`: Bảng kết quả hồi quy theo commit.
- `BAO_CAO_BAO_PHU_CHUC_NANG.md`: Báo cáo độ bao phủ chức năng.
- `MA_TRAN_BAO_PHU_CHUC_NANG.csv`: Bảng ma trận bao phủ phục vụ báo cáo.
- `CHECKLIST_DEMO_5_MAY.md`: Danh mục chuẩn bị cho 5 máy thành viên.
- `DANH_SACH_BLOCKER.md`: Danh sách các rào cản kỹ thuật cần giải quyết.

---

## 5. Ý NGHĨA PHÂN LOẠI KẾT QUẢ
- **PASS**: Chức năng/Quy tắc đã có code và kiểm thử thành công 100%.
- **FAIL**: Đã chạy nhưng kết quả sai lệch so với quy tắc A01-A08 hoặc CSDL.
- **BLOCKED**: Tính năng chưa được các thành viên khác triển khai hoặc chưa cấu hình SQL Server thật. Được ghi nhận trung thực, KHÔNG che giấu.
- **NOT RUN**: Các trường hợp kiểm thử giao diện thủ công hoặc chưa tới lượt chạy.

---

## 6. DANH SÁCH BẰNG CHỨNG CẦN CHỤP ẢNH ĐỂ LÀM BÁO CÁO NỘP THẦY
1. Ảnh chụp Terminal chạy `python tools/w3_diem/run_all_checks.py` hiển thị Dashboard nghiệm thu.
2. Ảnh chụp Terminal chạy `python -m unittest tests/test_smoke.py -v` (10/10 PASS).
3. Ảnh chụp Terminal chạy `python tools/w3_diem/audit_contract.py` hiển thị bảng phân công lỗi cho Minh, Nghĩa, Khải.
4. Ảnh chụp màn hình trang chủ giao diện tại `http://localhost:5000`.
5. Ảnh chụp màn hình responsive tại kích thước 375px trên DevTools trình duyệt.
