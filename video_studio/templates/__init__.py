"""templates — các bộ khuôn dựng video đi kèm engine.

Mỗi gói con là MỘT họ template (hiện có: `news`). Gói con chỉ được import khi thật sự render:
chúng cần `numpy`, `soundfile` và repo giọng (`agent-voice-studio`, extras `[voice]`), còn
`video-studio --help`, `init`, `doctor` phải chạy được trên máy chưa cài gì trong số đó.
"""
