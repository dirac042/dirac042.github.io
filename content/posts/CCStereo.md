---
title: CCStereo 논문 정리 & 모델 수정 기록
slug: ccstereo
date: 2026-06-14
draft: true
tags:
  - Audio
  - Binaural
  - Research Log
---

![Image Description](/images/CleanShot%202026-06-11%20at%2018.42.49.png)


용준님 Task의 비교 대상으로 삼은 모델.
모델이 풀고자 하는 Task가 달라서, 꼼꼼하게 읽어보고 코드를 수정해서 비교 대상에 맞게 변경하려고 함.

## Introduction

풀고자 하는 Task Field: Binaural Audio Generation (BAG)
* Binaural Audio Recording은 사람의 머리를 재현해야하므로, Costly하다.
* 그래서, Mono Audio를 Record한 다음에, Spatialize하는 방향으로 해결함 → BAG

문제 1: **기존 방식은 Simple Fusion을 사용하기 때문에, 복잡한 Visual-Spatial 관계를 학습할 수 없다.**
* 이걸 해결하기 위해, Modalities간의 Semantic/Spatial Awareness를 Enhance하는 방식들을 고안하게 됨.
* 문제는, 이런 방식들도 Concat.이나 Cross Attention을 Generation의 Guide로 사용
	* Cross Attn.은 Different Modalities에서 Feature Blending은 잘 하지만,
	* ? Audio의 Aligning, Spatial Fidelity Aligning에는 못 한다. (진짜?)
* 이 논문의 View: Cross Attn.은 두 데이터의 Global 상관관계를 계산해, 가중합을 구하는 방식으로 계산됨.
	* 근데, Attn. 연산을 거치면서 이 Fine-Graned된 Conditioning Information이 넓게 융합(Blending)되어버림
	* 그래서, (화면의 좌표, 오디오 파형) 사이의 관계(Spatial Aligning)가 엉망이 되어버린다.
* ! 논문: 아, 그러면 Visual Feature를 Audio Feature에 직접 더하거나 곱하지(Fusion) 말고, 오디오 Decoder 안에서 **Visual Context를 조건**으로 해서 Audio Feature Map의 평균/분산을 실시간으로 Align 한다면(**Modulation**)?
	* 내가 원하는 Visual Feature대로 Audio Feature를 ‘조정’할 수 있는 능력이 생긴다
	* 근데, **원본 Feature Map의 Topology는 변하지 않음!**
		* Cross Attention처럼 오디오의 Time/Frequency 구조가 망가지지 않는다는 것!
	* 실제 이미지 생성모델에서도 Modulation 방식이 차용됨.
		* ex. StyleGAN의 **AdaIN(Adaptive Instance Normalization)**
		* ![Image Description](/images/CleanShot%202026-06-11%20at%2018.37.29.png)
			* 기존 이미지의 형태(content), 그리고 질감, 색상(Style)을 자연스럽게 섞는게 어렵다.
			* 1. Target Image Feature Map의 평균, 표준편차 구하고 Normalize
				* (이렇게 되면, 원래 사진 안에 있었던 스타일 정보는 아예 지워짐)
			* 2. 내가 입히고 싶은 스타일 벡터 $y$에서, Scaling 변수 $y_{s,i}$, 이동 변수 $y_{b,i}$ 계산
			* 3. Normalized Target Feature Map에다가 매개변수 2개를 곱하고, 더해준다!
		* AdaIN과 비슷하게, 내가 원하는 ‘Visual Info.’에 따라, Normalized된 Audio Feature Map에다가 매개변수를 곱하고 더해서 Probability Distribution을 Morph하는 느낌!

문제 2: **기존 방식은 Training 데이터의 환경에 오버피팅하는 모습을 보인다.**
* 왜? Specific Data Dist.의 의존성 + Regularization 방식의 불충분함
	* 논문 ‘2.5D Visual Sound (Gao et al. 2018)’에서 발표한 FAIR-Play 데이터셋은 이 문제를 풀지 못 함
	* → 이유: Training, Test Set의 Spatial Overlap이 많음 → Overly Optimistic Evaluation을 보여줌.
