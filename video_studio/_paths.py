"""_paths.py — một luật duy nhất cho TÊN FILE RA, chạy y hệt nhau trên mọi hệ điều hành.

Ba lệnh đặt tên file ra (`templates/news`, `spec.outputs`, `edit --name`) đều nhận chuỗi từ
bên ngoài: spec do pipeline sinh, cờ do người gõ. Nếu chuỗi ấy hoá ra là một ĐƯỜNG DẪN thì
`os.path.join(out_dir, …)` **không báo lỗi** — nó lặng lẽ đẻ thư mục con, hoặc nhảy hẳn sang
chỗ khác — và bên gọi đi tìm ở đúng `--out` mình khai thì không thấy gì.

**Vì sao không hỏi `os`.** Bản vá đầu tiên viết `if os.sep in s or (os.altsep and …)`. Trên
POSIX `os.sep == "/"` và `os.altsep is None`, nên **nhánh dấu `\\` không bao giờ chạy**:
`18\\09\\2026` và `C:\\out\\x` lọt sạch trên macOS/Linux, dù chính test của cổng đòi phải
chặn. Luật ở đây **không hỏi hệ điều hành đang chạy là gì**: nó kiểm mặt chữ, và hỏi `ntpath`
**cùng** `posixpath` một lượt. Chỉ `join_out` mới dùng `os.path` — đúng chỗ phải dùng, vì
chốt hậu bằng `realpath` là phép đo trên ĐĨA THẬT của máy đang chạy.

**`C:foo.mp4` — cái bẫy không có dấu ngăn.** Dạng "ổ đĩa, không dấu ngăn" có
`ntpath.isabs` là `False` và không chứa `/` lẫn `\\`, nên lọt mọi phép kiểm hiển nhiên. Nhưng
`ntpath.join("D:\\deliver", "C:foo.mp4")` trả về `'C:foo.mp4'`: `--out` **biến mất không một
tiếng động**, file rơi vào thư mục hiện hành của ổ `C:`. Nên `splitdrive` là một phép kiểm
riêng, không phải phần thừa của phép kiểm dấu ngăn.
"""
import ntpath
import os
import posixpath

from .contract import ContractError

__all__ = ["plain_name", "join_out"]

#: Ký tự điều khiển: `\x00` cắt tên ở tầng C, phần còn lại không bao giờ là tên file thật.
_CONTROL = frozenset(chr(c) for c in range(0x20)) | {"\x7f"}


def _why_not_a_name(s):
    """-> lý do (tiếng Việt) chuỗi `s` KHÔNG phải một mảnh tên file, hoặc `None` nếu nó là.

    Thứ tự các phép kiểm chọn theo *độ rõ của thông điệp*, không theo độ chặt: người đọc lỗi
    cần biết mình sai ở đâu, nên "có dấu ngăn" đi trước "là đường tuyệt đối".
    """
    if not s.strip():
        return "rỗng"
    if any(ch in _CONTROL for ch in s):
        return "chứa ký tự điều khiển"
    if "/" in s or "\\" in s:
        return "có dấu ngăn thư mục"
    if ntpath.splitdrive(s)[0] or posixpath.splitdrive(s)[0]:
        return "mang tên ổ đĩa (dạng \"C:ten.mp4\" không có dấu ngăn vẫn nhảy sang ổ khác)"
    if ":" in s:
        return "có dấu hai chấm (trên Windows là luồng dữ liệu phụ của NTFS)"
    if ntpath.isabs(s) or posixpath.isabs(s):
        return "là đường tuyệt đối"
    if s.strip() in (".", ".."):
        return "là một thư mục, không phải tên file"
    return None


def plain_name(value, field, hint=""):
    """Kiểm `value` là một mảnh TÊN FILE. -> chính chuỗi đó; sai ⇒ `ContractError` (mã 2).

    `field` là tên trường để người đọc biết sửa ở đâu (`"date"`, `"outputs.long"`, `"--name"`).
    """
    s = str(value)
    why = _why_not_a_name(s)
    if why:
        msg = (f"\"{field}\" = {s!r} {why} nên sẽ ghi file RA NGOÀI --out. "
               "Cần một TÊN FILE trần: không thư mục, không ổ đĩa.")
        raise ContractError(msg + (" " + hint if hint else ""))
    return s


def join_out(out_dir, value, field, hint=""):
    """`plain_name` rồi ghép vào `out_dir`, **chốt hậu** bằng `realpath`. -> đường dẫn đầy đủ.

    Chốt hậu là lớp thứ hai có chủ đích: phép kiểm mặt chữ ở trên nói "chuỗi này không giống
    đường dẫn", còn `realpath` nói "và kết quả thật sự nằm trong `--out`" — kể cả khi hệ tệp
    có liên kết mềm, tên 8.3, hay một dạng nào đó chưa ai nghĩ ra.
    """
    name = plain_name(value, field, hint)
    joined = os.path.join(out_dir, name)
    root = os.path.realpath(out_dir)
    real = os.path.realpath(joined)
    if real == root or not real.startswith(root.rstrip(os.sep) + os.sep):
        raise ContractError(
            f"\"{field}\" = {name!r} ghép với --out ra {real!r}, nằm NGOÀI {root!r}.")
    return joined
