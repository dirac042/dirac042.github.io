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

Descript Audio Codec: Neural Audio Codec (오디오를 작게 압축하고, 원본에 가까운 음질로 복원). 오디오 생성 모델들이 Latent를 만들 때 자주 쓰는 코덱이라 구조를 짧게 정리해 둔다. 논문은 Kumar et al., [*High-Fidelity Audio Compression with Improved RVQGAN*](https://arxiv.org/abs/2306.06546) (NeurIPS 2023). 숫자로 요약하면 **44.1 kHz 오디오를 8 kbps, 약 90배 압축**하면서 음성·음악·환경음을 모델 하나로 다룬다.

## 구조

1. Encoder: Waveform을 CNN에 태우기 → Continuous Latent Representation 생성

2. **RVQ (Residual Vector Quantization)**
	* 연속적인 값을 Discrete한 Token으로 바꾸기 → Quantization
	* 첫 번째 층: 전체적 뼈대만 잡아서 토큰화 → Residual이 크다
	* 두 번째 ~ n번째 층: 이전 층의 오차(Residual)만 받아와서 Token화 → 반복…
	* 오차가 0에 수렴 → 적은 Token으로 디테일한 소리 정보 저장.

3. Decoder: RVQ의 Discrete Token을 입력받아, Waveform으로 만들기
	→ 훈련을 GAN으로 함. (그래서 이름이 RVQGAN)

![Image Description](/images/fig-rvq.png)
> RVQ 한 장 요약. 각 단계는 "남은 오차"만 양자화하므로, 뒤 코드북일수록 미세한 디테일을 담당한다.

> [!note] 비트레이트를 직접 계산해보면
> Encoder의 stride가 512라서 44.1 kHz 파형이 초당 약 86 프레임(44100/512 ≈ 86.1)의 latent가 된다. 프레임마다 코드북 9개가 각각 10비트(1024개 코드 중 하나) 인덱스를 내놓으니 86 × 9 × 10 ≈ 7,750 bps ≈ **8 kbps**. 원본 16-bit PCM(705.6 kbps)과 비교하면 약 91배 압축이다. 코드북 개수를 줄이면(예: 앞 4개만) 그대로 낮은 비트레이트 모델이 되는데, 이게 되도록 학습 때 **quantizer dropout**(예시마다 p=0.5 확률로 코드북 개수를 랜덤하게 자름)을 쓴다.

> [!note] 코드북이 죽지 않게 하는 두 가지 트릭
> VQ의 고질병은 코드북의 일부만 쓰이고 나머지는 죽어버리는 것(codebook collapse). DAC는 이미지 쪽 Improved VQGAN에서 두 가지를 가져왔다. **Factorized codes**: 코드 lookup은 8차원(또는 32차원)의 낮은 공간에서 하고, 실제 임베딩은 1024차원에 둔다 — 찾기는 쉽게, 표현력은 크게. **L2-normalized codes**: 인코더 출력과 코드북 벡터를 정규화해 유클리드 거리 대신 코사인 유사도로 매칭 → 안정성과 품질이 좋아진다.

## 구조적 특징

1. Fully Convolutional Network(FCN, 1차원 CNN)을 Encoder/Decoder에 사용
2. Snake Activation Function을 전 Layer에 사용 (주기가 있는 함수에 good)
3. Dilated Convolution으로 듬성듬성 넘어가서 Receptive Field 넓히기

![Image Description](/images/fig-snake.png)
> Snake: $x+\frac{1}{\alpha}\sin^2(\alpha x)$. 항등함수에 주기적인 굴곡이 들어가 있어서, ReLU로는 잘 못 배우는 주기 신호(= 소리)를 표현하기 좋다. 논문에서는 ReLU를 Snake로 바꾸는 것만으로 SI-SDR이 눈에 띄게 올랐다.

> [!note] 어떻게 학습시키나 (loss 구성)
> Decoder는 GAN으로 학습하는데, 판별자가 세 종류다: **multi-period** 파형 판별자(주기 2, 3, 5, 7, 11로 파형을 접어서 봄), **multi-scale STFT** 판별자(window 2048/1024/512), 그리고 STFT를 sub-band로 쪼개 고주파와 앨리어싱을 잡는 **multi-band multi-scale STFT** 판별자. 손실은 multi-scale mel reconstruction(가중치 15), feature matching(2), adversarial(HingeGAN, 1), codebook(1), commitment(0.25)의 합이다.

## 다음 이야기

→ Discrete Token을 생성하는 RVQ를 버리고, Continuous한 VAE를 쓰자 → DAC-VAE (Semantic-VAE)

## 참고 자료

- R. Kumar, P. Seetharaman, A. Luebs, I. Kumar, K. Kumar, [*High-Fidelity Audio Compression with Improved RVQGAN*](https://arxiv.org/abs/2306.06546), NeurIPS 2023. 코드/가중치: [descriptinc/descript-audio-codec](https://github.com/descriptinc/descript-audio-codec).
- N. Zeghidour et al., [*SoundStream: An End-to-End Neural Audio Codec*](https://arxiv.org/abs/2107.03312), 2021 — RVQ를 오디오 코덱에 처음 쓴 논문. A. Défossez et al., [*High Fidelity Neural Audio Compression*](https://arxiv.org/abs/2210.13438) (EnCodec), 2022 — DAC가 주로 비교하는 상대.
- L. Ziyin, T. Hartwig, M. Ueda, [*Neural networks fail to learn periodic functions and how to fix it*](https://arxiv.org/abs/2006.08195), NeurIPS 2020 — Snake activation의 출처. BigVGAN도 같은 활성함수를 쓴다.