* 이전 논문들의 해결 방식:
	* 논문 ‘Visually Informed Binaural Audio Generation without Binaural Audios’: FAIR-play 데이터셋을 Scene Similarity에 따라 Clustering하는 방식으로 이 Bias를 줄이는 것을 시도했음.
	* External Source에서부터 Synthetic Stereophonic Data로 학습하는 것이 Overfitting을 줄일 수 있음.
* 문제는, 이런 방식들이 새로운 Single-Source Audio Data에 의존하는 방식이기 때문에, Extra Cost 발생, Complexity 증가.
	* + 데이터 안에 존재하는 Spatial, Temporal Information을 Under-Utilize → 더 좋은 결과를 얻을 기회를 놓치게 됨.

우리가 해결하고자 하는 것
1. Cross-Modal Alignment의 Enhancement,
2. 제공된 Spatial Information에 따라 Generation process를 Adjust 할 수 있는 능력,
	→ ‘Conditional Normalization Layers’ 소개
	→ Novel Audio-Visual Contrastive Learning Method 소개
		Anchor Frame, 근처 Frame, 그리고 Spatial하게 Shuffle된 Anchor Frame에서 Feature Discrimination을 강제
		→ 같은 물체인데, 다른 장소에 있을 때 소리가 어떻게 달라지는지를 학습할 수 있다.
		ex. 피아노의 장소가 달라지면, 소리가 어떻게 달라지는지를 제대로 학습함.
3. Robust하고 Cost-Effective한 Inference.
	→ Test-time Dynamic Scene Simulation(TDSS) 소개
		Sliding Window 방식에서의 Frame Redundancy(반복)을 사용 → Consecutive Frame에서 Five-Crop 이미지 사용 → Robust, Accuracy 증가

## Model 수정

Ego2Ego
* masked_clip: CLIP Feature에다가 Masked Pooling 돌린 거
* masked_da3: DA3 Feature에다가 Masked Pooling 돌린 거

수정한 것들 정리

1. Inference Input
	* 원래: **target mono audio**, visual frame, mask
		* 애초에 Task가 Mono-to-Binaural Generation이기 때문에, Mono Audio가 Target임.
	* Ego2Ego: Source Mono Audio + Source Visual Frame + Dominant Speaker Label
	* revised: **source mono audio**, source visual frame
2. Conditioning
	* 원래: Visual Frame의 RGB Frame, Segmentation Mask, Optical Flow 등.
	* revised: 어떤 Condition을 넣을까?
		* masked_clip only
		* masked_da3 only
		* masked_clip + masked_da3
		* none

![Image Description](/images/CleanShot%202026-06-11%20at%2021.52.24.png)

3. Representation of Audio
	* 원래: Complex Mono STFT
		* 문제는, 우리 Input Audio는 Binaural → Mono STFT로 표현이 안 됨.
		* 그리고, 사실은 **CCStereo에서도 mid/side STFT를 사용하긴 했음**.
			* input: $a_{i,t}^{M}$ = L+R
			* output: $\hat{a}_{i, t}^{D}$ = L-R 
	* Ego2Ego: left Log Mag, right Log Mag, cos(IPD), sin(IPD)
	* revised: mid/side complex STFT
		* $$M_{src}=\frac{L_{src}+R_{src}}{2} \qquad S_{src}=\frac{L_{src}-R_{src}}{2}$$
		* input_spec_src = [real(Msrc), imag(Msrc), real(Ssrc), imag(Ssrc)]

4. Loss Function
	* 원래(CCStereo): MSE, Spectral Amplitude, Waveform Phase, (optional SSL)
