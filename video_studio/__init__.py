"""video_studio — engine dựng video cho agent quanh HyperFrames, cài được như một package.

    video_studio._env      MỘT nơi quyết định trạm video, bản HyperFrames, node, ffmpeg, font
    video_studio.contract  hợp đồng gọi: mã thoát 0/1/2/3, một dòng JSON cuối stdout
    video_studio.station   `init` (dựng trạm, di trú trạm cũ, `--undo`)
    video_studio.doctor    kiểm máy + trạm, chỉ bước cài còn thiếu

`API_VERSION` là phiên bản HỢP ĐỒNG (semver) mà pipeline khác ghim tối thiểu — tách khỏi
phiên bản phát hành của repo. Đổi chữ ký lệnh/spec công khai ⇒ tăng số đầu.
"""

__version__ = "0.1.0"
API_VERSION = "1.0.0"

__all__ = ["API_VERSION", "__version__"]
