---
title: Audio의 Mid-Side Representation
slug: mid-side-representation
date: 2026-07-06T10:40:00+09:00
draft: false
tags:
  - Audio
  - Binaural
  - Notes
---

Binaural/Stereo 오디오를 모델에 넣을 때, 왜 Left/Right 대신 Mid/Side로 바꿔서 다루는지에 대한 짧은 메모.

## Left-Right Processing

기본적으로 Binaural Audio 태스크에서 오디오는 2개의 Waveform으로 주어진다:
* Left Waveform: 왼쪽 귀에서 들리는 소리
* Right Waveform: 오른쪽 귀에서 들리는 소리

이 표현에는 문제점이 몇 가지 존재한다.

1. 모델의 자원 낭비: Left와 Right의 에너지와 주파수의 Correlation은 90% 이상으로 매우 높다.
	* 각각을 예측하라고 하면, Semantic/Acoustic을 두 번 중복해서 학습해야 한다.
2. Phase Error에 대한 페널티가 없다.
	* L/R의 Phase가 1ms 어긋났다고 가정하자.
	* 전체 Waveform의 관점에서는 둘 다 1ms 어긋났으니까, L1/MSE Loss의 변화가 없다.
	* 하지만 사람이 들으면 입체감이 붕괴된 안 좋은 소리가 난다.

## Mid-Side Processing

Left/Right 신호를 간단한 Linear Combination으로 나타내는 방법.

$$\text{Mid}=\frac{L+R}{2}$$
$$\text{Side}=\frac{L-R}{2}$$
* Mid: 소리의 공통 성분. (Mono Downmix)
* Side: 두 채널의 차이. (공간, 위상차, Reverb 등의 정보만 남음)

역변환도 간단하다: $L=\text{Mid}+\text{Side}$, $R=\text{Mid}-\text{Side}$.

장점
1. 자원 낭비가 없다.
	* Mid가 가지고 있는 정보와 Side가 가진 정보가 각각 다르다.
2. Phase Error에 직접적인 페널티가 존재한다.
	* Side에 L1 Loss만 걸어줘도 Phase를 잡을 수 있다.
