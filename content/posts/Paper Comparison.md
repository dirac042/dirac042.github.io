---
title: Audio Generation 논문 비교 노트
slug: paper-comparison
date: 2026-07-06T09:00:00+09:00
draft: true
tags:
  - Audio
  - Paper Notes
---

## Control Group

2가지의 축(Dilemma) 존재:
1. **Dimensional Dilemma**: 데이터를 어떻게 압축/표현할 것인가?
	* **Acoustic**: 소리의 음향적/물리적 특징으로 압축하자.
		* DAC, EnCodec 등 전통적인 오디오 코덱
		* 장점: Latent 공간 안에서 소리의 파형을 완벽하게 복원 가능.
		* 단점: 의미적 정보가 Entangled됨.
	* **Semantic**: 소리가 담는 고차원적인 의미로 압축하자.
		* **Semantic-VAE**
2. **Objective Dilemma**: 압축된 공간에서, 모델이 수행하는 태스크는 무엇인가?
	* **Reconstruction**: 원본 데이터를 입력으로 받아, 손실 없이, 다른 모달리티의 도움을 받아 원래의 물리적 형태로 되돌리자.
		* **SIREN**
	* **Generation**: Condition을 가지고, 노이즈로부터 완전히 새로운 데이터를 창조하자.
		* **Stable Audio (Condition: Text)**
		* **VisAudio/MMAudio (Condition: Video)**
	* 역설: Reconstruction을 완벽하게 하는 VAE를 만든다고, 위에서 작동하는 Generative Model이 성능이 좋아지지 않는다.
		* 모델: VAE로 만든 Latent → Generative Model → Latent를 다시 Waveform(VAE)
		* VAE가 Acoustic을 100% 복원 → 미세한 디테일까지 Latent Space로 우겨넣기
		* 

처음 이 문제를 제기한 논문은 **LongCat-AudioDiT**
* Waveform이 잘 일치하는 모델을 만든다고 해서, 소리가 좋아지는 건 아니다.

이걸 여러 방식으로 2개의 Trade-off를 Balancing
* **Semantic-VAE**: 오디오에서 semantic feature를 뽑고, 그걸 cosine sim. 계산해서 넣자.
* **LongCat-AudioDiT**: APG를 활용해서 semantic feature가 너무 커지는 걸 막자.
* **VisAudio**: Video에서 depth를 추출, align해서 semantic feature를 넣자.
* **Stable Audio**: Audio-Text가 잘 학습된 CLAP을 text encoder로 사용하자.
* **Stable Audio Open**: DiT의 Cross Attn.으로 2개의 feature를 잘 결합하자.


* **Semantic-VAE**
	* Waveform을 바로 다루는 것은 크기가 너무 크다.
		* 그래서 VAE나 DAC를 통해, 오디오를 Latent로 압축해서 학습시키는 방법을 사용함.
	* 기존 모델들은 Reconstruction: 원본의 소리를 완벽하게 복원하는 데에 초점.
		* Latent가 Acoustic 정보만 많지, Semantic 정보가 거의 없음.
		* ? 그래서, TTS 생성모델이 Latent를 생성할 때, 발음이 뭉개짐 + Semantic Mapping을 학습하기 어려워짐.
	* ! 위 문제를, Semantic-VAE, 즉 Semantic 정보까지 잘 담아내는 VAE 구조로 해결.
		* Semantic Alignment Regularization, 의미 정보의 정렬을 정규화하기
			* Latent 공간에 의미를 주입하기 위해, Speech Foundation Model(WavLM)을 Teacher로 삼아 Distillation
				* 원본 오디오를 모델(SSL)에 통과 -> Semantic Feature 생성
				* VAE가 오디오를 압축하면서 만든 Latent, 원본 오디오에서 나온 Semantic Feature의 Cosine Similarity 계산 -> Regularization Loss를 학습 Loss에 추가
		* Semantic Control을 강하게 학습했지만, Reconstruction 성능도 매우 강하게 잘 나옴.
