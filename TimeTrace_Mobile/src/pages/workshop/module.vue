<template>
  <view class="module-page">
    <view class="ambient-background">
      <view class="orb orb-gold"></view>
      <view class="orb orb-champagne"></view>
    </view>

    <view class="nav-bar glass-nav">
      <view class="nav-back float-hover" @tap="goBack"><text class="back-arrow">←</text></view>
      <view class="nav-center">
        <text class="nav-title">{{ moduleConfig.name }}</text>
        <text class="nav-subtitle">{{ moduleConfig.subtitle }}</text>
      </view>
      <view class="nav-right"></view>
    </view>

    <scroll-view class="module-content" scroll-y enhanced :show-scrollbar="false" style="width: 100%;">
      
      <view class="image-section animate-fade-in-up" style="animation-delay: 0.1s;" v-if="moduleId !== 'voice'">
        
        <view v-if="!imageUrl" class="upload-area glass-panel float-hover" @tap="triggerUpload">
          <view class="upload-icon-wrap float-breathing"><text class="upload-icon">{{ moduleConfig.emoji }}</text></view>
          <text class="upload-text">点击上传影像</text>
          <text class="upload-hint">支持 JPG / PNG 格式</text>
        </view>

        <view v-else-if="!(moduleId === 'live_portrait' && resultUrl)" class="preview-area glass-panel">
          
          <!-- 修复结果 / 普通图片显示（有结果时始终显示，长按对比原图） -->
          <view v-if="resultUrl || moduleId !== 'dustless' || dustlessParams.repairMode !== 'manual'" class="single-image-wrap">
            <image class="main-image" :src="isHoldingCompare ? imageUrl : (resultUrl || imageUrl)" mode="aspectFit" />
            <view class="status-badge glass-panel-light">
              <text class="badge-dot" :class="{ 'dot-original': !resultUrl || isHoldingCompare }"></text>
              <text>{{ isHoldingCompare ? '原图' : (!resultUrl ? '原图就绪' : '修复后') }}</text>
            </view>
            
            <view v-if="isProcessing" class="processing-scanner-overlay">
              <view class="scanner-line"></view>
              <view class="progress-glass-capsule">
                <text class="loading-msg">{{ loadingMsg }}</text>
                <view class="progress-bar-wrap"><view class="progress-bar" :style="{ width: progress + '%' }"></view></view>
                <text class="progress-percent">{{ progress }}%</text>
              </view>
            </view>

            <view v-if="resultUrl && !isProcessing" class="compare-control">
              <view class="compare-btn float-hover" @touchstart.prevent="onHoldStart" @touchend.prevent="onHoldEnd" @touchcancel.prevent="onHoldEnd" @mousedown.prevent="onHoldStart" @mouseup.prevent="onHoldEnd" @mouseleave.prevent="onHoldEnd">
                <view class="compare-icon-wrap"><text class="c-icon">✨</text></view>
                <text class="compare-text">长按对比原图</text>
              </view>
            </view>

            <view v-if="!isProcessing && !resultUrl" class="re-upload-btn float-hover" @tap="triggerUpload">
              <text class="re-upload-text">重新选择</text>
            </view>
          </view>
          
          <!-- 手动修复模式：Canvas 涂抹（拂尘手动修复） -->
          <view
            class="canvas-wrap"
            v-if="moduleId === 'dustless' && dustlessParams.repairMode === 'manual' && !resultUrl"
            @touchmove.stop.prevent
          >
            <view class="canvas-zoom-indicator" v-if="canvasScale !== 1">{{ Math.round(canvasScale * 100) }}%</view>
            <!-- 可绘制区域：图片 + Canvas 叠加 -->
            <view class="canvas-draw-area">
              <image class="canvas-bg-image" :src="imageUrl" mode="aspectFit" />
              <!-- #ifdef H5 -->
              <canvas
                ref="repairCanvasRef"
                class="repair-canvas"
                @touchstart="onTouchStart"
                @touchmove="onTouchMove"
                @touchend="onTouchEnd"
              ></canvas>
              <!-- #endif -->
              <!-- #ifdef MP-WEIXIN -->
              <canvas
                type="2d"
                id="repairCanvas"
                canvas-id="repairCanvas"
                class="repair-canvas"
                disable-scroll="true"
                @touchstart="onTouchStart"
                @touchmove="onTouchMove"
                @touchend="onTouchEnd"
              ></canvas>
              <!-- #endif -->
            </view>
            <!-- 工具栏：独立于画布下方，不遮挡图片 -->
            <view class="canvas-toolbar">
              <text class="canvas-hint">🖌️ 涂抹需要修复的区域 · {{ brushMode === 'draw' ? '画笔' : '橡皮' }}模式</text>
              <view class="paint-tool-row">
                <view class="paint-tool-btn paint-mode-btn" @tap="toggleBrushMode">
                  <text>{{ brushMode === 'draw' ? '🖌️ 画笔' : '🧹 橡皮' }}</text>
                </view>
                <view class="paint-tool-btn paint-clear-btn" @tap="clearCanvas">
                  <text>清空涂抹</text>
                </view>
              </view>
              <view class="brush-size-control">
                <text class="brush-label">笔刷大小</text>
                <text class="brush-size-value">{{ brushSize }}px</text>
                <slider :value="brushSize" :min="5" :max="60" :step="1" activeColor="#D4AF37" backgroundColor="#E8DCC8" block-size="16" @change="brushSize = $event.detail.value" style="flex: 1; margin: 0 16rpx;" />
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 留音模块：处理中状态 -->
      <view v-if="moduleId === 'voice' && isProcessing" class="result-media-section animate-fade-in-up">
        <view class="voice-processing-card glass-panel">
          <view class="voice-progress-icon-wrap"><text class="voice-progress-icon">🎙️</text></view>
          <text class="loading-msg">{{ loadingMsg }}</text>
          <view class="progress-bar-wrap"><view class="progress-bar" :style="{ width: progress + '%' }"></view></view>
          <text class="progress-percent">{{ progress }}%</text>
        </view>
      </view>

      <!-- 留音模块：语音结果展示 -->
      <view v-if="moduleId === 'voice' && resultUrl" class="result-media-section animate-fade-in-up">
        <view class="audio-player-card glass-panel">
          <view class="audio-card-icon-wrap"><text class="audio-card-icon">🎵</text></view>
          <text class="audio-card-title">语音生成完成</text>
          <text class="audio-card-hint">点击播放试听</text>
          <!-- 音频播放器 -->
          <view class="audio-player-wrap">
            <view class="audio-controls">
              <view class="audio-btn float-hover" @tap="toggleAudioPlay">
                <text class="audio-btn-icon">{{ isAudioPlaying ? '⏸' : '▶' }}</text>
              </view>
              <view class="audio-progress-wrap">
                <slider :value="audioProgress" :max="100" :step="0.1" activeColor="#D4AF37" backgroundColor="#E8DCC8" block-size="16" @change="seekAudio" @changing="seekAudio" :disabled="!audioCtx" />
              </view>
              <text class="audio-time">{{ formatAudioTime(audioCurrentTime) }} / {{ formatAudioTime(audioDuration) }}</text>
            </view>
          </view>
        </view>
      </view>

      <view v-if="resultUrl && moduleId === 'live_portrait'" class="result-media-section animate-fade-in-up">
        <view class="video-player-card glass-panel"><video :src="resultUrl" class="result-video" controls :show-center-play-btn="true" /></view>
      </view>

      <view class="params-section glass-panel animate-fade-in-up" style="animation-delay: 0.2s;">
        <view class="params-header">
          <text class="params-title">参数配置</text>
          <view class="reset-btn float-hover" @tap="resetParams"><text class="reset-text">重置</text></view>
        </view>

        <template v-if="moduleId === 'dustless'">
          <view class="param-group">
            <text class="param-label">修复模式</text>
            <view class="mode-grid">
              <view v-for="mode in dustlessModes" :key="mode.value" class="mode-card" :class="{ active: dustlessParams.repairMode === mode.value }" @tap="dustlessParams.repairMode = mode.value">
                <text class="mode-icon">{{ mode.icon }}</text><text class="mode-name">{{ mode.name }}</text><text class="mode-desc">{{ mode.desc }}</text>
              </view>
            </view>
          </view>
          <view v-if="dustlessParams.repairMode !== 'denoise'" class="param-group">
            <view class="param-row"><text class="param-label">检测灵敏度</text><text class="param-value">{{ dustlessParams.detectThreshold }}</text></view>
            <slider :value="dustlessParams.detectThreshold" :min="0.1" :max="0.9" :step="0.1" activeColor="#D4AF37" backgroundColor="#E8DCC8" block-size="20" @change="dustlessParams.detectThreshold = $event.detail.value" />
            <view class="param-hints"><text>宽松</text><text>严格</text></view>
          </view>
          <view v-if="dustlessParams.repairMode !== 'denoise'" class="param-group">
            <view class="param-row"><text class="param-label">修复范围</text><text class="param-value">{{ dustlessParams.dilateLevel }}</text></view>
            <slider :value="dustlessParams.dilateLevel" :min="1" :max="10" :step="1" activeColor="#D4AF37" backgroundColor="#E8DCC8" block-size="20" @change="dustlessParams.dilateLevel = $event.detail.value" />
            <view class="param-hints"><text>精确</text><text>扩展</text></view>
          </view>
          <view v-if="dustlessParams.repairMode === 'denoise'" class="info-card info-blue">
            <text class="info-icon">✦</text>
            <view class="info-content"><text class="info-title">UHDM 降噪修复</text><text class="info-desc">专门去除摩尔纹、噪点和图像噪声</text></view>
          </view>
        </template>

        <template v-if="moduleId === 'liuguang'">
          <view class="param-group">
            <text class="param-label">文本指导 (可选)</text>
            <input class="param-input" v-model="liuguangParams.prompt" placeholder="例如: 日落、森林、复古街景..." placeholder-class="input-placeholder" />
          </view>
          <view class="param-group">
            <view class="param-row"><text class="param-label">色温</text><text class="param-value">{{ liuguangParams.warmth > 0 ? '+' : '' }}{{ liuguangParams.warmth }}</text></view>
            <slider :value="liuguangParams.warmth" :min="-1" :max="1" :step="0.1" activeColor="#D4AF37" backgroundColor="#E8DCC8" block-size="20" @change="liuguangParams.warmth = $event.detail.value" />
            <view class="param-hints"><text>冷色调</text><text>暖色调</text></view>
          </view>
          <view class="param-group">
            <view class="param-row"><text class="param-label">鲜艳度</text><text class="param-value">{{ liuguangParams.saturation }}</text></view>
            <slider :value="liuguangParams.saturation" :min="0.5" :max="1.5" :step="0.1" activeColor="#D4AF37" backgroundColor="#E8DCC8" block-size="20" @change="liuguangParams.saturation = $event.detail.value" />
            <view class="param-hints"><text>淡雅</text><text>浓郁</text></view>
          </view>
          <view class="param-group">
            <view class="param-row"><text class="param-label">对比度</text><text class="param-value">{{ liuguangParams.contrast }}</text></view>
            <slider :value="liuguangParams.contrast" :min="0.5" :max="2.0" :step="0.1" activeColor="#D4AF37" backgroundColor="#E8DCC8" block-size="20" @change="liuguangParams.contrast = $event.detail.value" />
            <view class="param-hints"><text>柔和</text><text>鲜明</text></view>
          </view>
          <view class="param-group">
            <view class="switch-row" @tap="liuguangParams.colorEnhance = !liuguangParams.colorEnhance">
              <view class="switch-info"><text class="param-label">智能光影增强</text><text class="switch-desc">自动修复过暗或对比度不足</text></view>
              <view class="switch-track" :class="{ active: liuguangParams.colorEnhance }"><view class="switch-thumb"></view></view>
            </view>
          </view>
          <view class="param-group">
            <text class="param-label">快速预设</text>
            <view class="preset-grid">
              <view v-for="preset in colorPresets" :key="preset.name" class="preset-card float-hover" :class="preset.class" @tap="applyColorPreset(preset)">
                <text class="preset-name">{{ preset.name }}</text>
              </view>
            </view>
          </view>
        </template>

        <template v-if="moduleId === 'qingying'">
          <view class="param-group">
            <view class="param-row-between"><text class="param-label">修复提示词</text><view class="text-btn float-hover" @tap="recognizeText"><text class="text-btn-label">识别文字</text></view></view>
            <textarea class="param-textarea" v-model="qingyingParams.prompt" placeholder="输入描述修复需求的提示词..." placeholder-class="input-placeholder" :maxlength="500" />
          </view>
          <view class="param-group">
            <text class="param-label">放大倍数</text>
            <view class="select-grid">
              <view v-for="opt in [{label:'1x',value:1},{label:'2x',value:2},{label:'4x',value:4},{label:'8x',value:8}]" :key="opt.value" class="select-card float-hover" :class="{ active: qingyingParams.upscale === opt.value }" @tap="qingyingParams.upscale = opt.value">
                <text class="select-label">{{ opt.label }}</text>
              </view>
            </view>
          </view>
          <view class="param-group">
            <view class="switch-row" @tap="qingyingParams.enhanceText = !qingyingParams.enhanceText">
              <view class="switch-info"><text class="param-label">增强文字清晰度</text></view>
              <view class="switch-track" :class="{ active: qingyingParams.enhanceText }"><view class="switch-thumb"></view></view>
            </view>
          </view>
          <view class="param-group">
            <view class="switch-row" @tap="qingyingParams.repairBackground = !qingyingParams.repairBackground">
              <view class="switch-info"><text class="param-label">修复背景细节</text></view>
              <view class="switch-track" :class="{ active: qingyingParams.repairBackground }"><view class="switch-thumb"></view></view>
            </view>
          </view>
          <view class="param-group">
            <view class="collapse-header" @tap="showAdvanced = !showAdvanced"><text class="param-label">高级参数</text><text class="collapse-arrow" :class="{ expanded: showAdvanced }">▼</text></view>
            <view v-if="showAdvanced" class="collapse-body">
              <view class="sub-param"><text class="sub-param-label">Patch大小</text><picker :range="[512,640,768,896,1024]" @change="qingyingParams.patchSize = [512,640,768,896,1024][$event.detail.value]"><view class="picker-value">{{ qingyingParams.patchSize }}px ▼</view></picker></view>
              <view class="sub-param"><text class="sub-param-label">Stride</text><picker :range="[256,320,384,448,512]" @change="qingyingParams.stride = [256,320,384,448,512][$event.detail.value]"><view class="picker-value">{{ qingyingParams.stride }}px ▼</view></picker></view>
              <view class="sub-param"><text class="sub-param-label">随机种子</text><view class="seed-row"><input class="seed-input" type="number" v-model="qingyingParams.seed" /><view class="seed-random-btn float-hover" @tap="qingyingParams.seed = Math.floor(Math.random() * 4294967296)"><text class="seed-random-text">随机</text></view></view></view>
            </view>
          </view>
        </template>

        <template v-if="moduleId === 'zhenrong'">
          <view class="param-group">
            <view class="param-row"><text class="param-label">面部增强程度</text><text class="param-value">{{ zhenrongParams.faceEnhanceLevel }}</text></view>
            <slider :value="zhenrongParams.faceEnhanceLevel" :min="1" :max="10" :step="1" activeColor="#D4AF37" backgroundColor="#E8DCC8" block-size="20" @change="zhenrongParams.faceEnhanceLevel = $event.detail.value" />
            <view class="param-hints"><text>轻微</text><text>强烈</text></view>
          </view>
          <view class="param-group">
            <view class="param-row"><text class="param-label">皮肤平滑度</text><text class="param-value">{{ zhenrongParams.skinSmooth }}%</text></view>
            <slider :value="zhenrongParams.skinSmooth" :min="0" :max="100" :step="5" activeColor="#D4AF37" backgroundColor="#E8DCC8" block-size="20" @change="zhenrongParams.skinSmooth = $event.detail.value" />
            <view class="param-hints"><text>自然</text><text>光滑</text></view>
          </view>
          <view class="param-group">
            <view class="switch-row" @tap="zhenrongParams.eyeEnhance = !zhenrongParams.eyeEnhance">
              <view class="switch-info"><text class="param-label">眼部增强</text><text class="switch-desc">增强眼睛清晰度和细节</text></view>
              <view class="switch-track" :class="{ active: zhenrongParams.eyeEnhance }"><view class="switch-thumb"></view></view>
            </view>
          </view>
          <view class="param-group">
            <view class="switch-row" @tap="zhenrongParams.lipEnhance = !zhenrongParams.lipEnhance">
              <view class="switch-info"><text class="param-label">唇部增强</text><text class="switch-desc">增强唇部色彩和细节</text></view>
              <view class="switch-track" :class="{ active: zhenrongParams.lipEnhance }"><view class="switch-thumb"></view></view>
            </view>
          </view>
        </template>

        <template v-if="moduleId === 'voice'">
          <view class="param-group">
            <text class="param-label">合成模式</text>
            <view class="mode-grid mode-grid-2">
              <view class="mode-card float-hover" :class="{ active: voiceParams.mode === 'tts' }" @tap="voiceParams.mode = 'tts'"><text class="mode-icon">📝</text><text class="mode-name">文本转语音</text></view>
              <view class="mode-card float-hover" :class="{ active: voiceParams.mode === 'clone' }" @tap="voiceParams.mode = 'clone'"><text class="mode-icon">🎙️</text><text class="mode-name">声音复活</text></view>
            </view>
          </view>
          <view v-if="voiceParams.mode === 'tts'" class="param-group">
            <text class="param-label">选择预设音色</text>
            <view class="voice-list">
              <view v-for="voice in voicePresets" :key="voice.id" class="voice-card float-hover" :class="{ active: voiceParams.voiceId === voice.id }" @tap="voiceParams.voiceId = voice.id">
                <view class="voice-icon-wrap" :class="voice.colorClass"><text class="voice-icon-text">{{ voice.icon }}</text></view>
                <view class="voice-info"><text class="voice-name">{{ voice.name }}</text><text class="voice-desc">{{ voice.desc }}</text></view>
                <view v-if="voiceParams.voiceId === voice.id" class="voice-check">✓</view>
              </view>
            </view>
          </view>
          <view v-if="voiceParams.mode === 'clone'" class="param-group">
            <text class="param-label">上传声音样本</text>
            <view v-if="!voiceRefFileName" class="audio-upload-area float-hover" @tap="triggerVoiceUpload">
              <text class="audio-upload-icon">📁</text><text class="audio-upload-text">点击上传录音文件</text><text class="audio-upload-hint">支持 MP3/WAV (3-10秒最佳)</text>
            </view>
            <view v-else class="audio-file-card">
              <text class="audio-file-icon">🎵</text><view class="audio-file-info"><text class="audio-file-name">{{ voiceRefFileName }}</text></view>
              <view class="audio-file-remove float-hover" @tap="removeVoiceRef"><text>✕</text></view>
            </view>
            <view style="margin-top: 24rpx;">
              <text class="param-label">参考样本内容</text>
              <textarea class="param-textarea" v-model="voiceParams.promptText" placeholder="请输入参考音频中实际说的话..." placeholder-class="input-placeholder" :maxlength="50" />
              <text class="char-count">{{ voiceParams.promptText.length }}/50</text>
            </view>
          </view>
          <view class="param-group">
            <text class="param-label">{{ voiceParams.mode === 'tts' ? '想说的话' : '复活台词' }}</text>
            <textarea class="param-textarea" v-model="voiceParams.text" :placeholder="voiceParams.mode === 'tts' ? '输入您想转换的文字...' : '输入您希望人物说出的话...'" placeholder-class="input-placeholder" :maxlength="300" />
            <text class="char-count">{{ voiceParams.text.length }}/300</text>
          </view>
          <view class="param-group">
            <view class="param-row"><text class="param-label">语速调整</text><text class="param-value">{{ voiceParams.rate > 0 ? '+' : '' }}{{ voiceParams.rate }}%</text></view>
            <slider :value="voiceParams.rate" :min="-50" :max="50" :step="10" activeColor="#D4AF37" backgroundColor="#E8DCC8" block-size="20" @change="voiceParams.rate = $event.detail.value" />
            <view class="param-hints"><text>慢速</text><text>标准</text><text>快速</text></view>
          </view>
        </template>

        <template v-if="moduleId === 'live_portrait'">
          <view class="param-group">
            <text class="param-label">驱动视频 (可选)</text>
            <view v-if="!drivingVideoName" class="audio-upload-area float-hover" @tap="triggerVideoUpload">
              <text class="audio-upload-icon">🎬</text><text class="audio-upload-text">点击上传驱动视频</text><text class="audio-upload-hint">视频将驱动人像动作</text>
            </view>
            <view v-else class="audio-file-card">
              <text class="audio-file-icon">🎬</text><view class="audio-file-info"><text class="audio-file-name">{{ drivingVideoName }}</text></view>
              <view class="audio-file-remove float-hover" @tap="removeDrivingVideo"><text>✕</text></view>
            </view>
          </view>
          <view class="param-group">
            <text class="param-label">驱动音频</text>
            <view v-if="!drivingAudioName" class="audio-upload-area float-hover" @tap="triggerAudioUpload">
              <text class="audio-upload-icon">🎤</text><text class="audio-upload-text">点击上传驱动音频</text><text class="audio-upload-hint">音频将驱动人像说话</text>
            </view>
            <view v-else class="audio-file-card">
              <text class="audio-file-icon">🎵</text><view class="audio-file-info"><text class="audio-file-name">{{ drivingAudioName }}</text></view>
              <view class="audio-file-remove float-hover" @tap="removeDrivingAudio"><text>✕</text></view>
            </view>
          </view>
          <view class="param-group">
            <view class="param-row"><text class="param-label">表情幅度</text><text class="param-value">x{{ livePortraitParams.expressionScale.toFixed(1) }}</text></view>
            <slider :value="livePortraitParams.expressionScale" :min="0.5" :max="1.5" :step="0.1" activeColor="#D4AF37" backgroundColor="#E8DCC8" block-size="20" @change="livePortraitParams.expressionScale = $event.detail.value" />
            <view class="param-hints"><text>克制</text><text>自然</text><text>夸张</text></view>
          </view>
          <view class="param-group">
            <view class="switch-row" @tap="livePortraitParams.relativeMotion = !livePortraitParams.relativeMotion">
              <view class="switch-info"><text class="param-label">相对运动</text><text class="switch-desc">保留原图头部姿态</text></view>
              <view class="switch-track" :class="{ active: livePortraitParams.relativeMotion }"><view class="switch-thumb"></view></view>
            </view>
          </view>
          <view class="param-group">
            <view class="switch-row" @tap="livePortraitParams.pasteBack = !livePortraitParams.pasteBack">
              <view class="switch-info"><text class="param-label">背景保护</text><text class="switch-desc">防止背景扭曲</text></view>
              <view class="switch-track" :class="{ active: livePortraitParams.pasteBack }"><view class="switch-thumb"></view></view>
            </view>
          </view>
        </template>

        <template v-if="moduleId === 'time_engine'">
          <view class="info-card info-gold">
            <text class="info-icon">✦</text>
            <view class="info-content"><text class="info-title">Flux.1 Pro 核心引擎</text><text class="info-desc">基于ComfyUI节点工作流，AI智能多维度修复</text></view>
          </view>
          <view class="flow-steps">
            <view class="flow-step"><view class="step-dot active"></view><view class="step-line"></view><view class="step-content"><text class="step-title">影像解析</text><text class="step-desc">噪点特征提取 / 结构重组</text></view></view>
            <view class="flow-step"><view class="step-dot"></view><view class="step-line"></view><view class="step-content"><text class="step-title">Flux 核心引擎</text><text class="step-desc">潜空间重绘 (Strength: 0.85)</text></view></view>
            <view class="flow-step"><view class="step-dot"></view><view class="step-content"><text class="step-title">面部/细节强化</text><text class="step-desc">Adetailer 局部修复技术</text></view></view>
          </view>
        </template>
      </view>

      <view class="action-section animate-fade-in-up" style="animation-delay: 0.3s;">
        <view class="start-btn" :class="{ disabled: !canStartRepair || isProcessing }" @tap="startRepair">
          <view v-if="canStartRepair && !isProcessing" class="shimmer-effect"></view>
          <text class="start-btn-text">{{ startBtnText }}</text>
        </view>

        <view v-if="resultUrl && !isProcessing" class="result-actions">
          <view class="action-btn action-download float-hover" @tap="downloadResult"><text class="action-icon">⬇</text><text class="action-label">保存</text></view>
          <view class="action-btn action-continue float-hover" @tap="continueRepair"><text class="action-icon">↻</text><text class="action-label">继续修复</text></view>
          <view class="action-btn action-reset float-hover" @tap="resetAll"><text class="action-icon">✕</text><text class="action-label">重新开始</text></view>
        </view>
      </view>

      <view class="tips-section animate-fade-in-up" style="animation-delay: 0.4s;">
        <view class="tips-card glass-panel-light"><text class="tips-title">使用说明</text><text class="tips-item">{{ moduleConfig.tips }}</text></view>
      </view>
      
      <view style="height: 120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { uploadFile, post, get, voiceGenerate, getToken } from '@/utils/request'

