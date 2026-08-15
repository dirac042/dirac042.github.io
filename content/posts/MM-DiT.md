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

[이전 노트](/posts/dit/)에서 남긴 찝찝함 — 이미지/오디오가 주(主), 텍스트가 부(副)인 구조 — 을 정면으로 다루는 MM-DiT 정리. Stable Diffusion 3 논문(Esser et al., [*Scaling Rectified Flow Transformers for High-Resolution Image Synthesis*](https://arxiv.org/abs/2403.03206), 2024)에서 제안됐다.

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

![Image Description](/images/fig-mmdit-block.png)
> 한 블록의 흐름. 두 트랙은 가중치(adaLN, QKV, MLP)를 따로 갖고, attention 한 번만 같은 방에서 한다.

> [!note] SD3에서는 실제로 어떻게 조건을 만드나
> 텍스트 인코더를 세 개 쓴다: CLIP L/14, OpenCLIP bigG/14, T5-XXL. CLIP 두 개의 **pooled 출력**을 이어 붙여 하나의 벡터로 만들고, 여기에 timestep 임베딩을 더해 adaLN의 조건 벡터(위 그림의 "t + pooled text")로 쓴다. 반면 **토큰 단위 임베딩**(CLIP의 penultimate hidden state + T5 토큰)은 Track B의 시퀀스가 되어 joint attention에 들어간다. 즉 "문장의 요약"은 modulation으로, "문장의 단어 하나하나"는 attention으로 들어가는 셈이다.
>
> 그리고 이게 정말 나은지도 재봤다. 같은 조건에서 vanilla DiT < UViT < cross-attention DiT(CrossDiT) < **MM-DiT** 순서였고, 논문은 "MM-DiT가 cross-attention과 vanilla 변형을 크게 앞선다"고 쓴다. 학습 목표는 DDPM 대신 rectified flow이고, 중간 timestep을 더 자주 뽑는 logit-normal 샘플링을 쓴다. 깊이 38(약 8B 파라미터)까지 키워도 validation loss가 포화 없이 계속 내려갔다.

## Problems

뭔가 데이터가 엄청나게 커지게 되면, Joint Attention이 엄청나게 느려질 것 같은 예감.

1. Transformer Attention 연산은 $\mathcal{O}(N^2)$, 즉 데이터 길이의 제곱에 비례해 계산량이 늘어난다.
	* 기존 방식은 Noise Token이 Text를 참고만 하니까, $\mathcal{O}(N^2)$.
	* MM-DiT는 전부 다 몰아넣고 Attention을 실행하니까, $\mathcal{O}((N_{text}+N_{image})^2)$
	* 계산량이 매우매우 커진다.
2. Attention 계산에서 OOM 에러
3. Modality Imbalance하면 효율이 떨어진다.
	ex. 텍스트 100개, 이미지 4만 개 → 이미지-이미지 간의 상호작용만 여러 개.

> [!note] 숫자로 감 잡기
> 1024×1024 이미지를 8배 VAE로 줄이면 128×128 latent, 패치 2로 자르면 $64^2=4096$ 토큰. 텍스트는 CLIP 77 + T5 256 정도로 수백 개. 그러면 $(4096+333)^2\approx1.96\times10^7$ 대 $4096^2\approx1.68\times10^7$ — 텍스트를 같은 방에 넣어서 늘어나는 비용은 약 17%다. 걱정과 달리 병목은 "텍스트를 끼워서"가 아니라 애초에 이미지-이미지 attention이고, 이건 self-attention을 쓰는 이상 어떤 DiT든 똑같이 진다. 오디오는 토큰이 시간축으로 길어지기 쉬워서(수천~수만 프레임) 이 항이 더 아프다.

아직까지도 안 풀린 숙제로 남아 있다.
1. Flash Attention 같은 최적화 기술을 영끌해서 적용하거나,
2. 3개의 블럭에서만 Joint Attention하고, 나머지는 분리해서 연산하는 등…

> [!note] 실제로 나온 절충안들
> * FLUX.1(Black Forest Labs, 2024)은 앞쪽에 두 트랙이 분리된 MM-DiT식 **double-stream** 블록을 두고, 뒤쪽은 두 시퀀스를 아예 하나로 합쳐 처리하는 **single-stream** 블록으로 바꿔 파라미터를 아낀다 — 위 2번 아이디어와 같은 방향이다.
> * 오디오 쪽에서는 MMAudio(Cheng et al., 2024)가 비디오·텍스트·오디오 세 스트림을 joint attention으로 묶고, 비디오-오디오 프레임을 시간축에 맞춰 정렬한 위치 임베딩(aligned RoPE)을 얹어 동기화 문제를 푼다.
> * 계산량 자체는 FlashAttention 계열이 메모리 병목을 크게 완화하지만 $\mathcal{O}(N^2)$ 자체가 사라지진 않는다. 그래서 latent를 더 압축하거나(패치 크기, VAE 다운샘플 비율), 윈도우/희소 attention을 섞는 연구가 이어진다.

## 참고 자료

- P. Esser et al., [*Scaling Rectified Flow Transformers for High-Resolution Image Synthesis*](https://arxiv.org/abs/2403.03206), 2024 — MM-DiT 원 논문(Stable Diffusion 3).
- W. Peebles, S. Xie, [*Scalable Diffusion Models with Transformers*](https://arxiv.org/abs/2212.09748), ICCV 2023 — 출발점인 DiT.
- H. K. Cheng et al., [*MMAudio: Taming Multimodal Joint Training for High-Quality Video-to-Audio Synthesis*](https://arxiv.org/abs/2412.15322), 2024 — 오디오에서의 multimodal joint attention.
- [black-forest-labs/flux](https://github.com/black-forest-labs/flux) — double/single-stream 블록 구현.
