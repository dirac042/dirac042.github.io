#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
updateblog.py — Obsidian 노트 → Hugo 블로그 동기화 & 배포 (macOS / Windows 공용)

예전 updateblog.sh + images.py 를 하나로 합친 것입니다. 파이썬 3 표준 라이브러리만 사용하며
rsync 가 필요 없습니다. Obsidian 이미지 임베드([[img.png]])는 마크다운 이미지로, 노트 간 링크([[노트]])는
공개된 글이면 블로그 링크로, 아니면 글자만 남도록 변환합니다.

    python updateblog.py              동기화 → 이미지 처리 → hugo 빌드 검사 → test 브랜치 커밋 → (선택) master merge + push
    python updateblog.py --serve      동기화 → 이미지 처리 → hugo server --disableFastRender -D  (git 단계 없음)
    python updateblog.py --dry-run    무엇이 바뀔지만 보여주고 아무것도 쓰지 않음
    python updateblog.py --no-build   hugo 빌드 검사 생략
    python updateblog.py --posts <폴더> --images <폴더>   이번 실행에만 경로 지정

경로 우선순위:  --posts/--images  >  환경변수 BLOG_POSTS_DIR / BLOG_IMAGES_DIR
                >  updateblog.local.json (이 PC 전용, git 에는 올라가지 않음)  >  아래 PROFILES 기본값
