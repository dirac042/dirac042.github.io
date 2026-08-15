---
title: Semantic-VAE (DAC-VAE) 논문 정리
slug: dac-vae
date: 2026-07-06T10:10:00+09:00
draft: true
tags:
  - Audio
  - TTS
  - Paper Notes
---

# Semantic-VAE: Semantic-Alignment Latent Representation for Better Speech Synthesis

## 1. 이 논문이 해결하려고 하는 문제는

기본 Task: Zero-Shot Text-to-Speech (TTS)
* Reference Speech Prompt의 Semantic 정보를 유지하면서, 입력 텍스트를 자연스러운 음성으로 합성하기

기존 Method
* AR(AutoRegressive) Discrete-Token 방식
	* 음성을 Discrete Token으로 양자화 → Autoregressive하게 생성
	* 문제: Inference가 매우 느리다, Quantization 과정에서 Information Loss 발생
* NAR(Non-AutoRegressive) Mel-Spectrogram 방식
	* Diffusion/FM으로 Mel-Spectrogram 생성 → Vocoder가 Waveform으로 복원
	* 문제: Mel-Spec.이 가지는 Phase Information의 부재 → Text-Speech Alignment가 비효율적
* VAE Latent 방식
	* VAE가 Waveform을 Continuous Latent로 압축 → Downstream TTS가 Latent 생성
	* 문제: Reconstruction/Generation Dilemma

문제점: **Reconstruction/Generation Dilemma**
	Latent가 작으면 작아질수록 Generation은 쉽지만, Reconstruction은 어렵다.

## 2. 이 논문의 Contribution은

모델 Semantic-VAE: VAE의 Latent → Waveform 재구성 Good + pre-trained SSL speech model 안의 semantic 구조와 정렬되도록 학습.

1. Semantic Alignment Regularization
	* Frozen SSL 모델에서 Speech Feature 뽑기 → Interpolation + 1D Conv.로 VAE Latent와 차원을 맞추고, Negative Cosine Similarity 기반 Alignment Loss 추가
2. Reconstruction/Generation Trade-off의 완화
	* VAE Reconstruction Loss, KL, Adversarial/Feature Matching Loss에다가 Semantic Alignment Loss를 결합
3. F5-TTS
	1. 
