---
title: MM-DiT — 두 모달리티를 동등하게 다루는 Diffusion Transformer
slug: mm-dit
date: 2026-07-06T10:30:00+09:00
draft: false
tags:
  - Deep Learning
  - Diffusion
  - Paper Notes
---

[이전 노트](/posts/dit/)에서 남긴 찝찝함 — 이미지/오디오가 주(主), 텍스트가 부(副)인 구조 — 을 정면으로 다루는 MM-DiT 정리.

기존의 DiT 구조는 2가지의 모달리티에 계층이 존재했다.
1. 이미지, 오디오를 메인으로 두고,
2. 텍스트를 보조 힌트로 사용.

이렇게 되면 2개의 모달리티의 깊이가 달라서, Deeper Level의 Alignment가 잘 안 되는 문제가 생긴다.

그러나 MM-DiT는 2개의 모달리티를 완벽하게 동등한 비중으로 다루게 된다.

## Architecture

1. Stream을 2개로 쪼개자!
	* Track A: Noise Token이 지나가는 길 (이미지/오디오)
	* Track B: Text Token이 지나가는 길 (텍스트)
		* 이때 텍스트는 힌트로 쓰이고 버려지지 않고, 이미지랑 똑같이 블록을 통과할 때마다 스스로 update된다.
2. **Joint Attention**: 서로 다른 도로를 달리는 2개를 합치자!
	1. 이미지/텍스트는 성질이 달라서, 독립적인 Linear 신경망을 거쳐 QKV 제작
	2. 이미지 QKV와 텍스트 QKV를 Sequential하게 이어붙이기 (매우 큰 공간)
		→ 이 공간 안에서 토큰들이 서로 Attention (픽셀, 텍스트와의 관계 학습)
			"사람들 4000명을 앉혀놓고, 전부 떠들게 만들기"
	3. 정보를 가지게 된 토큰들을 다시 2개의 갈래로 나누기
	4. 분리된 토큰들이 독립적인 MLP를 거쳐 최종적인 결과를 내리고, 다음 블럭으로 넘어가기

## Problems

뭔가 데이터가 엄청나게 커지게 되면, Joint Attention이 엄청나게 느려질 것 같은 예감.

1. Transformer Attention 연산은 $\mathcal{O}(N^2)$, 즉 데이터 길이의 제곱에 비례해 계산량이 늘어난다.
	* 기존 방식은 Noise Token이 Text를 참고만 하니까, $\mathcal{O}(N^2)$.
	* MM-DiT는 전부 다 몰아넣고 Attention을 실행하니까, $\mathcal{O}((N_{text}+N_{image})^2)$
	* 계산량이 매우매우 커진다.
2. Attention 계산에서 OOM 에러
3. Modality Imbalance하면 효율이 떨어진다.
	ex. 텍스트 100개, 이미지 4만 개 → 이미지-이미지 간의 상호작용만 여러 개.

아직까지도 안 풀린 숙제로 남아 있다.
1. Flash Attention 같은 최적화 기술을 영끌해서 적용하거나,
2. 3개의 블럭에서만 Joint Attention하고, 나머지는 분리해서 연산하는 등…
