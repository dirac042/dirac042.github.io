---
title: Magnitude Scaling Technique — SGMSE의 Amplitude Transformation
slug: magnitude-scaling-technique
date: 2026-08-13
draft: false
tags:
  - Audio
  - Diffusion
  - Speech Enhancement
---

복소 STFT(cSTFT) 위에서 Diffusion을 돌릴 때, 유난히 큰 스펙트럼 피크 때문에 학습이 흔들리는 문제를 어떻게 다루는지에 대한 짧은 정리.

[**SGMSE**](https://arxiv.org/abs/2208.05830) 논문(Richter, Welker, Lemercier, Lay, Gerkmann, *Speech Enhancement and Dereverberation with Diffusion-based Generative Models*, IEEE/ACM TASLP 2023)에서 처음 사용한 기법이다.

논문에서는 Amplitude Transformation이라는 단어로 표현한다.
* STFT에서 만들어지는 Complex Coefficient를 그대로 사용하되,
* Phase는 유지하고, Magnitude를 Power-Law로 압축해 전체 Scale을 줄이자.

![Image Description](/images/fig-amplitude-compression.png)
> 같은 신호의 |c|(왼쪽)와 β|c|^α(가운데). 크게 울리는 배음 몇 개가 화면을 독차지하던 것이, 압축 뒤에는 조용한 마찰음 덩어리와 희미한 상승음까지 보인다. 오른쪽은 α에 따른 압축 곡선.

## Introduction

SGMSE의 Task: Speech Enhancement/Dereverberation을 cSTFT 도메인에서 수행.
* Pred: Clean Speech의 Real/Imaginary Spectrogram
	* 왜? Magnitude-only Domain에서는 Diffusion Process가 어색해진다.
	* Magnitude는 음수가 될 수 없음 → Gaussian Noise를 더하면 음수값의 Amplitude가 나옴.

> [!note] 배경: 왜 하필 cSTFT인가
> Diffusion은 "데이터에 가우시안 노이즈를 더했다가 되돌리는" 과정이라, 데이터가 실수 전체(음수 포함)에 자연스럽게 퍼져 있어야 한다. 크기(magnitude)만 쓰면 항상 0 이상이라 노이즈를 더하는 순간 정의역을 벗어나고, 위상은 따로 복원해야 한다. 실수부/허수부로 나눈 cSTFT는 두 채널이 모두 실수라 이 문제가 없다. 논문 세팅은 16 kHz, window 510(주파수 빈 256개), hop 128(75% 겹침), periodic Hann.

## Amplitude Transformation

cSTFT Coefficient는 다음과 같이 정의된다:
$$c=|c|e^{i\angle c}$$
이때, $|c|$는 Magnitude, $\angle c$는 Phase다.

SGMSE는 위의 Coefficient를 다음과 같이 변환한다.
$$\tilde{c}=\beta |c|^{\alpha}e^{i\angle c}$$
* $\alpha \in (0,1]$ : Magnitude Compression Exponent
* $\beta > 0$ : Scale Factor

위를 자세히 보면, Phase, 그리고 Complex Direction은 전혀 바뀌지 않았고, Magnitude에만 Scaling이 가해졌다.

논문이 실험적으로 고른 값은 $\alpha=0.5$, $\beta=0.15$다. 숫자로 감을 잡아보면: 어떤 빈의 크기가 100이고 다른 빈이 1이라면 원래는 100배 차이지만, $\alpha=0.5$를 거치면 $0.15\times10=1.5$ 대 $0.15\times1=0.15$, 즉 **10배** 차이로 줄어든다. 큰 놈은 많이, 작은 놈은 조금 눌리는 것이 power-law 압축의 성질이다. 논문의 표현을 빌리면, α는 "에너지가 낮은 주파수 성분(예: 무성음의 마찰음)을 끌어올리는" 역할이고, β는 전체 크기를 diffusion 노이즈 스케일에 맞추는 정규화 역할이다.

## Inverse Amplitude Transformation

위의 Representation은 역변환도 간단하다.
$$c=\left(\frac{|\tilde{c}|}{\beta}\right)^{\frac{1}{\alpha}}e^{i\angle \tilde{c}}$$

주의할 점 하나: 역변환은 $1/\alpha$ 제곱이라 **압축된 도메인에서의 작은 오차가 원래 도메인에서는 증폭**된다. $\alpha$를 너무 작게 잡으면 큰 성분의 오차가 커지는 이유다. 0.5는 그 사이의 타협점.

```python
import numpy as np

def compress(c, alpha=0.5, beta=0.15):        # c: complex STFT (F, T)
    return beta * np.abs(c) ** alpha * np.exp(1j * np.angle(c))

def decompress(c_tilde, alpha=0.5, beta=0.15):
    return (np.abs(c_tilde) / beta) ** (1 / alpha) * np.exp(1j * np.angle(c_tilde))
```

## 효과

1. 너무 큰 Spectral Peak가 지배적이지 않게 만들 수 있다.
2. Low-Energy의 Speech 성분이 부각되어 숨소리 같은 소리가 잘 보존된다.
3. 원래 Diffusion의 Noise Scale에서 어긋나지 않는다.
4. Extreme Magnitude가 덜 나와서 학습이 안정적이다.
5. Perceptual Relevance가 증가한다. (결과물이 더 그럴싸해진다.)

> [!note] 어디서 본 것 같다면
> 맞다. 스펙트로그램을 로그로 보는 것(dB), mel-spectrogram의 log 압축, μ-law 같은 것들이 전부 "큰 값은 세게, 작은 값은 약하게 누른다"는 같은 아이디어다. 논문도 이런 압축이 heavy-tailed한 음성 STFT 크기 분포를 보정하고, 음성 향상에서 지각적으로 더 의미 있다는 기존 연구를 근거로 든다. 차이라면 SGMSE는 로그가 아니라 power-law($|c|^{0.5}$)를 써서 0 근처에서도 매끄럽고 역변환이 깔끔하다는 점.

## 참고 자료

- J. Richter, S. Welker, J.-M. Lemercier, B. Lay, T. Gerkmann, [*Speech Enhancement and Dereverberation with Diffusion-based Generative Models*](https://arxiv.org/abs/2208.05830), IEEE/ACM TASLP 31, 2023. — 변환식, α=0.5·β=0.15, OU 드리프트 + Variance Exploding 확산으로 이루어진 SDE(OUVE)까지 이 논문.
- S. Welker, J. Richter, T. Gerkmann, [*Speech Enhancement with Score-Based Generative Models in the Complex STFT Domain*](https://arxiv.org/abs/2203.17004), Interspeech 2022. — 같은 그룹의 앞선 버전.
- 코드: [sp-uhh/sgmse](https://github.com/sp-uhh/sgmse) — `spec_transform` 쪽을 보면 위 식이 그대로 있다.