const moduleId = ref('')
const imageUrl = ref('')
const imageFilePath = ref('')
const imagePhotoId = ref<number | null>(null)
const resultUrl = ref('')
const isProcessing = ref(false)
const loadingMsg = ref('正在修复中...')
const progress = ref(0)
const showAdvanced = ref(false)

// 核心按压状态
const isHoldingCompare = ref(false)

const onHoldStart = () => { if(resultUrl.value && !isProcessing.value) isHoldingCompare.value = true }
const onHoldEnd = () => { isHoldingCompare.value = false }

// ====================================================================
// 音频播放器状态与方法（留音模块）
// ====================================================================
const audioCtx = ref<any>(null)
const isAudioPlaying = ref(false)
const audioProgress = ref(0)
const audioCurrentTime = ref(0)
const audioDuration = ref(0)
let _audioTimer: any = null

const initAudio = () => {
  destroyAudio()
  if (!resultUrl.value) return
  audioCtx.value = uni.createInnerAudioContext()
  audioCtx.value.src = resultUrl.value
  audioCtx.value.onPlay(() => { isAudioPlaying.value = true; startAudioTimer() })
  audioCtx.value.onPause(() => { isAudioPlaying.value = false; stopAudioTimer() })
  audioCtx.value.onStop(() => { isAudioPlaying.value = false; stopAudioTimer(); audioProgress.value = 0; audioCurrentTime.value = 0 })
  audioCtx.value.onEnded(() => { isAudioPlaying.value = false; stopAudioTimer(); audioProgress.value = 100; audioCurrentTime.value = audioDuration.value })
  audioCtx.value.onError((e: any) => { console.error('音频播放错误:', e); isAudioPlaying.value = false; stopAudioTimer() })
  audioCtx.value.onCanplay(() => {
    // uni-app createInnerAudioContext 的 duration 需要 play 后才能获取
  })
}