* **LongCat-AudioDiT**
	* 마찬가지, Waveform은 크기가 너무 크다
		* 그래서 원래 고전 모델들은 Mel-Spectrogram으로 변형, 이걸 Representation으로 사용함. (Image Model을 사용할 수 있으니까.)
	* ? 문제: Waveform - Mel-Spectrogram - Vocoder로 다시 Waveform 만들기에서, Mel에서 생기는 작은 오차가, Vocoder로 Waveform을 만들 때 증폭됨.
		* 이를 Compounding Error라고 칭함.
	* ! 위 문제를, Audio Representation인 Mel-Spec를 버리고, Waveform을 압축해서 Latent로 만드는 방식을 사용
		* Waveform을 바로 Latent로 압축하는 **Wav-VAE**
		* Latent Space에서 작동하는 Non-Autoregressive DiT 사용
	* ! 주목할만한 Inference 과정에서의 혁신
		1. Training-Inference Mismatch의 해결: Diffusion 모델이 학습할 때의 상태 vs 실제로 노이즈를 제거하면서 추론하는 수학 분포적 불일치 해결
		2. **Adaptive Projection Guidance**: 기존 모델들의 CFG는 Guidance Scale을 사용해서, 모델 안에서 Text 정보의 영향을 증폭시킨다.
			* 기존 CFG의 문제: Scale이 너무 높아지면 소리가 이상해짐
			* APG: 너무 예측 방향이 뻗어나가면, 데이터의 범위 내로 다시 Projection 시켜주기.
				* 텍스트의 Condition은 지키면서, Waveform의 Fidelity는 전혀 안 뭉개짐.
	* Ablation
		* 일반적인 생각: VAE가, 원본 Waveform을 완벽하게 Reconstruction 할수록, VAE 위의 TTS Backbone의 성능도 당연히 좋아지겠지?
		* id Ablation 결과: 그렇지 않음. Waveform의 Reconstruction이 좋다고, VAE 위 TTS가 좋아지지 않음. -> **Acoustic vs Semantic의 딜레마**
* **MMAudio**
	* Task: Video-to-Audio
	* ? 문제점: Video-Audio Pair는, Text-Audio Pair보다 구하기 어려움.
		* 일단 오디오 품질이 떨어짐.
		* Text-Audio 모델을 Fine-Tuning: 영상과의 시간적 동기화가 어긋남.
	* ! 위의 문제점을, Multimodal Joint Training으로 해결
		* Text-Audio 데이터와 Video-Audio 데이터를 하나의 네트워크에서 동시에 학습
			* Video, Text, Audio를 모두 동시에 입력, or 특정 모달리티에 mask 씌우기
			* One Transformer Network 안에 unified semantic space
* **VisAudio**
	* Task: Video-to-Audio
	* 기존 모델: 영상과 Semantic하게 일치하면서, Audio의 Acoustic Detail도 좋다.
		* ? 문제: Mono나 Simple Stereo에 그치기 때문에, 3D에서 존재하는 Spatial Cue를 담아내지 못함.
	* 현실 세계에서 인간의 귀는, ITD, IPD 등의 정보를 이용해 공간감을 느낄 수 있음.
		* 비디오에서 나오는 위치, Depth, 카메라 움직임 등으로 Binaural Audio를 만들 수 없을까?
	* ! 위 Task를, 여러 방식으로 해결
		* End-to-End Binaural Sound Generation 모델
			* 기존: Spatial 오디오를 만드려면 Mono Audio -> HRTF등의 DSP를 통한 Spatial Rendering 과정을 거쳐야 했음.
				* 복잡한(Cascaded) 파이프라인
		* Visual Spatial Cues의 Alignment
			* 영상 프레임에서, Depth 피쳐 추출
			* 이 정보를 ITD,ILD와 같은 Audio Metadata와 Align
* **Stable Audio**
	* Stereo Audio를 Long-Form으로 생성하는건 어렵다.
	* 기존 Diffusion Model은 고정된 길이(30초)만 가능, crop해서 학습했음.
		* ? 그래서, 생성된 결과물이 Structure를 가지고 있지 못함.
	* ! 위 문제를, Latent Diffusion과 Time-Conditioning으로 해결
		* Waveform에서의 Diffusion -> Latent에서 Diffusion
			* DAC의 Fully-Convolutional VAE를 사용 -> Latent 생성
		* Time-Conditioning: Time Metadata를 임베딩해 모델에 주입
			* seconds_start: 학습데이터의 오디오조각이 원본 몇 초인지
			* seconds_total: 원본 파일의 전체 길이가 몇 초인지
		* Text Encoder: 오디오-텍스트 학습된 CLAP 텍스트 인코더 사용
		* Diffusion Backbone: U-Net 구조인데, Memory-efficient Attention
		* + 길이 기반 Frechet Distance 평가 지표 제안
* **Stable Audio Open**
	* Stable Audio에서의 1D U-Net을, **DiT**로 변경
		* 왜? U-Net은 Local 구조는 잘 잡지만, 스케일이 커지면 Saturate됨 (성능 향상이 포화)
	* Stable Audio의 Text Encoder를 CLAP -> **T5**
		* CLAP의 문제: 길게 작성된 프롬프트의 문맥적 의미 파악이 안 됨.
		* T5-Large: LLM 모델이라, 텍스트 자체의 시맨틱 압축이 잘 됨.
	* Stable Audio의 U-Net Condition Injection
		* 텍스트 정보는 Cross-Attention에 넣기
		* Timing-Condition은 Sinusoidal 임베딩으로 바꿔, Conv. Feature Map에 더하거나, 채널 축으로 Concat
	* Stable Audio Open의 **DiT Condition Injection**
		* Cross-Attention: T5에서 나온 텍스트 토큰 -> DiT 블록 내부에서 Cross Attn.
		* AdaLN-Zero: Diffusion Timestep, Time-Conditioning 임베딩을 합산 -> Transformer Block 안에 Layer Norm Scale, Shift 2개를 Modulation
