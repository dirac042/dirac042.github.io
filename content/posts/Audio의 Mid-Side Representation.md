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

> [!note] 왜 1 ms가 큰 문제인가 — 사람이 공간을 듣는 방법
> 두 귀 사이의 거리는 약 17 cm라서, 소리가 한쪽 귀에 먼저 닿는 시간차(ITD, interaural time difference)는 최대 0.6~0.7 ms 정도다. 뇌는 이 sub-millisecond 차이와 크기 차이(ILD), 주파수별 위상차(IPD)로 소리의 방향을 잡는다. 즉 1 ms의 위상 오차는 "약간 틀린" 게 아니라 **가능한 ITD 범위를 통째로 벗어난** 오차다. 그런데 L, R을 각각 따로 L1/MSE로 비교하면 이 오차는 파형 전체가 살짝 밀린 정도로만 보여 거의 벌점을 받지 않는다.

## Mid-Side Processing

Left/Right 신호를 간단한 Linear Combination으로 나타내는 방법.

$$\text{Mid}=\frac{L+R}{2}$$
$$\text{Side}=\frac{L-R}{2}$$
* Mid: 소리의 공통 성분. (Mono Downmix)
* Side: 두 채널의 차이. (공간, 위상차, Reverb 등의 정보만 남음)

역변환도 간단하다: $L=\text{Mid}+\text{Side}$, $R=\text{Mid}-\text{Side}$.

![Image Description](/images/fig-mid-side.png)
> 가운데서 나는 소리(공통 성분)와 왼쪽에서 조금 늦게 오른쪽 귀에 닿는 소리를 섞은 예. L과 R은 거의 똑같아 보이지만, Side에는 두 귀의 차이 — 방향을 알려주는 성분 — 만 남는다.

장점
1. 자원 낭비가 없다.
	* Mid가 가지고 있는 정보와 Side가 가진 정보가 각각 다르다.
2. Phase Error에 직접적인 페널티가 존재한다.
	* Side에 L1 Loss만 걸어줘도 Phase를 잡을 수 있다.
3. 모노 호환·조절이 쉽다.
	* Mid만 남기면 그대로 모노 다운믹스이고, Side에 gain만 곱하면 스테레오 폭이 조절된다. 방송·믹싱에서 M/S를 오래 써온 이유이기도 하다.

> [!note] 2번을 숫자로 확인해보기
> 500 Hz 사인파가 L과 R에 똑같이 들어 있다고 하자(정중앙 소리). 모델이 R만 1 ms 늦게 냈다면, 500 Hz의 주기는 2 ms이니 1 ms는 정확히 반주기 = 위상 180°다. L/R 각각의 L1 오차는 파형이 조금 밀린 정도지만, Side = (L − R)/2 는 원래 0이어야 할 것이 **진폭이 원음과 같은 사인파**가 되어버린다. Side에 걸린 L1이 이걸 그대로 벌점으로 만든다.

```python
import numpy as np

def to_mid_side(x):          # x: (2, T) stereo waveform
    L, R = x
    return np.stack([(L + R) / 2, (L - R) / 2])

def from_mid_side(ms):
    M, S = ms
    return np.stack([M + S, M - S])
```

> [!note] 어디에 쓰이나
> * **Mono-to-binaural 연구**(2.5D Visual Sound, CCStereo 등)는 정확히 이 분해를 쓴다: 입력은 mono(L+R)이고, 모델은 difference(L−R)의 spectrogram/mask를 예측한 뒤 $L=(M+D)/2$, $R=(M-D)/2$로 되돌린다. Mid는 이미 주어졌으니 모델은 "공간 정보"만 배우면 된다.
> * 위 정의에서 1/2 대신 $1/\sqrt2$를 쓰면 변환이 직교(orthonormal)가 되어 에너지가 보존된다. 손실 함수에 쓸 때는 어느 쪽이든 상관없지만, M/S를 다시 섞어 STFT를 비교할 때는 스케일을 맞춰야 한다.
> * 다채널(5.1, ambisonics)로 가면 같은 아이디어가 "공통 성분 + 차이 성분" 분해로 일반화된다.

## 참고 자료

- R. Gao, K. Grauman, [*2.5D Visual Sound*](https://arxiv.org/abs/1812.04204), CVPR 2019 — mono에서 L−R을 예측해 binaural을 만드는 대표 논문.
- [Interaural time difference — Wikipedia](https://en.wikipedia.org/wiki/Interaural_time_difference), [Mid/Side (stereophonic sound) — Wikipedia](https://en.wikipedia.org/wiki/Stereophonic_sound#M/S_technique:_mid/side_stereophony).