처음 실행할 때 경로가 없으면 물어보고 updateblog.local.json 에 저장해 둡니다.
"""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────────────────────────────────────
PROFILES = {
    # macOS — 예전 스크립트와 같은 위치
    "Darwin": {
        "posts": "/Users/dirac042/Documents/dirac042/POSTS",
        "images": "/Users/dirac042/Documents/dirac042/Images",
    },
    # Windows — 아직 미정: 실제 Obsidian 폴더로 고치거나, 첫 실행 때 물어보는 값을 그대로 저장하세요.
    "Windows": {
        "posts": r"C:\Users\Selfm\Documents\dirac042\POSTS",
        "images": r"C:\Users\Selfm\Documents\dirac042\Images",
    },
    # Linux / WSL 등
    "Linux": {
        "posts": os.path.expanduser("~/Documents/dirac042/POSTS"),
        "images": os.path.expanduser("~/Documents/dirac042/Images"),
    },
}

REPO_URL = "https://github.com/dirac042/dirac042.github.io.git"
MAIN_BRANCH = "master"
LOCAL_CONFIG = "updateblog.local.json"          # 이 PC 전용 경로 저장 파일 (.gitignore 에 포함)
IMAGE_EXTS = ("png", "jpg", "jpeg", "gif", "webp", "svg")

ROOT = Path(__file__).resolve().parent            # 블로그 저장소 루트 (이 파일이 있는 곳)
CONTENT_POSTS = ROOT / "content" / "posts"
STATIC_IMAGES = ROOT / "static" / "images"

# Obsidian 임베드:  [[img.png]]  ![[img.png]]  [[img.png|300]]  ![[dir/img.jpg|caption]]
EMBED_RE = re.compile(
    r"!?\[\[([^\]|]*\.(?:" + "|".join(IMAGE_EXTS) + r"))(?:\|[^\]]*)?\]\]", re.IGNORECASE
)
# 이미 변환된 마크다운 이미지 링크:  ![...](/images/파일%20이름.png)
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(/images/([^)\s]+)\)")
# 노트 간 위키링크:  [[노트 이름]]  [[노트 이름|표시 글자]]  [[노트 이름#섹션]]
NOTE_LINK_RE = re.compile(r"(?<!!)\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\]")
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


def hugo_urlize(name: str) -> str:
    """Hugo 가 파일 이름으로 URL 조각을 만드는 규칙의 근사치 (소문자, 공백→'-', 특수문자 제거)."""
    s = re.sub(r"\s+", "-", name.strip().lower())
    return re.sub(r"[^\w.\-~+@#/]", "", s)


def note_index(posts_dir: Path):
    """POSTS 안의 노트 → {이름: (url, draft)}. slug 프런트매터가 있으면 그것을, 없으면 파일 이름을 URL 로 씁니다."""
    idx = {}
    for md in posts_dir.rglob("*.md"):
        text = md.read_text("utf-8")
        slug, draft = None, False
        m = FRONT_MATTER_RE.match(text)
        if m:
            fm = m.group(1)
            ms = re.search(r"^slug:\s*['\"]?([^'\"\n]+)['\"]?\s*$", fm, re.M)
            if ms:
                slug = ms.group(1).strip()
            md_ = re.search(r"^draft:\s*(true|false)\s*$", fm, re.M | re.I)
            draft = bool(md_ and md_.group(1).lower() == "true")
        idx[md.stem] = (f"/posts/{slug or hugo_urlize(md.stem)}/", draft)
    return idx


# ──────────────────────────────────────────────────────────────────────────────
# 출력 도우미
# ──────────────────────────────────────────────────────────────────────────────
def say(msg=""):
    print(msg, flush=True)


def step(title):
    say()
    say(f"── {title} " + "─" * max(4, 60 - len(title)))


def die(msg, code=1):
    say(f"\n✖ {msg}")
    sys.exit(code)


def run(cmd, check=True, capture=False, cwd=None):
    """서브프로세스 실행 (문자열이 아니라 리스트로 전달)."""
    return subprocess.run(
        cmd, cwd=cwd or ROOT, check=check, text=True, encoding="utf-8", errors="replace",
        capture_output=capture,
    )


def ask(prompt, default=None):
    suffix = f" [{default}]" if default else ""
    try:
        v = input(f"{prompt}{suffix}: ").strip()
    except EOFError:
        v = ""
    return v or (default or "")


def yes(prompt):
    return ask(prompt + " (y/N)", "N").lower() in ("y", "yes")


# ──────────────────────────────────────────────────────────────────────────────
# 경로 설정 읽기 / 저장
# ──────────────────────────────────────────────────────────────────────────────
def load_paths(args):
    system = platform.system()
    prof = dict(PROFILES.get(system, PROFILES["Linux"]))

    local_file = ROOT / LOCAL_CONFIG
    if local_file.exists():
        try:
            prof.update({k: v for k, v in json.loads(local_file.read_text("utf-8")).items() if v})
        except Exception as e:  # noqa
            say(f"! {LOCAL_CONFIG} 을 읽지 못했습니다 ({e}). 기본값을 사용합니다.")

    if os.environ.get("BLOG_POSTS_DIR"):
        prof["posts"] = os.environ["BLOG_POSTS_DIR"]
    if os.environ.get("BLOG_IMAGES_DIR"):
        prof["images"] = os.environ["BLOG_IMAGES_DIR"]
    if args.posts:
        prof["posts"] = args.posts
    if args.images:
        prof["images"] = args.images

    posts = Path(os.path.expanduser(prof["posts"]))
    images = Path(os.path.expanduser(prof["images"]))

    changed = False
    if not posts.is_dir():
        say(f"! Obsidian 글 폴더가 없습니다: {posts}")
        if args.dry_run or not sys.stdin.isatty():
            die("경로를 --posts 로 지정하거나 updateblog.local.json / PROFILES 를 고쳐 주세요.")
        while True:
            p = ask("Obsidian 에서 블로그 글을 모아 두는 폴더 경로를 입력하세요")
            if p and Path(os.path.expanduser(p)).is_dir():
                posts = Path(os.path.expanduser(p)); changed = True; break
            say("  그런 폴더가 없습니다. 다시 입력해 주세요 (Ctrl+C 로 중단).")
    if not images.is_dir():
        say(f"! Obsidian 이미지(첨부) 폴더가 없습니다: {images}")
        if args.dry_run or not sys.stdin.isatty():
            die("경로를 --images 로 지정하거나 updateblog.local.json / PROFILES 를 고쳐 주세요.")
        while True:
            p = ask("Obsidian 첨부 이미지 폴더 경로를 입력하세요")
            if p and Path(os.path.expanduser(p)).is_dir():
                images = Path(os.path.expanduser(p)); changed = True; break
            say("  그런 폴더가 없습니다. 다시 입력해 주세요 (Ctrl+C 로 중단).")

    if changed and yes(f"이 경로를 {LOCAL_CONFIG} 에 저장해 다음부터 자동으로 쓸까요?"):
        local_file.write_text(json.dumps({"posts": str(posts), "images": str(images)}, ensure_ascii=False, indent=2), "utf-8")
        say(f"  저장했습니다 → {local_file}")

    return posts, images


# ──────────────────────────────────────────────────────────────────────────────
# 1) 동기화 (rsync -av --delete 와 같은 미러링)
# ──────────────────────────────────────────────────────────────────────────────
def same_file(a: Path, b: Path) -> bool:
    try:
        sa, sb = a.stat(), b.stat()
    except FileNotFoundError:
        return False
    return sa.st_size == sb.st_size and int(sa.st_mtime) == int(sb.st_mtime)


def sync_posts(src: Path, dst: Path, dry_run=False):
    step(f"동기화  {src}  →  {dst.relative_to(ROOT)}")
    dst.mkdir(parents=True, exist_ok=True)
    src_files = {p.relative_to(src) for p in src.rglob("*") if p.is_file() and not p.name.startswith(".")}
    dst_files = {p.relative_to(dst) for p in dst.rglob("*") if p.is_file() and not p.name.startswith(".")}

    copied, deleted = [], []
    for rel in sorted(src_files):
        s, d = src / rel, dst / rel
        if not same_file(s, d):
            copied.append(rel)
            if not dry_run:
                d.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(s, d)                       # 내용 + 수정시각 복사
    for rel in sorted(dst_files - src_files):
        deleted.append(rel)
        if not dry_run:
            (dst / rel).unlink()
    if not dry_run:  # 비어 버린 하위 폴더 정리
        for p in sorted([p for p in dst.rglob("*") if p.is_dir()], reverse=True):
            if not any(p.iterdir()):
                p.rmdir()

    for rel in copied:
        say(f"  + {rel}")
    for rel in deleted:
        say(f"  - {rel}   (Obsidian 에서 사라져 블로그에서도 삭제)")
    if not copied and not deleted:
        say("  변경 없음")
    return copied, deleted


# ──────────────────────────────────────────────────────────────────────────────
# 2) 이미지 링크 변환 + 이미지 복사  (예전 images.py)
# ──────────────────────────────────────────────────────────────────────────────
def find_image(name: str, images_dir: Path):
    """Obsidian 첨부 폴더(하위 폴더 포함)에서 파일 이름으로 찾기."""
    direct = images_dir / name
    if direct.is_file():
        return direct
    base = Path(name).name
    for p in images_dir.rglob(base):
        if p.is_file():
            return p
    return None


def process_images(posts_dir: Path, images_dir: Path, dry_run=False):
    step("이미지·노트 링크 변환 및 이미지 복사")
    STATIC_IMAGES.mkdir(parents=True, exist_ok=True)
    converted, copied, missing = 0, [], []
    notes = note_index(posts_dir)

    for md in sorted(posts_dir.rglob("*.md")):
        text = md.read_text("utf-8")
        needed = []

        def to_markdown(m):
            name = Path(m.group(1)).name                 # 하위 폴더 표기가 있어도 파일명만 사용
            needed.append(name)
            return f"![Image Description](/images/{name.replace(' ', '%20')})"

        new_text = EMBED_RE.sub(to_markdown, text)
        # 이미 마크다운 형식인 링크도 파일이 있는지 확인
        for m in MD_IMAGE_RE.finditer(new_text):
            needed.append(m.group(1).replace("%20", " "))

        # 노트 간 위키링크: 공개된 노트면 블로그 링크로, 아니면 글자만 남김
        links_changed = 0

        def to_link(m):
            nonlocal links_changed
            name = m.group(1).strip()
            label = (m.group(2) or name).strip()
            links_changed += 1
            hit = notes.get(name)
            if hit and not hit[1]:
                return f"[{label}]({hit[0]})"
            return label

        new_text = NOTE_LINK_RE.sub(to_link, new_text)

        if new_text != text:
            converted += len(needed)
            if not dry_run:
                md.write_text(new_text, "utf-8")
            n_embed = len(EMBED_RE.findall(text))
            parts = []
            if n_embed:
                parts.append(f"이미지 임베드 {n_embed}개")
            if links_changed:
                parts.append(f"노트 링크 {links_changed}개")
            say(f"  ✎ {md.relative_to(posts_dir)}: {', '.join(parts) or '변경'} 변환")

        for name in dict.fromkeys(needed):               # 중복 제거, 순서 유지
            dst = STATIC_IMAGES / name
            if dst.exists():
                continue
            src = find_image(name, images_dir)
            if src is None:
                missing.append((md.name, name))
                continue
            copied.append(name)
            if not dry_run:
                shutil.copy2(src, dst)

    for name in copied:
        say(f"  + static/images/{name}")
    for post, name in missing:
        say(f"  ! {post}: '{name}' 을(를) 첨부 폴더에서 찾지 못했습니다 (글에서는 깨진 이미지로 보입니다)")
    if not converted and not copied and not missing:
        say("  변경 없음")
    return missing


# ──────────────────────────────────────────────────────────────────────────────
# 3) Hugo
# ──────────────────────────────────────────────────────────────────────────────
def hugo_build():
    step("Hugo 빌드 검사 (public/ 은 .gitignore 되어 있음)")
    r = run(["hugo", "--gc", "--minify"], check=False, capture=True)
    if r.returncode != 0:
        say(r.stdout[-2000:])
        say(r.stderr[-2000:])
        die("Hugo 빌드가 실패했습니다. 위 오류를 고친 뒤 다시 실행하세요.")
    tail = [l for l in r.stdout.splitlines() if l.strip()][-1:]
    say("  OK  " + (tail[0].strip() if tail else ""))


def hugo_serve():
    step("Hugo 개발 서버  (Ctrl+C 로 종료)  http://localhost:1313")
    try:
        run(["hugo", "server", "--disableFastRender", "-D", "--navigateToChanged"], check=False)
    except KeyboardInterrupt:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# 4) git: test 브랜치 → 확인 → master merge + push  (예전 흐름 그대로)
# ──────────────────────────────────────────────────────────────────────────────
def git(*a, **kw):
    return run(["git", "-c", "core.quotepath=false", *a], **kw)


def git_flow():
    step("Git")
    if not (ROOT / ".git").exists():
        say("  git 저장소가 없어 초기화합니다.")
        git("init")
        git("remote", "add", "origin", REPO_URL)
    elif "origin" not in git("remote", capture=True).stdout.split():
        git("remote", "add", "origin", REPO_URL)

    status = git("status", "--short", capture=True).stdout.strip()
    if not status:
        say("  커밋할 변경 사항이 없습니다.")
        return
    say(status)
    say()

    msg = ask("커밋 메시지")
    if not msg:
        die("커밋 메시지가 비어 있어 중단합니다.")

    branch = "test-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    git("checkout", "-b", branch)
    git("add", "-A")
    git("commit", "-m", msg)
    say(f"\n✅ '{branch}' 브랜치에 커밋했습니다.")
    say("👉 hugo server 로 확인해 보거나, 바로 병합할 수 있습니다.")

    if yes(f"'{branch}' 를 '{MAIN_BRANCH}' 에 merge 하고 push 할까요?"):
        git("checkout", MAIN_BRANCH)
        git("merge", "--no-edit", branch)
        git("push", "origin", MAIN_BRANCH)
        git("branch", "-d", branch)
        say(f"✅ {MAIN_BRANCH} 에 병합하고 push 했습니다. GitHub Actions 가 곧 배포합니다.")
        say("   https://github.com/dirac042/dirac042.github.io/actions")
    else:
        say(f"❗ 병합하지 않았습니다. 지금 브랜치: '{branch}'  (나중에: git checkout {MAIN_BRANCH} && git merge {branch} && git push origin {MAIN_BRANCH})")


# ──────────────────────────────────────────────────────────────────────────────
def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="Obsidian → Hugo 블로그 동기화 & 배포")
    ap.add_argument("--posts", help="Obsidian 글 폴더")
    ap.add_argument("--images", help="Obsidian 첨부 이미지 폴더")
    ap.add_argument("--serve", action="store_true", help="동기화 후 hugo server 실행 (git 단계 생략)")
    ap.add_argument("--dry-run", action="store_true", help="바뀔 내용만 보여주고 아무것도 쓰지 않음")
    ap.add_argument("--no-build", action="store_true", help="hugo 빌드 검사 생략")
    ap.add_argument("--no-git", action="store_true", help="git 단계 생략")
    args = ap.parse_args()

    os.chdir(ROOT)
    for tool in ("git", "hugo"):
        if shutil.which(tool) is None:
            die(f"'{tool}' 을(를) 찾을 수 없습니다. 설치 후 PATH 에 추가해 주세요.")

    posts_dir, images_dir = load_paths(args)
    say(f"\n블로그 폴더 : {ROOT}\nObsidian 글 : {posts_dir}\nObsidian 이미지 : {images_dir}"
        + ("\n(dry-run: 실제로 쓰지 않습니다)" if args.dry_run else ""))

    sync_posts(posts_dir, CONTENT_POSTS, args.dry_run)
    process_images(CONTENT_POSTS, images_dir, args.dry_run)

    if args.dry_run:
        say("\n(dry-run 종료)")
        return
    if args.serve:
        hugo_serve()
        return
    if not args.no_build:
        hugo_build()
    if not args.no_git:
        git_flow()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        say("\n중단했습니다.")
        sys.exit(130)
    except subprocess.CalledProcessError as e:
        die(f"명령 실패: {' '.join(map(str, e.cmd))} (exit {e.returncode})")
