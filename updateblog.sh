#!/bin/bash
# updateblog.sh — 호환용 래퍼. 실제 작업은 updateblog.py (macOS / Windows 공용) 가 합니다.
#   ./updateblog.sh            동기화 → 이미지 → hugo 빌드 검사 → test 브랜치 커밋 → (선택) master merge + push
#   ./updateblog.sh --serve    동기화 후 hugo server --disableFastRender -D
#   ./updateblog.sh --dry-run  바뀔 내용만 보기
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1
exec python3 updateblog.py "$@"
