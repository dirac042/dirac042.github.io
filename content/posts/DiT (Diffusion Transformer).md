---
title: DiT (Diffusion Transformer) 정리
slug: dit
date: 2026-07-06T10:20:00+09:00
draft: false
tags:
  - Deep Learning
  - Diffusion
  - Paper Notes
---

Diffusion의 백본을 U-Net에서 Transformer로 바꾼 DiT를, 오디오 생성 관점에서 읽고 정리한 노트.

이전에 사용하던 U-Net 기반의 Diffusion은 이미지 생성 Task에서 많이 활용되어 왔다.
* 하지만, U-Net의 구조적인 한계 때문에, 시간 간격이 긴 데이터에 약하다.
* 즉, 앞의 데이터와 뒤의 데이터를 서로 연결할 수 있는 힘이 없다.

그래서 Transformer의 Attention 구조가 가진 Long-Term Dependency를 이용해 Transformer 기반의 Diffusion Method를 고안하게 되는데, 이것이 DiT라고 볼 수 있겠다.

## Architecture

결국 Diffusion이 메인이라, Gaussian Noise에서 GT로 가는 방향을 예측하는 건 동일하다.

즉, DiT의 Block은 현재 Timestep에서 입력된 Noisy Latent를 어떤 방향으로 Denoise할 것인지를 구하는 게 목표다.

1. AdaLN (Adaptive Layer Normalization)
	* 먼저 시간 $t$를 주입받아, 각각의 토큰들에게 '얼마나 깎아야 하는지'를 전달한다.
2. Self-Attention
	* 1에서 나온 정보들을 바탕으로, 각 토큰들은 자기 자신(Waveform) 안에서 패턴을 분석한다.
3. Cross-Attention
	* 이때 외부의 Condition(Video/Text)이 들어와 Denoising을 위한 힌트를 제공하고, 소리 생성의 방향성이 생긴다.
4. MLP
	* 최종적으로 "이 소리는 이 방향으로 이동해야 한다!"를 구하게 된다.

## Commentary

찝찝한 부분이 있다.

현재 DiT에서는 Self-Attention에서 Waveform의 패턴을 분석한 다음,
부가적으로 Condition이 들어와 Denoising을 시행한다.

그 말인즉슨, Waveform이 주(主), Video/Text가 부(副)가 되는 형태라고 볼 수 있겠다.

이런 식으로 이미지/오디오가 메인, 텍스트가 보조가 되면 정보 불균형이 생기지 않을까?

이걸 Hierarchical하지 않고, Equal하게 다룰 수는 없을까?

→ 다음 노트: [MM-DiT](/posts/mm-dit/)