const startAudioTimer = () => {
  stopAudioTimer()
  _audioTimer = setInterval(() => {
    if (audioCtx.value) {
      audioCurrentTime.value = audioCtx.value.currentTime || 0
      audioDuration.value = audioCtx.value.duration || 0
      if (audioDuration.value > 0) {
        audioProgress.value = Math.round((audioCurrentTime.value / audioDuration.value) * 10000) / 100
      }
    }
  }, 250)
}

const stopAudioTimer = () => { if (_audioTimer) { clearInterval(_audioTimer); _audioTimer = null } }

const toggleAudioPlay = () => {
  if (!audioCtx.value) initAudio()
  if (audioCtx.value) {
    if (isAudioPlaying.value) { audioCtx.value.pause() }
    else { audioCtx.value.play() }
  }
}

const seekAudio = (e: any) => {
  if (!audioCtx.value) return
  const pos = (e.detail.value / 100) * audioDuration.value
  audioCtx.value.seek(pos)
  audioCurrentTime.value = pos
  audioProgress.value = e.detail.value
}

const destroyAudio = () => {
  stopAudioTimer()
  if (audioCtx.value) { audioCtx.value.destroy(); audioCtx.value = null }
  isAudioPlaying.value = false; audioProgress.value = 0; audioCurrentTime.value = 0; audioDuration.value = 0
}

