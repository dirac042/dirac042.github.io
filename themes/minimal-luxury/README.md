# Minimal Luxury — Hugo theme for dirac042.github.io

`design-pick` 스킬의 **web-minimal-luxury** 팩(패션 하우스풍 절제된 럭셔리)을 그대로 옮긴 Hugo 테마입니다.
Sass·npm 등 빌드 도구 없이 순수 CSS/JS 하나씩으로만 이루어져 있어 Hugo(extended 여부 무관, 0.134+)만 있으면 됩니다.

## 디자인 규칙 (요약)

| 항목 | 값 |
| --- | --- |
| 배경 / 먹 / 헤어라인 | `#f4f1ea` / `#1a1a18` / `#c9c4b8` — 그 외 색·강조색 없음 |
| 서체 | Jost(라틴, Google Fonts) + Pretendard Variable(한글, jsDelivr) — 단일 위계, weight 300 본문 |
| 타이포 | 헤드라인 `clamp(1.5rem,3.2vw,2.6rem)` / 자간 0.22em / 대문자, 라벨 0.7rem·0.32em, 캡션 0.65rem·0.28em |
| 형태 | radius 0, 그림자 없음, 그라디언트 없음, 1px 헤어라인만 |
| 모션 | `600ms cubic-bezier(.22,1,.36,1)`, 스크롤 진입 opacity/translateY(16px) 700ms, 링크 밑줄 좌→우 400ms |

## 폴더

```
themes/minimal-luxury/
├─ assets/css/main.css        모든 스타일 (디자인 토큰은 :root 변수)
├─ assets/js/main.js          모바일 메뉴 · 스크롤 리빌 · 코드 복사 버튼
├─ layouts/
│  ├─ index.html              홈: 히어로 → 최근 글 → 먹빛 스테이트먼트 → 토픽
│  ├─ posts/single.html       글 페이지 (메타·본문·이전/다음)
│  ├─ _default/list.html      Journal 목록 · 태그 목록 · 태그별 목록
│  ├─ _default/single.html    일반 페이지 (About 등)
│  ├─ _default/_markup/       렌더 훅: 수식(passthrough) · 콜아웃(blockquote) · 이미지(figure) · 링크
│  └─ partials/               head · header · footer · entries · math · functions/sorted
└─ static/favicon.svg
```

## hugo.toml 에서 바꿀 수 있는 것

```toml
[params]
  wordmark   = "dirac042"                     # 헤더/푸터 워드마크
  tagline    = "Cozy Place to Learn Anything"
  dateFormat = "January 2, 2006"
  latestCount = 5                              # 홈에 보여줄 최근 글 수

  [params.hero]                                # 홈 히어로 (image 를 주면 풀블리드 사진 모드)
    label = "Journal — est. 2025"
    headline = "A cozy place to learn anything"
    caption = "…"
    # image = "images/hero.jpg"

  [params.statement]                           # 먹빛 밴드 (text 비우면 숨김)
    label = "…"  text = "…"  caption = "…"
    [params.statement.link]  text = "…"  url = "posts/…/"

  [params.math]
    always = false                             # true 면 모든 페이지에 MathJax 로드
    lib = "https://cdn.jsdelivr.net/npm/mathjax@4/tex-chtml.js"
```

## 글 프런트매터

```yaml
title: 제목
date: 2025-07-16
draft: false
tags: [Blog, Coding]
subtitle: 부제 (선택)
toc: true        # 선택 — 본문 위에 목차 박스
math: false      # 선택 — 이 페이지에서 MathJax 강제 끄기/켜기 (기본은 수식 감지 시 자동)
```

- 수식: `$...$`, `$$...$$`, `\(...\)`, `\[...\]` 모두 지원. 수식이 있는 페이지에만 MathJax v4 가 로드되며 긴 수식은 자동 줄바꿈됩니다.
- Obsidian 콜아웃 `> [!note] 제목` / `> [!warning] 제목` 은 헤어라인 박스로 렌더됩니다.
- 이미지 바로 아래 줄에 `> 캡션` 을 쓰면 캡션으로 표시됩니다 (기존 글쓰기 습관 그대로).
- 코드 블록에는 마우스를 올리면 COPY 버튼이 나타납니다.

## 로컬 미리보기

```sh
hugo server            # http://localhost:1313
hugo --gc --minify     # public/ 생성 (GitHub Actions 가 push 시 자동으로 수행)
```
