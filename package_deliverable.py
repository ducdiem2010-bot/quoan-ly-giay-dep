"""Đóng gói mã nguồn sạch, dùng đường dẫn tương đối, không xóa bản gốc.

Cách chạy: python package_deliverable.py [duong_dan_zip_dau_ra]
Lệnh này chạy test trên bản giải nén, không phụ thuộc vào thư mục code gốc.
"""
import os
import sys
import zipfile
import tempfile
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent
output = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else root.parent / 'Nhom6_Website_GiayDep_DaSua.zip'
output.parent.mkdir(parents=True, exist_ok=True)

exclude_dirs = {'.venv', 'venv', '.git', '__pycache__', 'instance', '.pytest_cache',
                '.mypy_cache', 'htmlcov', 'scratch', 'legacy', 'dist', '.gemini', '.vscode'}
exclude_suffixes = {'.pyc', '.pyo', '.pyd', '.sqlite', '.sqlite3', '.db', '.zip', '.log',
                    '.xlsx', '.xls', '.docx', '.pdf', '.csv'}
exclude_parts = {('docs', 'evidence'), ('docs', 'references')}
exclude_names = {'scratch_reproduce.py', 'check_hash.py', 'minh_smoke_result.txt'}
qa_terms = ('bug_log', 'buglog', 'test_case', 'test_plan', 'test_summary',
            'kiem_thu', 'minh_chung', 'smoke_result', 'w4_connection_verification',
            'ui_smoke_w4', 'tuan_ui_checklist', 'ket_qua_test')

included = []
with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for directory, dirs, files in os.walk(root):
        rel_dir = Path(directory).relative_to(root)
        dirs[:] = [d for d in dirs if d not in exclude_dirs
                   and (not d.startswith('.') or d == '.github')
                   and (str(rel_dir / d).replace('\\', '/').split('/')[:2] not in
                        [list(part) for part in exclude_parts])
                   and not (str(rel_dir).replace('\\','/') == 'docs' and d.upper().startswith('QA'))]
        for filename in files:
            rel = rel_dir / filename
            rel_str = rel.as_posix()
            if filename in exclude_names or filename == '.env' or (filename.startswith('.env.') and filename != '.env.example'):
                continue
            if filename.startswith('.') and filename not in ('.env.example', '.gitignore', '.dockerignore'):
                continue
            if rel.suffix.lower() in exclude_suffixes or any(term in rel_str.lower() for term in qa_terms):
                continue
            full = Path(directory) / filename
            archive.write(full, rel_str)
            included.append(rel_str)
print(f'Tạo ZIP: {output} ({len(included)} file, {output.stat().st_size:,} bytes)')

with tempfile.TemporaryDirectory(prefix='nhom6_zip_verify_') as work:
    with zipfile.ZipFile(output) as archive:
        archive.extractall(work)
    env = os.environ.copy()
    env['DB_BACKEND'] = 'sqlite'
    env['SECRET_KEY'] = 'test-only-unpacked-project-key'
    # Chỉ giữ đường dẫn thư viện Python ngoài ZIP nếu môi trường hiện tại cần;
    # không cho Python import mã nguồn app từ cây gốc thay vì thư mục giải nén.
    env['PYTHONPATH'] = os.pathsep.join(
        path for path in env.get('PYTHONPATH', '').split(os.pathsep)
        if path and Path(path).resolve() != root
    )
    result = subprocess.run([sys.executable, '-m', 'unittest', 'discover',
                             '-s', 'tests', '-p', 'test*.py'], cwd=work, env=env,
                            capture_output=True, text=True)
    tail = (result.stdout + '\n' + result.stderr).splitlines()[-12:]
    print('\n'.join(tail))
    if result.returncode:
        print('LỖI: Bộ test trên ZIP giải nén không thành công.', file=sys.stderr)
        sys.exit(result.returncode)
    print('PASS: Bộ kiểm thử chạy thành công từ ZIP giải nén.')