const formatAudioTime = (t: number) => {
  if (!t || !isFinite(t)) return '0:00'
  const m = Math.floor(t / 60); const s = Math.floor(t % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

// ====================================================================
// Canvas 手动涂抹相关 (拂尘手动修复) —— 模板级条件编译双端兼容
// H5：模板用 <canvas ref="repairCanvasRef">，通过 Vue ref 获取原生 HTMLCanvasElement
// 小程序：模板用 <canvas type="2d" id="repairCanvas" canvas-id="repairCanvas">
//        通过 createSelectorQuery .fields({node:true}) 获取节点
// 坐标：小程序用 touch.x/y，H5 用 clientX/Y - canvasRect
// ====================================================================
const brushSize = ref(20)
const brushMode = ref<'draw' | 'erase'>('draw')
const canvasScale = ref(1)
const isPainting = ref(false)
const hasStrokes = ref(false)

// #ifdef H5
const repairCanvasRef = ref<HTMLCanvasElement | null>(null)
// #endif

let canvasNode: any = null
let ctx: any = null
let lastX = 0
let lastY = 0
let canvasRect = { left: 0, top: 0, width: 0, height: 0 }

// 跨端坐标获取
const getTouchPos = (e: any) => {
  const touch = e.touches[0]
  // #ifdef MP-WEIXIN
  if (touch.x !== undefined && touch.y !== undefined) {
    return { x: touch.x, y: touch.y }
  }
  // #endif
  return { x: touch.clientX - canvasRect.left, y: touch.clientY - canvasRect.top }
}

// 初始化画布 (双端完全独立实现)
const initCanvas = () => {
  hasStrokes.value = false

  // ===== H5：Vue ref 直接拿原生 Canvas =====
  // #ifdef H5
  const doInitH5 = () => {
    const cvs = repairCanvasRef.value
    if (!cvs) { setTimeout(doInitH5, 100); return }
    const rect = cvs.getBoundingClientRect()
    if (rect.width === 0) { setTimeout(doInitH5, 200); return }
    canvasRect = { left: rect.left, top: rect.top, width: rect.width, height: rect.height }
    const dpr = uni.getSystemInfoSync().pixelRatio
    cvs.width = canvasRect.width * dpr
    cvs.height = canvasRect.height * dpr
    canvasNode = cvs
    ctx = cvs.getContext('2d')
    if (ctx) { ctx.scale(dpr, dpr); ctx.clearRect(0, 0, canvasRect.width, canvasRect.height) }
  }
  setTimeout(doInitH5, 50)
  // #endif

  // ===== 小程序：createSelectorQuery 拿 type="2d" 节点 =====
  // #ifdef MP-WEIXIN
  setTimeout(() => {
    const query = uni.createSelectorQuery()
    query.select('#repairCanvas')
      .fields({ node: true, size: true, rect: true })
      .exec((res) => {
        if (!res[0] || !res[0].node) return
        canvasRect = { left: res[0].left, top: res[0].top, width: res[0].width, height: res[0].height }
        const dpr = uni.getSystemInfoSync().pixelRatio
        canvasNode = res[0].node
        ctx = canvasNode.getContext('2d')
        canvasNode.width = canvasRect.width * dpr
        canvasNode.height = canvasRect.height * dpr
        ctx.scale(dpr, dpr)
        ctx.clearRect(0, 0, canvasRect.width, canvasRect.height)
      })
  }, 150)
  // #endif
}

// 触摸开始（落笔）—— ctx 为空时自动触发初始化
const onTouchStart = (e: any) => {
  if (!ctx) { initCanvas(); return }
  isPainting.value = true
  const pos = getTouchPos(e)
  lastX = pos.x; lastY = pos.y
  ctx.lineWidth = brushSize.value
  ctx.lineCap = 'round'; ctx.lineJoin = 'round'
  ctx.globalCompositeOperation = brushMode.value === 'draw' ? 'source-over' : 'destination-out'
  ctx.strokeStyle = 'rgba(255, 107, 53, 0.7)'
  ctx.beginPath(); ctx.moveTo(lastX, lastY); ctx.lineTo(lastX, lastY)
  ctx.stroke()
}

// 触摸移动（拖拽）
const onTouchMove = (e: any) => {
  if (!isPainting.value || !ctx) return
  const pos = getTouchPos(e)
  ctx.beginPath(); ctx.moveTo(lastX, lastY); ctx.lineTo(pos.x, pos.y)
  ctx.stroke()
  lastX = pos.x; lastY = pos.y; hasStrokes.value = true
}

// 触摸结束（抬手）
const onTouchEnd = () => { isPainting.value = false }

// 切换画笔 / 橡皮模式
const toggleBrushMode = () => { brushMode.value = brushMode.value === 'draw' ? 'erase' : 'draw' }

// 清空涂抹区域
const clearCanvas = () => {
  hasStrokes.value = false
  if (!ctx || !canvasNode) return
  // #ifdef H5
  const cvs = repairCanvasRef.value
  if (cvs) { const r = cvs.getBoundingClientRect(); ctx.clearRect(0, 0, r.width, r.height) }
  // #endif
  // #ifdef MP-WEIXIN
  uni.createSelectorQuery().select('#repairCanvas').boundingClientRect((r: any) => {
    if (r) ctx.clearRect(0, 0, r.width, r.height)
  }).exec()
  // #endif
  uni.showToast({ title: '已清空涂抹', icon: 'none', duration: 1000 })
}

// 导出遮罩图 (双端兼容)
const exportMask = (): Promise<string> => {
  return new Promise((resolve, reject) => {
    if (!canvasNode) return reject(new Error('画布未初始化'))
    // #ifdef MP-WEIXIN
    uni.canvasToTempFilePath({ canvas: canvasNode, fileType: 'png', success: (res: any) => resolve(res.tempFilePath), fail: reject })
    // #endif
    // #ifdef H5
    try { resolve((canvasNode as HTMLCanvasElement).toDataURL('image/png')) } catch (err) { reject(err) }
    // #endif
  })
}

const moduleConfigs: Record<string, any> = {
  dustless: { name: '拂尘修复', subtitle: '去除划痕污渍', emoji: '✨', tips: '自动修复：系统智能检测并修复疤痕；手动修复：涂抹需要修复的区域；降噪修复：去除摩尔纹和噪点' },
  liuguang: { name: '流光上色', subtitle: '黑白照片上色', emoji: '🎨', tips: '支持文本指导上色方向，可调节色温、鲜艳度和对比度，也可使用快速预设方案' },
  qingying: { name: '清影清晰', subtitle: '提升照片清晰度', emoji: '🔍', tips: '支持1-8倍放大，可使用提示词引导修复方向，高级参数可调节Patch大小和Stride' },
  zhenrong: { name: '真容精修', subtitle: '精修面部细节', emoji: '👤', tips: '增强面部清晰度，平滑皮肤纹理，可选增强眼部和唇部细节' },
  voice: { name: '留音', subtitle: '语音合成与克隆', emoji: '🎙️', tips: '文本转语音：选择预设音色合成语音；声音复活：上传声音样本克隆音色' },
  live_portrait: { name: '灵动人像', subtitle: '人像动态复活', emoji: '🎬', tips: '上传驱动音频或视频，让静态人像动起来，可调节表情幅度和背景保护' },
  time_engine: { name: '时光引擎', subtitle: 'AI一键重塑', emoji: '✦', tips: '基于Flux.1 Pro的AI一键修复，自动进行影像解析、核心引擎重绘和面部强化' }
}
const moduleConfig = computed(() => moduleConfigs[moduleId.value] || moduleConfigs.dustless)

// 各模块参数 (全部保持原有变量名称与初始值)
const dustlessParams = ref({ repairMode: 'auto' as 'auto' | 'manual' | 'denoise', detectThreshold: 0.5, dilateLevel: 3 })
const dustlessModes = [
  { value: 'auto', name: '自动修复', icon: '✨', desc: '智能检测并修复瑕疵' },
  { value: 'manual', name: '手动修复', icon: '🖌️', desc: '涂抹需要修复的区域' },
  { value: 'denoise', name: '降噪修复', icon: '🔇', desc: '去除摩尔纹和噪点' }
]

const liuguangParams = ref({ modelSize: 'advanced', model: 'advanced', inputSize: 512, colorEnhance: true, prompt: '', warmth: 0.0, saturation: 1.0, contrast: 1.0, enhance_only: false })
const colorPresets = [
  { name: '自然', warmth: 0.0, saturation: 1.0, contrast: 1.0, class: 'preset-natural' },
  { name: '鲜艳', warmth: 0.2, saturation: 1.3, contrast: 1.1, class: 'preset-vivid' },
  { name: '温暖', warmth: 0.6, saturation: 1.2, contrast: 1.0, class: 'preset-warm' },
  { name: '冷调', warmth: -0.4, saturation: 0.9, contrast: 1.1, class: 'preset-cool' },
  { name: '复古', warmth: 0.3, saturation: 0.8, contrast: 1.2, class: 'preset-retro' },
  { name: '电影', warmth: 0.1, saturation: 1.1, contrast: 1.3, class: 'preset-cinema' }
]

const qingyingParams = ref({ prompt: '', upscale: 2, patchSize: 512, stride: 256, seed: 42, enhanceText: false, repairBackground: false })
const zhenrongParams = ref({ faceEnhanceLevel: 5, skinSmooth: 50, eyeEnhance: true, lipEnhance: false })
const voiceParams = ref({ mode: 'tts' as 'tts' | 'clone', text: '', voiceId: 'female1', promptText: '', pitch: 0, rate: 0 })
const voiceRefFileName = ref('')
const voiceRefFilePath = ref('')
const voicePresets = [
  { id: 'male1', name: '男一 · 沉稳磁性', icon: '👔', desc: '中气十足，略带播音腔', colorClass: 'voice-blue' },
  { id: 'male2', name: '男二 · 温和亲切', icon: '🧑', desc: '温和亲切，充满亲和力', colorClass: 'voice-indigo' },
  { id: 'female1', name: '女一 · 温柔细腻', icon: '👩', desc: '温柔细腻，清晰知性', colorClass: 'voice-pink' },
  { id: 'female2', name: '女二 · 温暖关怀', icon: '👩‍🦰', desc: '温暖关怀，充满关爱', colorClass: 'voice-rose' },
  { id: 'narrator', name: '讲述者 · 标准播音', icon: '🎤', desc: '普通话标准，适合旁白', colorClass: 'voice-purple' }
]

const livePortraitParams = ref({ drivingAudio: null as any, drivingVideo: null as any, relativeMotion: true, pasteBack: true, expressionScale: 1.0 })
const drivingAudioName = ref('')
const drivingAudioPath = ref('')
const drivingAudioFile = ref<File | null>(null)
const drivingVideoName = ref('')
const drivingVideoPath = ref('')
const drivingVideoFile = ref<File | null>(null)

const canStartRepair = computed(() => {
  if (isProcessing.value) return false
  if (moduleId.value === 'voice') return !!voiceParams.value.text
  if (moduleId.value === 'live_portrait') return !!(imageUrl.value || imagePhotoId.value) && !!(drivingAudioPath.value || drivingAudioFile.value) && !!(drivingVideoPath.value || drivingVideoFile.value)
  // 手动修复模式：必须有图片 + 已绘制涂抹区域
  if (moduleId.value === 'dustless' && dustlessParams.value.repairMode === 'manual') return !!(imageUrl.value || imagePhotoId.value) && hasStrokes.value
  return !!(imageUrl.value || imagePhotoId.value)
})

const startBtnText = computed(() => {
  if (isProcessing.value) return 'AI 引擎运转中...'
  if (moduleId.value === 'dustless' && dustlessParams.value.repairMode === 'manual' && !hasStrokes.value && (imageUrl.value || imagePhotoId.value)) return '请先涂抹修复区域'
  return '开始修复'
})

onMounted(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  const options = currentPage.options || currentPage.$page?.options || {}
  moduleId.value = options.id || 'dustless'

  // 从创作时光轴跳转：通过 history_id 加载历史修复结果
  if (options.history_id) {
    loadHistoryData(parseInt(options.history_id))
  } else {
    if (options.imageUrl) imageUrl.value = decodeURIComponent(options.imageUrl)
    if (options.photoId) imagePhotoId.value = parseInt(options.photoId)
  }
})

// 加载历史记录数据（从创作时光轴跳转时），直接显示修复成功的结果页
const loadHistoryData = async (historyId: number) => {
  try {
    // 先尝试直接获取单条历史记录
    const record = await get<any>(`/workshop/histories/${historyId}`)
    if (record) {
      imageUrl.value = getFullUrl(record.input_path)
      resultUrl.value = getFullUrl(record.result_path)
      return
    }
  } catch (_) { /* fallback to list */ }

  // 降级：从列表中查找
  try {
    const data = await get<any[]>('/workshop/histories', { skip: 0, limit: 200 })
    if (!Array.isArray(data)) return
    const target = data.find((h: any) => h.id === historyId)
    if (target) {
      imageUrl.value = getFullUrl(target.input_path)
      resultUrl.value = getFullUrl(target.result_path)
    }
  } catch (e) {
    console.error('加载历史记录失败', e)
  }
}

const goBack = () => { uni.navigateBack() }

const triggerUpload = () => {
  if (isProcessing.value) return
  uni.chooseImage({ count: 1, sizeType: ['compressed'], sourceType: ['album', 'camera'],
    success: (res) => { imageFilePath.value = res.tempFilePaths[0]; imageUrl.value = res.tempFilePaths[0]; resultUrl.value = ''; imagePhotoId.value = null; isHoldingCompare.value = false; }
  })
}

const triggerVoiceUpload = () => {
  // H5 环境：使用 DOM file input
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'audio/*'
  input.onchange = (e: any) => {
    const file = e.target?.files?.[0]
    if (file) {
      voiceRefFileName.value = file.name
      voiceRefFilePath.value = URL.createObjectURL(file)
    }
  }
  input.click()
}
const removeVoiceRef = () => { voiceRefFileName.value = ''; voiceRefFilePath.value = '' }
const triggerAudioUpload = () => {
  // H5 环境：使用 DOM file input（uni.chooseMessageFile 在 H5 不可用）
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'audio/*'
  input.onchange = (e: any) => {
    const file = e.target?.files?.[0]
    if (file) {
      drivingAudioFile.value = file
      drivingAudioName.value = file.name
      drivingAudioPath.value = URL.createObjectURL(file)
    }
  }
  input.click()
}
const triggerVideoUpload = () => {
  // H5 环境：先尝试 uni.chooseVideo，失败则使用 DOM input
  uni.chooseVideo({ sourceType: ['album', 'camera'], maxDuration: 60,
    success: (res) => {
      drivingVideoPath.value = res.tempFilePath
      drivingVideoName.value = '驱动视频.mp4'
      drivingVideoFile.value = null  // uni 路径无法直接作为 File
    },
    fail: () => {
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = 'video/*'
      input.onchange = (e: any) => {
        const file = e.target?.files?.[0]
        if (file) {
          drivingVideoFile.value = file
          drivingVideoName.value = file.name
          drivingVideoPath.value = URL.createObjectURL(file)
        }
      }
      input.click()
    }
  })
}
const removeDrivingAudio = () => { drivingAudioName.value = ''; drivingAudioPath.value = ''; drivingAudioFile.value = null }
const removeDrivingVideo = () => { drivingVideoName.value = ''; drivingVideoPath.value = ''; drivingVideoFile.value = null }
const applyColorPreset = (preset: any) => { liuguangParams.value.warmth = preset.warmth; liuguangParams.value.saturation = preset.saturation; liuguangParams.value.contrast = preset.contrast }

const recognizeText = async () => {
  if (!imagePhotoId.value) { uni.showToast({ title: '请先从图库选择图片', icon: 'none' }); return }
  try {
    uni.showLoading({ title: '识别中...' })
    const res = await post('/workshop/recognize-text', { photo_id: imagePhotoId.value })
    uni.hideLoading()
    if (res && (res as any).text) { qingyingParams.value.prompt = (res as any).text; uni.showToast({ title: '识别成功', icon: 'success' }) }
  } catch (e) { uni.hideLoading(); uni.showToast({ title: '识别失败', icon: 'none' }) }
}

// 监听修复模式变化，切换到手动模式时初始化 Canvas
watch(() => dustlessParams.value.repairMode, (newMode) => {
  if (newMode === 'manual' && imageUrl.value) {
    setTimeout(() => initCanvas(), 50)
  }
})

// 监听图片 URL 变化
watch(imageUrl, (newUrl) => {
  if (newUrl && dustlessParams.value.repairMode === 'manual') {
    setTimeout(() => initCanvas(), 50)
  }
})

const resetParams = () => {
  if (moduleId.value === 'dustless') { dustlessParams.value = { repairMode: 'auto', detectThreshold: 0.5, dilateLevel: 3 }; brushMode.value = 'draw'; clearCanvas(); canvasScale.value = 1 }
  else if (moduleId.value === 'liuguang') liuguangParams.value = { modelSize: 'advanced', model: 'advanced', inputSize: 512, colorEnhance: true, prompt: '', warmth: 0.0, saturation: 1.0, contrast: 1.0, enhance_only: false }
  else if (moduleId.value === 'qingying') qingyingParams.value = { prompt: '', upscale: 2, patchSize: 512, stride: 256, seed: 42, enhanceText: false, repairBackground: false }
  else if (moduleId.value === 'zhenrong') zhenrongParams.value = { faceEnhanceLevel: 5, skinSmooth: 50, eyeEnhance: true, lipEnhance: false }
  else if (moduleId.value === 'voice') voiceParams.value = { mode: 'tts', text: '', voiceId: 'female1', promptText: '', pitch: 0, rate: 0 }
  else if (moduleId.value === 'live_portrait') livePortraitParams.value = { drivingAudio: null, drivingVideo: null, relativeMotion: true, pasteBack: true, expressionScale: 1.0 }
}

const startRepair = async () => {
  if (!canStartRepair.value || isProcessing.value) return
  isProcessing.value = true; progress.value = 0; resultUrl.value = ''; isHoldingCompare.value = false
  loadingMsg.value = '正在处理中...'
  try {
    if (moduleId.value === 'time_engine') { await handleTimeEngine(); return }
    if (moduleId.value === 'live_portrait') { await handleLivePortrait(); return }
    if (moduleId.value === 'voice') { await handleVoice(); return }
    await handleImageRepair()
  } catch (e: any) { isProcessing.value = false; uni.showToast({ title: e.message || '修复失败', icon: 'none' }) }
}

const handleImageRepair = async () => {
  loadingMsg.value = '正在提交修复任务...'
  let params: Record<string, any> | null = null
  let repairMode = 'auto'
  if (moduleId.value === 'dustless') { params = { detectThreshold: dustlessParams.value.detectThreshold, dilateLevel: dustlessParams.value.dilateLevel }; repairMode = dustlessParams.value.repairMode }
  else if (moduleId.value === 'liuguang') { params = { modelSize: liuguangParams.value.modelSize, model: liuguangParams.value.model, inputSize: liuguangParams.value.inputSize, colorEnhance: liuguangParams.value.colorEnhance, prompt: liuguangParams.value.prompt, warmth: liuguangParams.value.warmth, saturation: liuguangParams.value.saturation, contrast: liuguangParams.value.contrast, enhance_only: liuguangParams.value.enhance_only } }
  else if (moduleId.value === 'qingying') { params = { prompt: qingyingParams.value.prompt, upscale: qingyingParams.value.upscale, patchSize: qingyingParams.value.patchSize, stride: qingyingParams.value.stride, seed: qingyingParams.value.seed, enhanceText: qingyingParams.value.enhanceText, repairBackground: qingyingParams.value.repairBackground } }
  else if (moduleId.value === 'zhenrong') { params = { faceEnhanceLevel: zhenrongParams.value.faceEnhanceLevel, skinSmooth: zhenrongParams.value.skinSmooth, eyeEnhance: zhenrongParams.value.eyeEnhance, lipEnhance: zhenrongParams.value.lipEnhance } }

  const apiModuleMap: Record<string, string> = { dustless: 'dustless', liuguang: 'colorize', qingying: 'qingying', zhenrong: 'trueface' }
  const apiModule = apiModuleMap[moduleId.value] || moduleId.value
  let taskId: number | null = null

  // 手动修复模式：导出遮罩并上传 —— 完全参照 Web 前端流程
  let maskId: number | null = null
  if (moduleId.value === 'dustless' && repairMode === 'manual') {
    // 校验：必须有涂抹轨迹
    if (!hasStrokes.value) {
      throw new Error('请先在图片上涂抹需要修复的区域')
    }

    loadingMsg.value = '正在导出涂抹遮罩...'
    let photoId = imagePhotoId.value
    
    // 如果是从相册直接上传的本地图片，先上传到图库获取 photo_id（参照 Web 前端流程）
    if (!photoId && imageFilePath.value) {
      try {
        const uploadRes = await uploadFile({ url: '/gallery/photos/upload', filePath: imageFilePath.value, name: 'file' })
        photoId = (uploadRes as any).id
        imagePhotoId.value = photoId
      } catch (e: any) {
        throw new Error('图片上传失败: ' + (e.message || '请重试'))
      }
    }
    if (!photoId) throw new Error('请先选择或上传图片')

    // 导出 canvas 遮罩为临时文件
    let maskTempPath = ''
    try {
      maskTempPath = await exportMask()
    } catch (e: any) {
      throw new Error('遮罩导出失败，请重新涂抹后重试')
    }

    // 上传遮罩到后端 (参照 Web 前端: POST /workshop/masks, form: mask + photo_id)
    loadingMsg.value = '正在上传涂抹遮罩...'
    try {
      // #ifdef H5
      // H5: uni.uploadFile 对 blob URL 支持不稳定，使用 FormData + fetch 直接上传
      const maskBlob = await fetch(maskTempPath).then(r => r.blob())
      const fd = new FormData()
      fd.append('mask', maskBlob, 'mask.png')
      fd.append('photo_id', String(photoId))
      const token = getToken()
      const fHeaders: Record<string, string> = {}
      if (token) fHeaders['Authorization'] = `Bearer ${token}`
      const fRes = await fetch('http://localhost:8000/api/v1/workshop/masks', { method: 'POST', body: fd, headers: fHeaders })
      const maskResData = await fRes.json()
      if (!fRes.ok) throw new Error(maskResData.detail || '上传失败')
      maskId = maskResData.id
      // #endif
      // #ifndef H5
      const maskRes = await uploadFile({ 
        url: '/workshop/masks', 
        filePath: maskTempPath, 
        name: 'mask', 
        formData: { photo_id: String(photoId) } 
      })
      maskId = (maskRes as any).id
      // #endif
      if (!maskId) throw new Error('遮罩上传失败，未获取到有效的 maskId')
    } catch (e: any) {
      throw new Error('遮罩上传失败: ' + (e.message || '请重试'))
    }
    
    // 创建修复任务 (参照 Web 前端: createTaskFromGallery 流程)
    const requestData: any = { 
      photo_id: photoId, 
      steps: [apiModule], 
      task_type: 'single', 
      use_powerpaint: true, 
      powerpaint_task_type: 'object-removal', 
      repair_mode: repairMode, 
      mask_id: maskId 
    }
    if (params) requestData.params = params
    loadingMsg.value = '正在创建修复任务...'
    const res = await post('/workshop/tasks', requestData)
    taskId = (res as any).id
  } else if (imagePhotoId.value) {
    const requestData: any = { photo_id: imagePhotoId.value, steps: [apiModule], task_type: 'single', use_powerpaint: true, powerpaint_task_type: 'object-removal', repair_mode: repairMode }
    if (params) requestData.params = params
    loadingMsg.value = '正在创建修复任务...'
    const res = await post('/workshop/tasks', requestData)
    taskId = (res as any).id
  } else if (imageFilePath.value) {
    loadingMsg.value = '正在上传图片...'
    const formData: Record<string, any> = { module: apiModule, use_powerpaint: 'true', task_type: 'object-removal', repair_mode: repairMode }
    if (params) formData.params = JSON.stringify(params)
    const res = await uploadFile({ url: '/workshop/tasks', filePath: imageFilePath.value, name: 'file', formData })
    taskId = (res as any).id
  } else { throw new Error('请先选择或上传图片') }
  if (!taskId) throw new Error('任务创建失败')
  await pollTaskStatus(taskId)
}

const handleLivePortrait = async () => {
  if (!drivingAudioFile.value && !drivingAudioPath.value) throw new Error('请先上传驱动音频')
  if (!drivingVideoFile.value && !drivingVideoPath.value) throw new Error('请先上传驱动视频')
  
  loadingMsg.value = '正在提交人像复活任务...'
  
  // 先上传图片到图库（如未上传）
  let photoId = imagePhotoId.value
  if (!photoId && imageFilePath.value) {
    const uploadRes = await uploadFile({ url: '/gallery/photos/upload', filePath: imageFilePath.value, name: 'file' })
    photoId = (uploadRes as any).id
    imagePhotoId.value = photoId
  }
  if (!photoId) throw new Error('请先选择或上传图片')

  // 构建 FormData，同时上传音频和视频（参照 Web 前端逻辑）
  const fd = new FormData()
  fd.append('image_id', photoId.toString())
  fd.append('relative_motion', livePortraitParams.value.relativeMotion.toString())
  fd.append('paste_back', livePortraitParams.value.pasteBack.toString())
  fd.append('expression_scale', livePortraitParams.value.expressionScale.toString())

  // 添加音频文件
  if (drivingAudioFile.value) {
    fd.append('audio', drivingAudioFile.value)
  } else if (drivingAudioPath.value) {
    // uni 路径 → Blob（H5 环境通过 fetch 获取）
    const resp = await fetch(drivingAudioPath.value)
    const blob = await resp.blob()
    fd.append('audio', blob, drivingAudioName.value || 'audio.wav')
  }

  // 添加驱动视频文件
  if (drivingVideoFile.value) {
    fd.append('driving_video', drivingVideoFile.value)
  } else if (drivingVideoPath.value) {
    const resp = await fetch(drivingVideoPath.value)
    const blob = await resp.blob()
    fd.append('driving_video', blob, drivingVideoName.value || 'driving_video.mp4')
  }

  loadingMsg.value = '正在上传驱动文件...'
  
  const token = uni.getStorageSync('token')
  const BASE_URL = 'http://localhost:8000/api/v1'
  const response = await fetch(`${BASE_URL}/workshop/live_portrait/generate`, {
    method: 'POST',
    body: fd,
    headers: {
      'Authorization': token ? `Bearer ${token}` : ''
    }
  })

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}))
    throw new Error((errData as any).detail || `请求失败 (${response.status})`)
  }

  const data = await response.json()
  if ((data as any).task_id) {
    await pollTaskStatus((data as any).task_id)
  } else if ((data as any).result_url || (data as any).result_path) {
    resultUrl.value = getFullUrl((data as any).result_url || (data as any).result_path)
    isProcessing.value = false
    progress.value = 100
  } else {
    throw new Error('任务创建失败，未获取到任务 ID')
  }
}