* **Stable Audio 3**
	* 초기 모델의 DAC 기반의 VAE -> **SAME**: 오디오 전용 AE 도입
		* 4096배의 Downsampling Ratio, 원본의 Acoustic, Semantic Detail 보존
		* VRAM 소모 없이 빠른 Downsampling 가능
	* Generation with Variable Length
		* ? 초기 모델: 긴 오디오는 생성 가능, 짧은 오디오를 생성하려면 긴 오디오를 만들고, 남는 부분 버리는 방법 사용.
		* SA3: n초짜리가 필요하면, n초만큼의 연산만 수행. -> Inference 속도 매우 빨라짐.
	* Learning Objective + Sampling Method
		* 초기 모델: Latent Diffusion 사용
		* SA3: Flow Matching -> Adversarial Post-Training
			* Inference: 노이즈 제거 -> 소량의 노이즈 다시 주입 -> 다시 제거 (Ping-Pong Sampling)
			* CFG가 필요없어짐 -> 추론 속도가 매우매우매우 빨라졌다!
	* Inpainting & Continuation
		* 초기 모델: 텍스트 프롬프트에 기반한 '처음부터 오디오 생성하기'에 집중
		* SA3: Mask Condition을 모델에 통합:
			* Inpainting: 오디오의 특정 구간 지정 -> 다른 악기 소리로 교체 및 수정 가능
			* Continuation: 짧은 클립의 뒷부분을 자연스럽게 Extend
* [**SIREN**](https://arxiv.org/abs/2603.29820)
	* 일반적인 영상(consumer video)는 소리가 공간감 없는 mono audio로 녹음됨.
		* 그래서, 이걸 binaural하게 변환해야 몰입형으로 바뀜.
	* 기존 모델: 영상에서 소리의 좌/우 위치의 측정
		* 사람이 직접 pixel 단위의 mask를 씌움.
		* ? 너무 mask-dependent하고, spatial grounding을 제대로 못 잡음.
	* ! 위의 문제를 SIREN 프레임워크로 해결
		* ViT-based Dual-head Self Attention 사용
			* ViT 인코더로 화면 안 객체 (Patch Token) 분석
			* 화면 전체 scene 맵 + Attention Map(좌/우) 동시에 학습
		* Soft Annealed Spatial Prior: 어닐링 사용
			* 학습 초반에 모델이 소리를 엉뚱하게 잡는 문제 → Spatial Prior 주입
			* 근데, 학습이 지날수록 서서히 사라짐 (어닐링)
			* 초기 학습이 안정적, 최종 모델의 유연성 방해 X
	* Inference: Confidence-Weighted Fusion
		* ? 긴 오디오를 여러 window로 자르기 → 이어붙일 때 Crosstalk(혼선), Phase 왜곡 생김
		* 1차원 복원된 Mono-Audio + IPD 기준, Confidence Score 매기기
		* 이후, Waveform에서 Fusion → 깔끔한 입체 음향

* ViSAudio vs SIREN
	* ViSAudio: **Generation**
		* 텍스트/비디오만 보고, 백지 상태에서 입체적인 소리를 완전히 새롭게 만들기
	* SIREN: **Reconstruction**
		* 이미 존재하는 모노 오디오를 바탕으로, 소리를 좌/우 배치 + 위상의 조절
	* 

## 직접 돌려본 Stable Audio Open

솔직히 좀 구리다.

1. Music Generation 퀄리티가 별로임
	→ 아마 이건 open-source로 학습시켰기 때문.
	→ 그리고 학습할 때 효과음으로 학습시켜서, 효과음 생성은 진짜 잘 됨. (audio source)

2. Talking, 대화 소리를 못 냄
	→ 애초에 TTS 모델이아님, Semantic을 뱉어내는 구조가 없다. (texture만 출력)

3. “Left Ear”와 같이, 공간감이 없다.
	→ 3D 공간을 이해하는 부분이 모델에 없음.

4. 텍스트 인코더를 T5를 사용해서 그런지, 복잡한 텍스트도 잘 알아먹음.

* **WavTTS**
	* 이전 모델: VQ-VAE, DAC와 같은 Latent Space로의 압축
		* 문제: 아직까지도 Long-Range Linguistic Dependencies와 Fine-Grained Phase, Periodicity, High-Freq. Structure를 동시에 잡기가 힘들다. (Waveform에서는)
		* 문제: Waveform-based TTS는 modern zero-shot settings로 scale됨 → mel-, latent-space TTS와의 generalization gap이 존재.


* **Back to Ear: Perceptually Driven High Fidelity Music Reconstruction**
	* 읽은 이유: 지금 내가 겪고있는 문제를 Tackle하고 있는 논문이라서!
		* 문제: VAE가 Phase를 잘 못 잡음. (input이 single channel이라서.)
	* 기존 모델: DiT 기반 Backbone Model (DAC, EnCodec 등)은 