```python
mse_loss = MSE(pred_diff_spec, gt_diff_spec)
amp_loss = spec_amp_loss(pred_diff_spec, gt_diff_spec) * 0.005
fakes = diff_to_stereo(audio_mono, pred_diff_spec)
phase_wav_loss = PhaseLoss(real_stereo, fake_stereo)
ssl_loss = output["ssl_loss"] * 0.1

loss = mse_loss + amp_loss + phase_wav_loss + ssl_loss
```
* Loss Function 분석
	* 우리가 만드는 거: Complex Difference Spectrogram(CDS)
		* Given: Mono(L+R)
		* Get: Diff(L-R)
		* model input: STFT(mono)
		* model output: STFT(diff_pred) → Complex Difference Spectrogram(CDS)
		* target: STFT(diff_gt)
	* 이후, 최종적으로 나오는 결과물을 복원
		* L_pred = (mono+diff_pred)/2
		* R_pred = (mono-diff_pred)/2
	* 1. MSE Loss (MSE)
		* pred_diff_spec, gt_diff_spec간의 MSE
	* 2. Spectral Amplitude Loss (APM)
		* |STFT(pred)|, |STFT(target)|간의 MAE
	* 3. Waveform Phase Loss (PHS)
		* phase = angle(STFT(waveform)) → Complex STFT bins의 angle 비교
			* 일단 Waveform으로 복원한 후,
			* Pred의 Phase와 GT phase 비교
	* 4. Self-Supervised Learning Loss
		* 
* Our Loss Function

지금 현재 Representation:
	S = [mid_real, mid_imag, side_real, side_imag]
	S_src, S_pred, S_tgt
	S를 이용해 Stereo Waveform 복원 → x_pred, x_tgt
	Main Idea: S_pred = S_src * M_pred
		M_pred: predicted Complex Mask

1. MSE Loss: Complex STFT 사이의 MSE
	* `L_mse = mean((S_pred - S_tgt)^2)`
	* $\lambda = 1.0$
2. Amplitude Loss: Mid-Side 2개의 Magnitude 사이의 MAE
	* `|S_mid| = sqrt(mid_real^2 + mid_imag^2)`
	* `|S_side| = sqrt(side_real^2 + side_imag^2)`
	* `L_amp = mean(abs(|S_pred| - |S_tgt|))`
	* $\lambda = 0.005$
3. Waveform Phase Loss: Waveform으로 변환했을 때의 Phase 차이
	* `x_pred = ISTFT(S_pred)`
	* `x_tgt = target waveform`
	* `P_pred = angle(STFT(x_pred))`
	* `P_tgt = angle(STFT(x_tgt))`
	* `L_phase = mean(wrapped_abs(P_pred - P_tgt))`
		* `wrapped_abs(d) = pi - abs(abs(d) - pi)`
	* $\lambda = 1.0$
4. SSL Loss: 주변 Anchor Frame과의 Stability 차이
	* `z_anchor = fusion(audio, current_frame)`
	* `z_pos = fusion(audio, previous_frame)`
	* `z_neg = fusion(audio, shuffled_frame)`
	* `L_ssl = InfoNCE(z_anchor, z_pos, z_neg)`
	* $\lambda = 0.1$

비슷한 것들:

1. Visual Backbone: ResNet + DeepLabV3 Plus 사용중 (SAME)
2. Audio Network: U-Net + Transformer Fusion 사용중 (SAME)
3. Prediction Style: Complex Mask를 예측하고, input STFT에 넣자 (SAME)
4. Mask Range 동일
5. Loss: 4개 전부 사용중 (SAME)
6. Optimizer: Adam-style 사용중
7. Loss에서 사용하는 Multi-Frame Input (Self-Supervised Loss) 사용중 (SAME)
8. Learning Rate에서 사용하는 Polynomial Scheduler (사용중)
9. Hyperparameter 값도 동일.

변화시킨 것들:

1. Input Audio: mono(L+R) → source stereo mid/side (Task 차이)
2. Target: diff(L-R) → target stereo mid/side (Task 차이)
3. Output: 2-channel complex diff STFT → 4-channel complex target mid/side STFT (Task 차이)
4. Reconstruction: mono+diff = stereo → mid+side = stereo (Task 차이)
5. Dataset: FairPlay/YT-clean → EgoCom (Task 차이)
6. ! STFT Setting (EGOCOM 데이터의 크기가 달라서…) → 원본 따라가기
7. 

