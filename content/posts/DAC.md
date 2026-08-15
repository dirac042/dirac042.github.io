---
title: DAC (Descript Audio Codec) 정리
slug: dac
date: 2026-07-06T10:00:00+09:00
draft: false
tags:
  - Audio
  - Codec
  - Paper Notes
---

Descript Audio Codec: Neural Audio Codec (오디오를 작게 압축하고, 원본에 가까운 음질로 복원). 오디오 생성 모델들이 Latent를 만들 때 자주 쓰는 코덱이라 구조를 짧게 정리해 둔다.

## 구조

1. Encoder: Waveform을 CNN에 태우기 → Continuous Latent Representation 생성

2. **RVQ (Residual Vector Quantization)**
	* 연속적인 값을 Discrete한 Token으로 바꾸기 → Quantization
	* 첫 번째 층: 전체적 뼈대만 잡아서 토큰화 → Residual이 크다
	* 두 번째 ~ n번째 층: 이전 층의 오차(Residual)만 받아와서 Token화 → 반복…
	* 오차가 0에 수렴 → 적은 Token으로 디테일한 소리 정보 저장.

3. Decoder: RVQ의 Discrete Token을 입력받아, Waveform으로 만들기
	→ 훈련을 GAN으로 함. (그래서 이름이 RVQGAN)

## 구조적 특징

1. Fully Convolutional Network(FCN, 1차원 CNN)을 Encoder/Decoder에 사용
2. Snake Activation Function을 전 Layer에 사용 (주기가 있는 함수에 good)
3. Dilated Convolution으로 듬성듬성 넘어가서 Receptive Field 넓히기

## 다음 이야기

→ Discrete Token을 생성하는 RVQ를 버리고, Continuous한 VAE를 쓰자 → DAC-VAE (Semantic-VAE)
