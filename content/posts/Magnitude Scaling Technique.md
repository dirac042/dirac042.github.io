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

[**SGMSE**](https://arxiv.org/pdf/2208.05830) 논문에서 처음 사용한 기법이다.

논문에서는 Amplitude Transformation이라는 단어로 표현한다.
* STFT에서 만들어지는 Complex Coefficient를 그대로 사용하되,
* Phase는 유지하고, Magnitude를 Power-Law로 압축해 전체 Scale을 줄이자.

## Introduction

SGMSE의 Task: Speech Enhancement/Dereverberation을 cSTFT 도메인에서 수행.
* Pred: Clean Speech의 Real/Imaginary Spectrogram
	* 왜? Magnitude-only Domain에서는 Diffusion Process가 어색해진다.
	* Magnitude는 음수가 될 수 없음 → Gaussian Noise를 더하면 음수값의 Amplitude가 나옴.

## Amplitude Transformation

cSTFT Coefficient는 다음과 같이 정의된다:
$$c=|c|e^{i\angle c}$$
이때, $|c|$는 Magnitude, $\angle c$는 Phase다.

SGMSE는 위의 Coefficient를 다음과 같이 변환한다.
$$\tilde{c}=\beta |c|^{\alpha}e^{i\angle c}$$
* $\alpha \in (0,1]$ : Magnitude Compression Exponent
* $\beta > 0$ : Scale Factor

위를 자세히 보면, Phase, 그리고 Complex Direction은 전혀 바뀌지 않았고, Magnitude에만 Scaling이 가해졌다.

## Inverse Amplitude Transformation

위의 Representation은 역변환도 간단하다.
$$c=\left(\frac{|\tilde{c}|}{\beta}\right)^{\frac{1}{\alpha}}e^{i\angle \tilde{c}}$$

## 효과

1. 너무 큰 Spectral Peak가 지배적이지 않게 만들 수 있다.
2. Low-Energy의 Speech 성분이 부각되어 숨소리 같은 소리가 잘 보존된다.
3. 원래 Diffusion의 Noise Scale에서 어긋나지 않는다.
4. Extreme Magnitude가 덜 나와서 학습이 안정적이다.
5. Perceptual Relevance가 증가한다. (결과물이 더 그럴싸해진다.)