const handleVoice = async () => {
  if (!voiceParams.value.text) throw new Error('请输入要转换的文字')
  if (voiceParams.value.text.length > 1000) throw new Error('文本内容过长，请控制在1000字以内')

  const mode = voiceParams.value.mode
  if (mode === 'clone' && !voiceRefFilePath.value) throw new Error('请上传声音样本')

  loadingMsg.value = mode === 'clone' ? '正在进行声音克隆，请耐心等待...' : '正在合成语音...'

  // 语速格式："+10%" 或 "-10%"
  const rateStr = voiceParams.value.rate >= 0
    ? `+${voiceParams.value.rate}%`
    : `${voiceParams.value.rate}%`

  // 模拟进度动画（语音生成是直接响应，无任务轮询）
  const progressTimer = setInterval(() => {
    if (progress.value < 90) progress.value += Math.floor(Math.random() * 5) + 2
  }, 800)

  try {
    const audioPath = await voiceGenerate({
      text: voiceParams.value.text.trim(),
      mode,
      voiceId: voiceParams.value.voiceId,
      rate: rateStr,
      promptText: voiceParams.value.promptText,
      refAudioPath: mode === 'clone' ? voiceRefFilePath.value : undefined,
    })

    clearInterval(progressTimer)
    progress.value = 100
    resultUrl.value = audioPath
    isProcessing.value = false
    uni.showToast({ title: '语音生成成功', icon: 'success' })
    // 自动初始化音频播放器
    setTimeout(() => initAudio(), 300)
  } catch (e) {
    clearInterval(progressTimer)
    throw e
  }
}