Output도 Mid-Side인 이유???
YTAUdio를 어떻게 처리하고 있는지?
	7sec to 0.7?
데이터셋 처리 => 동일하게 들고가야하는지?
1→2 / 1→3: Masked Dataset

1. ! **데이터로더 다시 Align하기** (원래 데이터셋, EgoCom 데이터셋의 차이)
	* 모델에서 제일 중요한 건 Dataset Alignment임! → 이 부분은 이전 Work까지 다 읽어봐야함.
		* 원래 Video/Audio가 어떤 Spec.을 가지고 있지?
			* 몇 초짜리 데이터인가?
			* 데이터에 어떤 특징이 있는가?
		* 이걸 이전 논문에서는 어떻게 처리했지?
			* Overlapping이나 Sampling을 사용한 부분이 있는가?
			* 
2. Mask를 넣어야 함 (왜? 여러 명의 사람이 있을 때 )


데이터로더… 이 부분은 다시.
1. 다른 데이터셋을 어떻게 맞출까

Visual Masking → Manifest (4초, 22,000)
	근데, manifest는 6초→3초, offset을 줬었음.
	(데이터셋)
	

Mask
	사진 안에서 Mask를 씌우고,




* Revised(CCStereo_revised): 

## 용준님께 Confirm 받아야할 사항들

1. 모델에 Condition을 넣는 과정에서, 다른 모델들은 BinauralGrad를 제외하면 전부 다 CLIP Feature만 넣고, DA3에서 나온 Geometric Feature는 넣지 않았었는데, CCStereo 모델도 마찬가지고 CLIP Feature만 넣을까요?
	* 논문에서 Geometric Feature를 넣는지를 봤는데, ‘Patch Shuffling된 사진으로 Contrastive Learning을 진행하는 과정에서 스스로 Condition과 Geometric한 정보를 학습한다’ 라고 되어있는데, 직접 Feature를 넣는 것보다는 확실히 학습 효과가 미비할 것 같아서 넣을지 고민입니다.
	* 일단은 Flag를 넣는 것으로 처리했습니다.
		* --egocom_condition_mode none          # no CLIP, no DA3
		* --egocom_condition_mode semantic      # masked_clip only
		* --egocom_condition_mode semantic_geo  # masked_clip + masked_da3
	* ! **최대한 원래 모델과 비슷하게. 그래서 그냥 아예 안 넣는 방향으로.**
2. Audio Representation을 어떻게 바꿀지 고민입니다.
	* 원래 Ego2Ego 모델은 [Lmag, Rmag, cos(IPD), sin(IPD)]를 사용해서 Complex STFT를 Mag/Phase 정보로 분리하고 있습니다.
	* 그러나, 기존의 CCStereo 모델은 Mono → Binaural을 수행하므로, input이 mono라 Complex Mono STFT (Re, Im)을 사용하고 있습니다.
		* 근데, model의 input으로 $a_{i,t}^{M}$, 즉 Mono Audio (L+R)를 넣어서,
		* output으로 $\hat{a}_{i,t}^{D}$, 즉 Mono에다가 씌울 Complex Mask (L-R)를 내뱉기 때문에,
	* Binaural Audio를 Input으로 받는 CCStereo_revised 모델도 mid/side representation을 사용해보려고 합니다.
		* 즉, target mid/side의 complex mask를 예측해서 씌울 수 있는 Representation을 사용할 생각입니다.
	* ! **이것도 내가 구현한 대로 하면 될 듯. 최대한 원래 모델과 비슷하게.**

## 2026.06.14. Training 시작

구현한 거 전부 가지고 Training 시작함.

* Training Loss가 30~40 정도를 Oscillate하는 것을 보임 (Loss * 1000을 track하므로, 0.03 정도?)
* Validation Loss도 마찬가지, 29.63~29.65 정도를 왔다갔다함.
	* 좋은 모델이 아니라는 소리인 듯.
	* ? 물론 우리 모델과 Task가 다르기 때문에, 어쩔 수 없는 Bottleneck인 것 같기도.

### Loss Function Comparison

