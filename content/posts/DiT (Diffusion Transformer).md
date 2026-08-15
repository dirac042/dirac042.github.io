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

Diffusion의 백본을 U-Net에서 Transformer로 바꾼 DiT(Peebles & Xie, [*Scalable Diffusion Models with Transformers*](https://arxiv.org/abs/2212.09748), ICCV 2023)를, 오디오 생성 관점에서 읽고 정리한 노트.

이전에 사용하던 U-Net 기반의 Diffusion은 이미지 생성 Task에서 많이 활용되어 왔다.
* 하지만, U-Net의 구조적인 한계 때문에, 시간 간격이 긴 데이터에 약하다.
* 즉, 앞의 데이터와 뒤의 데이터를 서로 연결할 수 있는 힘이 없다.

그래서 Transformer의 Attention 구조가 가진 Long-Term Dependency를 이용해 Transformer 기반의 Diffusion Method를 고안하게 되는데, 이것이 DiT라고 볼 수 있겠다.

> [!note] 논문이 실제로 내세운 주장은 조금 다르다
> 위 직관(긴 의존성)은 오디오 쪽에서 DiT를 좋아하는 이유로 맞는 말이지만, 원 논문의 핵심 메시지는 **"U-Net의 inductive bias는 필수가 아니고, Transformer로 바꾸면 계산량(Gflops)을 늘릴수록 성능이 착실히 좋아진다"** 는 스케일링 이야기다. 12개 모델 변형에서 Gflops와 FID-50K의 상관계수가 −0.93이었고, 가장 큰 DiT-XL/2(28층, hidden 1152, 16 heads)가 ImageNet 256×256 class-conditional에서 FID 2.27로 당시 SOTA를 찍었다. 입력은 픽셀이 아니라 Stable Diffusion VAE의 latent(256² 이미지 → 32×32×4)이고, ADM처럼 노이즈 ε과 공분산 Σ를 예측한다.

## Architecture

결국 Diffusion이 메인이라, Gaussian Noise에서 GT로 가는 방향을 예측하는 건 동일하다.

즉, DiT의 Block은 현재 Timestep에서 입력된 Noisy Latent를 어떤 방향으로 Denoise할 것인지를 구하는 게 목표다.

### Patchify: latent를 토큰으로

Transformer는 토큰의 시퀀스를 먹으니, 먼저 latent를 잘라야 한다. $I\times I$ latent를 $p\times p$ 패치로 자르면 토큰 수는 $T=(I/p)^2$. 논문은 $p\in\{2,4,8\}$을 실험했는데, $p$를 반으로 줄이면 토큰이 4배가 되고 Gflops도 최소 4배가 된다(파라미터 수는 거의 그대로). 그리고 그만큼 성능이 좋아진다 — 이것도 "계산량이 곧 성능"의 한 사례. 위치 정보는 ViT처럼 sine-cosine positional embedding으로 넣는다. 오디오라면 $I\times I$ 대신 (시간 × 주파수/채널) latent를 같은 식으로 자르면 된다.

### 블록 안에서 일어나는 일

1. AdaLN (Adaptive Layer Normalization)
	* 먼저 시간 $t$를 주입받아, 각각의 토큰들에게 '얼마나 깎아야 하는지'를 전달한다.
2. Self-Attention
	* 1에서 나온 정보들을 바탕으로, 각 토큰들은 자기 자신(Waveform) 안에서 패턴을 분석한다.
3. Cross-Attention
	* 이때 외부의 Condition(Video/Text)이 들어와 Denoising을 위한 힌트를 제공하고, 소리 생성의 방향성이 생긴다.
4. MLP
	* 최종적으로 "이 소리는 이 방향으로 이동해야 한다!"를 구하게 된다.

![Image Description](/images/fig-dit-block.png)
> 원 논문에서 가장 좋았던 adaLN-Zero 블록. 조건(t, c)은 attention이 아니라 LayerNorm의 scale/shift와 residual 앞의 gate로 들어간다.

> [!note] 조건을 넣는 네 가지 방법 — 그리고 승자
> 위 1~4번은 "cross-attention을 쓰는 DiT"의 그림이다(오디오/텍스트 조건 모델들이 실제로 이렇게 쓴다). 그런데 원 논문은 조건(timestep $t$, class label $c$)을 주입하는 방법을 네 가지 비교했다.
>
> | 방식 | 어떻게 | 비용 | 결과 |
> | --- | --- | --- | --- |
> | In-context | $t$, $c$ 임베딩을 토큰 두 개로 시퀀스 앞에 붙임 | 거의 0 | 가장 나쁨 |
> | Cross-attention | 조건 시퀀스에 대해 별도 cross-attn 층 | 약 +15% Gflops | 중간 |
> | adaLN | 조건 벡터에서 LayerNorm의 scale γ, shift β를 회귀 | 가장 적음 | 좋음 |
> | **adaLN-Zero** | adaLN + residual 직전의 dimension-wise gate α를 **0으로 초기화** | 가장 적음 | **최고** (400K step에서 FID가 in-context의 거의 절반) |
>
> adaLN-Zero의 아이디어는 학습 초기에 각 블록이 항등함수(identity)에서 출발하게 만드는 것. 그래서 위 그림의 α가 "0으로 초기화"다. 정리하면 — 조건이 "짧은 벡터"(timestep, class, pooled text)라면 adaLN 계열이, 조건이 "긴 시퀀스"(문장 토큰, 비디오 프레임)라면 cross-attention이 자연스럽다. Stable Audio Open 같은 오디오 DiT가 텍스트 토큰은 cross-attention으로, timestep/타이밍 조건은 adaLN으로 넣는 이유가 여기 있다.

## Commentary

찝찝한 부분이 있다.

현재 DiT에서는 Self-Attention에서 Waveform의 패턴을 분석한 다음,
부가적으로 Condition이 들어와 Denoising을 시행한다.

그 말인즉슨, Waveform이 주(主), Video/Text가 부(副)가 되는 형태라고 볼 수 있겠다.

이런 식으로 이미지/오디오가 메인, 텍스트가 보조가 되면 정보 불균형이 생기지 않을까?

이걸 Hierarchical하지 않고, Equal하게 다룰 수는 없을까?

→ 다음 노트: [MM-DiT](/posts/mm-dit/)

## 참고 자료

- W. Peebles, S. Xie, [*Scalable Diffusion Models with Transformers*](https://arxiv.org/abs/2212.09748), ICCV 2023. 코드: [facebookresearch/DiT](https://github.com/facebookresearch/DiT).
- P. Esser et al., [*Scaling Rectified Flow Transformers for High-Resolution Image Synthesis*](https://arxiv.org/abs/2403.03206), 2024 (Stable Diffusion 3) — DiT를 두 모달리티 동등 구조로 확장한 MM-DiT.
- Z. Evans et al., [*Stable Audio Open*](https://arxiv.org/abs/2407.14358), 2024 — 오디오 latent 위에서 돌아가는 DiT의 실제 예 (T5 텍스트는 cross-attention, 타이밍 조건은 adaLN).