const handleTimeEngine = async () => {
  if (!imageFilePath.value && !imagePhotoId.value) throw new Error('请先上传图片')
  loadingMsg.value = '正在启动时光引擎...'
  if (imageFilePath.value) {
    const res = await uploadFile({ url: '/time-engine/repair', filePath: imageFilePath.value, name: 'file' })
    if ((res as any).prompt_id) await pollTimeEngineTask()
  }
}

const pollTaskStatus = (taskId: number): Promise<void> => {
  return new Promise((resolve, reject) => {
    const pollInterval = setInterval(async () => {
      try {
        const res = await get(`/workshop/tasks/${taskId}`)
        const task = res as any
        if (task.status === 'processing') { 
          loadingMsg.value = task.progress_msg || '正在处理中...'; 
          if (progress.value < 90) progress.value += Math.floor(Math.random() * 8) + 2 
        }
        else if (task.status === 'completed') {
          clearInterval(pollInterval); progress.value = 100
          setTimeout(() => {
             if (task.result_path) resultUrl.value = getFullUrl(task.result_path)
             isProcessing.value = false; uni.showToast({ title: '修复完成', icon: 'success' }); resolve()
          }, 800) // 延迟确保进度条展示
        } else if (task.status === 'failed') {
          clearInterval(pollInterval); isProcessing.value = false
          uni.showToast({ title: task.error_message || '修复失败', icon: 'none' }); reject(new Error(task.error_message || '修复失败'))
        }
      } catch (e) { clearInterval(pollInterval); isProcessing.value = false; reject(e) }
    }, 2000)
  })
}

const pollTimeEngineTask = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    const pollInterval = setInterval(async () => {
      try {
        const res = await get('/workshop/tasks')
        const tasks = res as any[]
        const currentTask = tasks.find((t: any) => t.task_type === 'time_engine' && (t.status === 'processing' || t.status === 'completed'))
        if (!currentTask) throw new Error('未找到时光引擎任务')
        if (currentTask.status === 'processing') { 
          loadingMsg.value = '正在处理中...'; 
          if (progress.value < 90) progress.value += 3 
        }
        else if (currentTask.status === 'completed') {
          clearInterval(pollInterval); progress.value = 100
          setTimeout(() => {
            if (currentTask.step_results?.length > 0) resultUrl.value = getFullUrl(currentTask.step_results[currentTask.step_results.length - 1])
            else if (currentTask.result_urls?.length > 0) resultUrl.value = currentTask.result_urls[currentTask.result_urls.length - 1]
            else if (currentTask.result_path) resultUrl.value = getFullUrl(currentTask.result_path)
            isProcessing.value = false; uni.showToast({ title: '时光引擎处理完成', icon: 'success' }); resolve()
          }, 800)
        } else if (currentTask.status === 'failed') {
          clearInterval(pollInterval); isProcessing.value = false
          uni.showToast({ title: '时光引擎运行失败', icon: 'none' }); reject(new Error('时光引擎运行失败'))
        }
      } catch (e) { clearInterval(pollInterval); isProcessing.value = false; reject(e) }
    }, 2000)
  })
}

const getFullUrl = (path: string): string => {
  if (!path) return ''
  if (path.startsWith('http')) return path
  let cleanPath = path.replace(/\\/g, '/')
  cleanPath = cleanPath.startsWith('/') ? cleanPath.substring(1) : cleanPath
  while (cleanPath.startsWith('static/static/')) cleanPath = cleanPath.replace('static/static/', 'static/')
  if (!cleanPath.startsWith('static/')) cleanPath = `static/${cleanPath}`
  return `http://localhost:8000/${cleanPath}`
}

const downloadResult = () => {
  if (!resultUrl.value) return
  // 语音模块：保存音频文件
  if (moduleId.value === 'voice') {
    uni.saveFile({
      tempFilePath: resultUrl.value,
      success: (res) => {
        uni.showToast({ title: '音频已保存', icon: 'success' })
      },
      fail: () => uni.showToast({ title: '保存失败，请检查存储权限', icon: 'none' })
    })
    return
  }
  // H5 端 uni.downloadFile 会因 CORS 无法读取 Content-Disposition 头而报错
  // 直接使用 uni.request + arraybuffer 方案
  uni.showLoading({ title: '下载中...' })
  uni.request({
    url: resultUrl.value,
    responseType: 'arraybuffer',
    success: (reqRes) => {
      uni.hideLoading()
      if (reqRes.statusCode === 200 && reqRes.data) {
        const buffer = reqRes.data as ArrayBuffer
        if (buffer.byteLength === 0) {
          uni.showToast({ title: '下载的文件为空', icon: 'none' })
          return
        }
        const fs = uni.getFileSystemManager()
        const tempPath = `${uni.env.USER_DATA_PATH}/save_${Date.now()}.jpg`
        fs.writeFile({
          filePath: tempPath,
          data: buffer,
          success: () => {
            uni.saveImageToPhotosAlbum({
              filePath: tempPath,
              success: () => uni.showToast({ title: '已保存到相册', icon: 'success' }),
              fail: () => uni.showToast({ title: '保存失败，请检查权限', icon: 'none' })
            })
          },
          fail: () => uni.showToast({ title: '文件写入失败', icon: 'none' })
        })
      } else {
        uni.showToast({ title: '下载失败', icon: 'none' })
      }
    },
    fail: () => {
      uni.hideLoading()
      uni.showToast({ title: '下载失败，请检查网络', icon: 'none' })
    }
  })
}

const continueRepair = () => {
  if (!resultUrl.value) return
  // 语音模块不支持继续修复
  if (moduleId.value === 'voice') {
    resetAll()
    return
  }
  uni.downloadFile({ url: resultUrl.value, success: (res) => {
    if (res.statusCode === 200) {
      imageUrl.value = resultUrl.value; imageFilePath.value = res.tempFilePath
      imagePhotoId.value = null; resultUrl.value = ''; isHoldingCompare.value = false
      uni.showToast({ title: '已将修复结果作为新输入', icon: 'none' })
    }
  }})
}

const resetAll = () => {
  destroyAudio()
  imageUrl.value = ''; imageFilePath.value = ''; imagePhotoId.value = null
  resultUrl.value = ''; isProcessing.value = false; progress.value = 0
  isHoldingCompare.value = false; brushMode.value = 'draw'
  hasStrokes.value = false; clearCanvas()
  voiceRefFileName.value = ''; voiceRefFilePath.value = ''
  drivingAudioName.value = ''; drivingAudioPath.value = ''; drivingAudioFile.value = null
  drivingVideoName.value = ''; drivingVideoPath.value = ''; drivingVideoFile.value = null
  resetParams()
}
</script>

<style lang="scss" scoped>
/* ================= 核心动画与环境 ================= */
@keyframes fadeInUp { 0% { opacity: 0; transform: translateY(40rpx); } 100% { opacity: 1; transform: translateY(0); } }
@keyframes orbDrift { 0% { transform: translate(0, 0) scale(1); } 50% { transform: translate(30rpx, -20rpx) scale(1.05); } 100% { transform: translate(0, 0) scale(1); } }
@keyframes shimmer { 0% { transform: translateX(-150%) skewX(-30deg); } 100% { transform: translateX(200%) skewX(-30deg); } }
@keyframes scanMove { 0% { top: 0%; opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { top: 100%; opacity: 0; } }
@keyframes pulse { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.1); opacity: 0.7; } }

.animate-fade-in-up { opacity: 0; animation: fadeInUp 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; }
.float-hover { transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease; &:active { transform: scale(0.95); box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05) !important; } }
.float-breathing { animation: orbDrift 6s ease-in-out infinite alternate; }

