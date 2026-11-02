# Quy trình đưa bản ghép lên GitHub – chưa thực hiện push
1. Tạo branch mới từ `main` tại repo sạch, ví dụ `integration-w2-w3`.
2. Sao lưu mã nguồn cũ và kiểm tra `git status` trước khi sao chép bản ghép. Không copy `.git`, `.env`, `instance`, `.venv`.
3. Thêm các file ứng dụng, `database` migration, `tests`, docs từ ZIP; tránh ghi đè code tiến hành bởi thành viên khác sau ngày tạo ZIP.
4. `git diff --stat` và `git diff --check`; kiểm thử `python -m unittest discover -s tests`.
5. `git add app database tests run.py README.md requirements.txt .gitignore .env.example docs`.
6. `git commit -m "Integrate W2-W3 product catalog and admin prototype"`.
7. `git push -u origin integration-w2-w3`.
8. Trên GitHub mở PR vào main, Điểm review Files changed và bổ sung minh chứng SQL Server khi có.
9. Không merge nếu test SQL Server hoặc phân quyền còn FAIL/BLOCKED theo DoD.