.ambient-background { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: var(--bg-elegant, #FAF8F5); z-index: -1; overflow: hidden; }
.orb { position: absolute; border-radius: 50%; filter: blur(90px); opacity: 0.5; animation: orbDrift 15s ease-in-out infinite; }
.orb-gold { width: 600rpx; height: 600rpx; background: rgba(212, 175, 55, 0.2); top: -10%; left: -20%; }
.orb-champagne { width: 700rpx; height: 700rpx; background: rgba(242, 169, 127, 0.15); bottom: 10%; right: -20%; animation-delay: -5s; }

/* 玻璃控件基础类 */
.glass-panel { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); border: 1rpx solid rgba(255, 255, 255, 0.8); box-shadow: 0 16rpx 40rpx rgba(44, 36, 23, 0.04), inset 0 4rpx 8rpx rgba(255, 255, 255, 0.5); border-radius: 40rpx; }
.glass-panel-light { background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px); border-radius: 24rpx; border: 1rpx solid #FFFFFF; box-shadow: 0 8rpx 24rpx rgba(0,0,0,0.03); }

/* ================= 页面结构 ================= */
.module-page { min-height: 100vh; width: 100%; box-sizing: border-box; }
.glass-nav { width: 100%; display: flex; align-items: center; justify-content: space-between; padding: 24rpx 32rpx; padding-top: calc(24rpx + var(--status-bar-height, 48rpx)); background: rgba(255,255,255,0.75); backdrop-filter: blur(20px); border-bottom: 1rpx solid rgba(255,255,255,0.5); position: sticky; top: 0; z-index: 100; box-sizing: border-box; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.02); }
.nav-back { width: 72rpx; height: 72rpx; display: flex; align-items: center; justify-content: center; border-radius: 50%; background: #FFFFFF; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05); .back-arrow { font-size: 36rpx; color: #3D352B; font-weight: 800; } }
.nav-center { flex: 1; text-align: center; .nav-title { display: block; font-size: 36rpx; font-weight: 800; color: #3D352B; letter-spacing: 2rpx; } .nav-subtitle { display: block; font-size: 22rpx; color: #A39B90; margin-top: 4rpx; font-weight: 500; } }
.nav-right { width: 72rpx; }
.module-content { height: calc(100vh - 140rpx - var(--status-bar-height, 48rpx)); padding: 0 32rpx; width: 100%; box-sizing: border-box; }

/* ================= 影像区域 ================= */
.image-section { margin-top: 32rpx; margin-bottom: 32rpx; width: 100%; }
.upload-area { height: 500rpx; width: 100%; border: 2rpx dashed var(--gold-main); display: flex; flex-direction: column; align-items: center; justify-content: center; box-sizing: border-box;
  .upload-icon-wrap { width: 120rpx; height: 120rpx; background: linear-gradient(135deg, #FDF8EF, #F5E4C3); border-radius: 40rpx; display: flex; align-items: center; justify-content: center; margin-bottom: 24rpx; box-shadow: 0 12rpx 32rpx rgba(212, 175, 55, 0.2), inset 0 4rpx 8rpx #FFF; }
  .upload-icon { font-size: 56rpx; } .upload-text { font-size: 32rpx; color: #5A4A32; font-weight: 800; margin-bottom: 8rpx; } .upload-hint { font-size: 24rpx; color: #A39B90; font-weight: 500; }
}

/* 预览区域：单图显示 + Canvas涂抹分离 */
.preview-area { border-radius: 48rpx; overflow: hidden; background: #FFFFFF; box-shadow: 0 16rpx 50rpx rgba(0,0,0,0.06); border: 2rpx solid #FFF; position: relative; }

/* 单图模式 —— 固定高度防止塌陷，与 canvas-draw-area 保持一致 */
.single-image-wrap { width: 100%; height: 650rpx; display: flex; align-items: center; justify-content: center; position: relative; }
.main-image { width: 100%; height: 100%; display: block; }

/* Canvas 手动涂抹模式 —— 画布区域合理大小，工具栏独立于下方 */
.canvas-wrap { 
  width: 100%; 
  position: relative; 
  display: flex; 
  flex-direction: column;
  border-radius: 48rpx; 
  overflow: hidden; 
  background: #FFFFFF; 
  box-shadow: 0 16rpx 50rpx rgba(0,0,0,0.06); 
  border: 2rpx solid #FFF; 
}
/* 可绘制区域：固定高度，保证图片和 Canvas 正确渲染 */
.canvas-draw-area { 
  width: 100%; 
  height: 650rpx; 
  position: relative; 
  overflow: hidden;
  background: #F5F0E8;
}
.canvas-zoom-indicator { position: absolute; top: 16rpx; left: 16rpx; z-index: 8; background: rgba(0,0,0,0.55); color: #FFF; font-size: 24rpx; padding: 6rpx 16rpx; border-radius: 12rpx; font-weight: 700; }
.canvas-bg-image { width: 100%; height: 100%; display: block; position: absolute; top: 0; left: 0; z-index: 1; pointer-events: none; }
.repair-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 5; touch-action: none; }
/* 工具栏：正常文档流，不再遮挡图片 */
.canvas-toolbar { 
  width: 100%; 
  background: rgba(255,255,255,0.95); 
  backdrop-filter: blur(12px); 
  padding: 20rpx 28rpx 28rpx; 
  box-shadow: 0 -4rpx 20rpx rgba(0,0,0,0.06);
  border-top: 1rpx solid rgba(212,175,55,0.15);
  flex-shrink: 0;
}
.canvas-hint { font-size: 24rpx; color: #5A4A32; font-weight: 700; display: block; margin-bottom: 12rpx; text-align: center; }
.paint-tool-row { display: flex; align-items: center; justify-content: center; gap: 20rpx; margin-bottom: 16rpx; }
.paint-tool-btn { padding: 14rpx 32rpx; border-radius: 20rpx; text { font-size: 24rpx; color: #FFF; font-weight: 700; } }
.paint-mode-btn { background: linear-gradient(135deg, #D4AF37, #F2A97F); }
.paint-clear-btn { background: linear-gradient(135deg, #E53E3E, #FC8181); }
.brush-size-control { display: flex; align-items: center; gap: 8rpx; padding-top: 8rpx; border-top: 1rpx solid rgba(0,0,0,0.05); }
.brush-label { font-size: 22rpx; color: #5A4A32; font-weight: 600; white-space: nowrap; }
.brush-size-value { font-size: 22rpx; color: var(--gold-dark); font-weight: 800; min-width: 60rpx; text-align: center; }

/* 状态徽章 */
.status-badge { position: absolute; top: 24rpx; left: 24rpx; z-index: 3; padding: 10rpx 28rpx; display: flex; align-items: center; gap: 12rpx; font-size: 24rpx; font-weight: 800; color: #5A4A32;
  .badge-dot { width: 12rpx; height: 12rpx; border-radius: 50%; background: var(--champagne-main); transition: background 0.3s; }
  .dot-original { background: #A39B90; }
}

/* 重新选择按钮 */
.re-upload-btn { position: absolute; top: 24rpx; right: 24rpx; z-index: 10; background: rgba(255,255,255,0.85); backdrop-filter: blur(12px); padding: 12rpx 28rpx; border-radius: 30rpx; box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.08); border: 1rpx solid #FFF; .re-upload-text { font-size: 24rpx; color: #5A4A32; font-weight: 700; } }

/* 按压对比按钮 */
.compare-control { margin-top: -40rpx; z-index: 4; position: relative; }
.compare-btn { display: inline-flex; align-items: center; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(16px); padding: 12rpx 36rpx 12rpx 12rpx; border-radius: 64rpx; box-shadow: 0 12rpx 40rpx rgba(212, 175, 55, 0.2); border: 1rpx solid rgba(255, 255, 255, 0.9); user-select: none;
  .compare-icon-wrap { width: 64rpx; height: 64rpx; border-radius: 50%; background: linear-gradient(135deg, var(--gold-main), var(--champagne-main)); display: flex; align-items: center; justify-content: center; margin-right: 16rpx; box-shadow: inset 0 2rpx 6rpx rgba(255,255,255,0.4); }
  .c-icon { font-size: 32rpx; color: #FFF; }
  .compare-text { font-size: 26rpx; font-weight: 800; color: #5A4A32; }
}

/* ================= 终极特效：处理中扫描器 ================= */
.processing-scanner-overlay { position: absolute; inset: 0; background: rgba(255,255,255,0.1); backdrop-filter: blur(12px); z-index: 10; overflow: hidden; display: flex; align-items: center; justify-content: center; }
/* 上下移动的金色扫描线 */
.scanner-line { position: absolute; left: 0; width: 100%; height: 6rpx; background: linear-gradient(90deg, transparent, var(--gold-main), transparent); box-shadow: 0 0 30rpx 10rpx rgba(212, 175, 55, 0.4); animation: scanMove 2.5s cubic-bezier(0.4, 0, 0.2, 1) infinite; z-index: 11; }
/* 进度悬浮仓 */
.progress-glass-capsule { background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(20px); border-radius: 40rpx; padding: 32rpx 48rpx; box-shadow: 0 20rpx 60rpx rgba(0,0,0,0.1); border: 2rpx solid #FFF; display: flex; flex-direction: column; align-items: center; z-index: 12; width: 70%;
  .loading-msg { font-size: 28rpx; font-weight: 800; color: #3D352B; margin-bottom: 20rpx; letter-spacing: 2rpx; }
  .progress-bar-wrap { width: 100%; height: 12rpx; background: #E8DCC8; border-radius: 6rpx; overflow: hidden; margin-bottom: 12rpx; }
  .progress-bar { height: 100%; background: linear-gradient(90deg, var(--gold-main), var(--champagne-main)); border-radius: 6rpx; transition: width 0.3s ease; box-shadow: 0 0 10rpx rgba(212, 175, 55, 0.5); }
  .progress-percent { font-size: 26rpx; color: var(--gold-main); font-weight: 800; font-family: monospace; }
}

/* ================= 参数调校区 ================= */
.params-section { padding: 40rpx 32rpx; margin-bottom: 40rpx; width: 100%; box-sizing: border-box; }
.params-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 32rpx; .params-title { font-size: 34rpx; font-weight: 800; color: #3D352B; letter-spacing: 2rpx; } .reset-btn { padding: 10rpx 28rpx; background: #FFFFFF; border-radius: 30rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.03); .reset-text { font-size: 24rpx; color: #A39B90; font-weight: 700; } } }
.param-group { margin-bottom: 32rpx; &:last-child { margin-bottom: 0; } }
.param-label { font-size: 28rpx; font-weight: 800; color: #5A4A32; margin-bottom: 16rpx; display: block; }
.param-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; .param-label { margin-bottom: 0; } .param-value { font-size: 26rpx; color: var(--gold-dark); font-weight: 800; font-family: monospace; background: rgba(212,175,55,0.1); padding: 4rpx 16rpx; border-radius: 12rpx; } }
.param-row-between { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16rpx; .param-label { margin-bottom: 0; } .text-btn { padding: 8rpx 24rpx; background: linear-gradient(135deg, #FDF8EF, #F5E4C3); border-radius: 20rpx; .text-btn-label { font-size: 24rpx; color: #D4AF37; font-weight: 700; } } }
.param-hints { display: flex; justify-content: space-between; margin-top: 8rpx; text { font-size: 22rpx; color: #A39B90; font-weight: 500; } }
.param-input { width: 100%; height: 96rpx; background: rgba(255,255,255,0.8); border-radius: 24rpx; padding: 0 32rpx; font-size: 28rpx; color: #3D352B; border: 1rpx solid #FFF; box-shadow: inset 0 2rpx 6rpx rgba(0,0,0,0.02); }
.param-textarea { width: 100%; height: 160rpx; background: rgba(255,255,255,0.8); border-radius: 24rpx; padding: 24rpx 28rpx; font-size: 28rpx; color: #3D352B; border: 1rpx solid #FFF; box-shadow: inset 0 2rpx 6rpx rgba(0,0,0,0.02); }
.input-placeholder { color: #C8C0B4; }
.char-count { display: block; text-align: right; font-size: 22rpx; color: #A39B90; margin-top: 8rpx; }

.mode-grid { display: flex; gap: 16rpx; &.mode-grid-2 { .mode-card { width: calc(50% - 8rpx); } } }
.mode-card { flex: 1; background: rgba(255,255,255,0.8); border-radius: 28rpx; padding: 24rpx 16rpx; text-align: center; border: 2rpx solid transparent; transition: all 0.3s; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.02);
  &.active { background: #FFFFFF; border-color: var(--gold-main); box-shadow: 0 8rpx 24rpx rgba(212, 175, 55, 0.15); transform: translateY(-4rpx); }
  .mode-icon { font-size: 40rpx; display: block; margin-bottom: 8rpx; } .mode-name { font-size: 26rpx; font-weight: 800; color: #3D352B; display: block; margin-bottom: 4rpx; } .mode-desc { font-size: 20rpx; color: #A39B90; display: block; font-weight: 500;}
}

.preset-grid { display: flex; flex-wrap: wrap; gap: 16rpx; }
.preset-card { flex: 1; min-width: 120rpx; padding: 20rpx 0; border-radius: 24rpx; text-align: center; border: 1px solid rgba(255,255,255,0.8); .preset-name { font-size: 26rpx; font-weight: 800; }
  &.preset-natural { background: linear-gradient(135deg, #FDFDFD, #F0F0F0); .preset-name { color: #5A4A32; } } 
  &.preset-vivid { background: linear-gradient(135deg, #FFF0F0, #FEE2E2); .preset-name { color: #C53030; } }
  &.preset-warm { background: linear-gradient(135deg, #FFF5EB, #FEEBC8); .preset-name { color: #C05621; } } 
  &.preset-cool { background: linear-gradient(135deg, #EBF8FF, #BEE3F8); .preset-name { color: #3182CE; } }
  &.preset-retro { background: linear-gradient(135deg, #FFFFF0, #FEFCBF); .preset-name { color: #975A16; } } 
  &.preset-cinema { background: linear-gradient(135deg, #FAF5FF, #E9D8FD); .preset-name { color: #805AD5; } }
}

.select-grid { display: flex; gap: 16rpx; }
.select-card { flex: 1; text-align: center; padding: 20rpx 0; background: rgba(255,255,255,0.8); border-radius: 20rpx; border: 2rpx solid transparent; transition: all 0.3s;
  &.active { background: #FFFFFF; border-color: var(--gold-main); box-shadow: 0 8rpx 24rpx rgba(212, 175, 55, 0.15); transform: translateY(-4rpx); } .select-label { font-size: 28rpx; font-weight: 700; color: #3D352B; }
}

.switch-row { display: flex; align-items: center; justify-content: space-between; padding: 12rpx 0; }
.switch-info { flex: 1; .param-label { margin-bottom: 4rpx; } .switch-desc { font-size: 22rpx; color: #A39B90; display: block; } }
.switch-track { width: 96rpx; height: 52rpx; background: rgba(0,0,0,0.1); border-radius: 30rpx; position: relative; transition: background 0.3s; box-shadow: inset 0 2rpx 6rpx rgba(0,0,0,0.05);
  &.active { background: var(--gold-main); }
  .switch-thumb { width: 44rpx; height: 44rpx; background: #FFFFFF; border-radius: 50%; position: absolute; top: 4rpx; left: 4rpx; transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.15); }
  &.active .switch-thumb { transform: translateX(44rpx); }
}

.collapse-header { display: flex; justify-content: space-between; align-items: center; .param-label { margin-bottom: 0; } .collapse-arrow { font-size: 22rpx; color: #A39B90; transition: transform 0.3s; &.expanded { transform: rotate(180deg); } } }
.collapse-body { margin-top: 20rpx; padding: 24rpx; background: rgba(255,255,255,0.5); border-radius: 24rpx; }
.sub-param { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; &:last-child { margin-bottom: 0; } .sub-param-label { font-size: 26rpx; color: #3D352B; font-weight: 600; } }
.picker-value { font-size: 26rpx; color: var(--gold-dark); font-weight: 600; background: rgba(212,175,55,0.1); padding: 8rpx 20rpx; border-radius: 16rpx; }
.seed-row { display: flex; gap: 12rpx; align-items: center; .seed-input { flex: 1; height: 64rpx; background: #FFFFFF; border-radius: 16rpx; padding: 0 20rpx; font-size: 26rpx; border: 2rpx solid #F0ECE4; }
  .seed-random-btn { padding: 12rpx 24rpx; background: #FDF8EF; border-radius: 16rpx; .seed-random-text { font-size: 24rpx; color: var(--gold-dark); font-weight: 700; } }
}

.info-card { display: flex; gap: 20rpx; padding: 28rpx; border-radius: 24rpx; margin-bottom: 24rpx; .info-icon { font-size: 40rpx; flex-shrink: 0; }
  .info-content { flex: 1; .info-title { display: block; font-size: 28rpx; font-weight: 700; margin-bottom: 8rpx; } .info-desc { display: block; font-size: 24rpx; line-height: 1.5; } }
  &.info-blue { background: #EBF8FF; border: 2rpx solid #BEE3F8; .info-title { color: #2B6CB0; } .info-desc { color: #4A90C4; } }
  &.info-gold { background: linear-gradient(135deg, #FDF8EF, #F5E4C3); border: 2rpx solid #D4AF37; .info-title { color: #8B6914; } .info-desc { color: #A39B90; } }
}

.flow-steps { padding-left: 24rpx; }
.flow-step { display: flex; align-items: flex-start; position: relative; padding-bottom: 32rpx; &:last-child { padding-bottom: 0; } }
.step-dot { width: 24rpx; height: 24rpx; border-radius: 50%; background: #E0DCD4; flex-shrink: 0; margin-top: 8rpx; margin-right: 20rpx; &.active { background: #D4AF37; box-shadow: 0 0 16rpx rgba(212, 175, 55, 0.5); } }
.step-line { position: absolute; left: 11rpx; top: 36rpx; width: 2rpx; height: calc(100% - 36rpx); background: #E0DCD4; }
.step-content { flex: 1; .step-title { display: block; font-size: 28rpx; font-weight: 700; color: #3D352B; margin-bottom: 4rpx; } .step-desc { display: block; font-size: 22rpx; color: #A39B90; } }

.voice-list { display: flex; flex-direction: column; gap: 16rpx; }
.voice-card { display: flex; align-items: center; padding: 24rpx; background: rgba(255,255,255,0.8); border-radius: 24rpx; border: 2rpx solid transparent; transition: all 0.3s;
  &.active { background: #FFFFFF; border-color: var(--gold-main); box-shadow: 0 8rpx 24rpx rgba(212, 175, 55, 0.15); transform: translateY(-4rpx); }
  .voice-icon-wrap { width: 72rpx; height: 72rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 20rpx; flex-shrink: 0;
    &.voice-blue { background: #EBF8FF; } &.voice-indigo { background: #E9D8FD; } &.voice-pink { background: #FED7E2; } &.voice-rose { background: #FED7D7; } &.voice-purple { background: #E9D8FD; }
    .voice-icon-text { font-size: 32rpx; }
  }
  .voice-info { flex: 1; .voice-name { display: block; font-size: 28rpx; font-weight: 700; color: #3D352B; } .voice-desc { display: block; font-size: 22rpx; color: #A39B90; margin-top: 4rpx; } }
  .voice-check { font-size: 32rpx; color: var(--gold-main); font-weight: 700; }
}

.audio-upload-area { background: rgba(255,255,255,0.8); border-radius: 24rpx; border: 2rpx dashed var(--gold-main); padding: 40rpx; display: flex; flex-direction: column; align-items: center; justify-content: center;
  .audio-upload-icon { font-size: 48rpx; margin-bottom: 12rpx; } .audio-upload-text { font-size: 28rpx; color: #3D352B; font-weight: 700; margin-bottom: 8rpx; } .audio-upload-hint { font-size: 22rpx; color: #A39B90; }
}
.audio-file-card { display: flex; align-items: center; padding: 24rpx; background: #FDF8EF; border-radius: 24rpx; border: 2rpx solid var(--gold-main);
  .audio-file-icon { font-size: 36rpx; margin-right: 20rpx; } .audio-file-info { flex: 1; .audio-file-name { font-size: 26rpx; color: #3D352B; font-weight: 600; } }
  .audio-file-remove { padding: 8rpx 16rpx; color: #E53E3E; font-size: 28rpx; font-weight: 700; }
}

/* ================= 底部操作区 ================= */
.action-section { margin-bottom: 40rpx; width: 100%; }
.start-btn { width: 100%; height: 112rpx; background: linear-gradient(135deg, var(--gold-main), var(--champagne-main)); border-radius: 56rpx; display: flex; align-items: center; justify-content: center; box-shadow: 0 16rpx 40rpx rgba(212, 175, 55, 0.35); transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); position: relative; overflow: hidden;
  &:active { transform: scale(0.96); box-shadow: 0 8rpx 20rpx rgba(212, 175, 55, 0.2); }
  &.disabled { background: rgba(200, 180, 140, 0.45); box-shadow: none; pointer-events: none; .start-btn-text { color: rgba(61, 53, 43, 0.35); } }
  .start-btn-text { font-size: 34rpx; color: #3D352B; font-weight: 800; letter-spacing: 6rpx; position: relative; z-index: 2; }
  .shimmer-effect { position: absolute; top: 0; left: 0; width: 30%; height: 100%; background: linear-gradient(90deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0.15)); z-index: 1; animation: shimmer 3s cubic-bezier(0.4, 0, 0.2, 1) infinite; }
}

.result-actions { display: flex; gap: 20rpx; margin-top: 32rpx; }
.action-btn { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 24rpx 0; background: #FFFFFF; border-radius: 32rpx; border: 1rpx solid rgba(255,255,255,0.9); box-shadow: 0 8rpx 24rpx rgba(0,0,0,0.04);
  .action-icon { font-size: 40rpx; margin-bottom: 8rpx; } .action-label { font-size: 24rpx; font-weight: 800; }
  &.action-download { background: linear-gradient(135deg, #FDF8EF, #FFFFFF); .action-icon, .action-label { color: var(--gold-dark); } border-color: rgba(212,175,55,0.2); }
  &.action-continue { .action-icon, .action-label { color: #5A4A32; } }
  &.action-reset { background: #FFF9F9; .action-icon, .action-label { color: #E53E3E; } border-color: rgba(229,62,62,0.1); }
}

.tips-section { margin-bottom: 40rpx; width: 100%; }
.tips-card { padding: 32rpx; .tips-title { display: block; font-size: 28rpx; font-weight: 800; color: var(--gold-dark); margin-bottom: 12rpx; } .tips-item { display: block; font-size: 24rpx; color: #8C7A5A; line-height: 1.6; font-weight: 500;} }

/* ================= 媒体结果展示（视频/音频） ================= */
.result-media-section { margin-bottom: 40rpx; width: 100%; }

.voice-processing-card { padding: 40rpx; display: flex; flex-direction: column; align-items: center; justify-content: center;
  .voice-progress-icon-wrap { width: 96rpx; height: 96rpx; border-radius: 50%; background: linear-gradient(135deg, #FDF8EF, #FFF9F0); display: flex; align-items: center; justify-content: center; margin-bottom: 20rpx; border: 2rpx solid rgba(212, 175, 55, 0.3); }
  .voice-progress-icon { font-size: 44rpx; animation: pulse 1.5s ease-in-out infinite; }
  .loading-msg { font-size: 28rpx; font-weight: 800; color: #3D352B; margin-bottom: 20rpx; letter-spacing: 2rpx; }
  .progress-bar-wrap { width: 80%; height: 12rpx; background: #E8DCC8; border-radius: 6rpx; overflow: hidden; margin-bottom: 12rpx; }
  .progress-bar { height: 100%; background: linear-gradient(90deg, var(--gold-main), var(--champagne-main)); border-radius: 6rpx; transition: width 0.3s ease; box-shadow: 0 0 10rpx rgba(212, 175, 55, 0.5); }
  .progress-percent { font-size: 26rpx; color: var(--gold-main); font-weight: 800; font-family: monospace; }
}

.audio-player-card { padding: 40rpx; display: flex; flex-direction: column; align-items: center; justify-content: center;
  .audio-card-icon-wrap { width: 96rpx; height: 96rpx; border-radius: 50%; background: linear-gradient(135deg, #FDF8EF, #FFF9F0); display: flex; align-items: center; justify-content: center; margin-bottom: 20rpx; border: 2rpx solid rgba(212, 175, 55, 0.3); }
  .audio-card-icon { font-size: 44rpx; }
  .audio-card-title { font-size: 30rpx; font-weight: 800; color: #3D352B; margin-bottom: 8rpx; }
  .audio-card-hint { font-size: 22rpx; color: #A39B90; margin-bottom: 20rpx; }
  .audio-player-wrap { width: 100%; }
  .audio-controls { display: flex; align-items: center; gap: 16rpx; width: 100%; }
  .audio-btn { width: 64rpx; height: 64rpx; border-radius: 50%; background: var(--gold-main); display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 4rpx 12rpx rgba(212, 175, 55, 0.3); }
  .audio-btn-icon { font-size: 28rpx; color: #fff; }
  .audio-progress-wrap { flex: 1; }
  .audio-time { font-size: 20rpx; color: #A39B90; flex-shrink: 0; width: 108rpx; text-align: right; }
}
</style>