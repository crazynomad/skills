---
name: tts
description: Text-to-speech and speech-to-text on Apple Silicon using Vox CLI (Qwen3-TTS + MLX)
---

# Vox TTS / STT (Apple Silicon)

Local text-to-speech, speech-to-text, and voice cloning powered by Qwen3-TTS/ASR + MLX on Apple Silicon.

## Description

A powerful local TTS/STT skill based on [Vox CLI](https://github.com/3Craft/tts) that runs entirely on Apple Silicon Macs. Features speech synthesis with preset and custom voices, voice cloning from audio samples, speech recognition with subtitle generation, and batch processing. All models run locally via MLX - your data never leaves your machine.

## When to Use

Use this skill when users:
- Want to convert text to speech, "read this aloud", "generate audio from text"
- Ask for "TTS", "text to speech", "语音合成", "文字转语音", "朗读"
- Want to transcribe audio to text, "STT", "speech to text", "语音识别", "转录"
- Need voice cloning from a sample, "clone this voice", "克隆声音"
- Want to generate subtitles (SRT/VTT) from audio
- Ask for batch text-to-speech conversion
- Mention "vox" or "Qwen3-TTS"

## Features

- **Text-to-Speech**: Synthesize speech with 20+ preset voices
- **Speech-to-Text**: Transcribe audio with word-level timestamps
- **Voice Cloning**: Clone a voice from a 3+ second audio sample
- **Voice Design**: Describe a voice in natural language and generate it
- **Subtitle Generation**: Output SRT/VTT with word-level timestamps
- **Batch Processing**: Process multiple texts in one model-load cycle
- **Daemon Mode**: Keep models resident in memory for faster subsequent calls
- **Multiple Models**: 0.6B (small/fast) and 1.7B (large/quality) parameter models
- **100% Local**: All processing runs on-device via MLX

## Usage

### Basic Syntax

```bash
python scripts/vox_tts.py speak "Hello, this is a test" [OPTIONS]
python scripts/vox_tts.py transcribe audio.wav [OPTIONS]
python scripts/vox_tts.py clone "Text to speak" --ref voice_sample.wav [OPTIONS]
```

### Common Scenarios

**Speak text with default voice**:
```bash
python scripts/vox_tts.py speak "Hello world" -o ./output
```

**Speak text and play immediately**:
```bash
python scripts/vox_tts.py speak "Hello world" --play
```

**Speak with a specific voice**:
```bash
python scripts/vox_tts.py speak "Hello world" --voice Chelsie -o ./output
```

**Speak with emotion/style instruction**:
```bash
python scripts/vox_tts.py speak "I can't believe it!" --instruct "excited and surprised" -o ./output
```

**Speak Chinese text**:
```bash
python scripts/vox_tts.py speak "你好，世界" --voice Chelsie -o ./output
```

**Clone a voice and speak**:
```bash
python scripts/vox_tts.py clone "Text in the cloned voice" --ref sample.wav -o ./output
```

**Register a cloned voice for reuse**:
```bash
python scripts/vox_tts.py clone --ref sample.wav --register my-voice
python scripts/vox_tts.py speak "Now using my custom voice" --voice my-voice
```

**Design a voice from description**:
```bash
python scripts/vox_tts.py design "Hello everyone" --desc "A warm, friendly female voice with a slight British accent" -o ./output
```

**Transcribe audio to text**:
```bash
python scripts/vox_tts.py transcribe recording.wav
```

**Transcribe with subtitles**:
```bash
python scripts/vox_tts.py transcribe recording.wav --subtitle srt -o ./output
```

**Batch TTS from file** (one line per utterance):
```bash
python scripts/vox_tts.py batch texts.txt --voice Chelsie -o ./output
```

**Use large model for higher quality**:
```bash
python scripts/vox_tts.py speak "High quality speech" --model large -o ./output
```

**List available voices**:
```bash
python scripts/vox_tts.py voices
```

### Arguments

#### `speak` - Text-to-Speech

| Argument | Description | Default |
|----------|-------------|---------|
| `text` | Text to synthesize (required) | - |
| `-o, --output` | Output directory | Current directory |
| `-v, --voice` | Voice name (see `voices` command) | Chelsie |
| `-m, --model` | Model size: `small`, `large`, `large-hq` | small |
| `-s, --speed` | Speech speed multiplier | 1.0 |
| `-i, --instruct` | Emotion/style instruction | None |
| `--play` | Play audio after generation | False |
| `--subtitle` | Generate subtitle: `srt` or `vtt` | None |

#### `transcribe` - Speech-to-Text

| Argument | Description | Default |
|----------|-------------|---------|
| `audio` | Audio file path (required) | - |
| `-o, --output` | Output directory | Current directory |
| `--subtitle` | Output format: `srt`, `vtt`, `json` | plain text |
| `--language` | Source language | auto-detect |

#### `clone` - Voice Cloning

| Argument | Description | Default |
|----------|-------------|---------|
| `text` | Text to synthesize | None |
| `--ref` | Reference audio file (3+ seconds, required) | - |
| `--register` | Register as reusable voice name | None |
| `-o, --output` | Output directory | Current directory |

#### `design` - Voice Design

| Argument | Description | Default |
|----------|-------------|---------|
| `text` | Text to synthesize (required) | - |
| `--desc` | Voice description in natural language (required) | - |
| `-o, --output` | Output directory | Current directory |

#### `batch` - Batch Processing

| Argument | Description | Default |
|----------|-------------|---------|
| `file` | Text file, one utterance per line (required) | - |
| `-v, --voice` | Voice name | Chelsie |
| `-o, --output` | Output directory | Current directory |

## Dependencies

```bash
# Requirements: Apple Silicon Mac (M1/M2/M3/M4), Python 3.10+, macOS 13+

# Install via pipx (recommended, global CLI)
brew install pipx
pipx ensurepath
git clone https://github.com/3Craft/tts.git /tmp/vox-tts
cd /tmp/vox-tts && pipx install .

# Or install via pip in a venv
pip install -e /path/to/tts

# Optional: Chinese text support
pipx inject vox-cli 'misaki[zh]'

# Optional: Japanese text support
pipx inject vox-cli 'misaki[ja]'
```

## Output Structure

### Single TTS
```
OutputDir/
├── output.wav              # Generated audio
└── output.srt              # Subtitle (if --subtitle srt)
```

### Batch TTS
```
OutputDir/
├── 001_first_line.wav
├── 002_second_line.wav
└── ...
```

### Transcription
```
OutputDir/
├── recording.txt           # Plain text transcript
└── recording.srt           # Subtitle (if --subtitle srt)
```

## Claude Integration

When user requests TTS, STT, or voice cloning:

1. **Read skill documentation**:
   ```python
   view("/mnt/skills/user/tts/SKILL.md")
   ```

2. **Check if vox is installed**:
   ```bash
   python /mnt/skills/user/tts/scripts/vox_tts.py check
   ```

3. **Install if needed**:
   ```bash
   brew install pipx && pipx ensurepath
   git clone https://github.com/3Craft/tts.git /tmp/vox-tts
   cd /tmp/vox-tts && pipx install .
   ```

4. **Execute command**:
   ```bash
   # TTS
   python /mnt/skills/user/tts/scripts/vox_tts.py speak "TEXT" \
     --voice Chelsie -o /mnt/user-data/outputs

   # STT
   python /mnt/skills/user/tts/scripts/vox_tts.py transcribe audio.wav \
     -o /mnt/user-data/outputs

   # Voice cloning
   python /mnt/skills/user/tts/scripts/vox_tts.py clone "TEXT" \
     --ref sample.wav -o /mnt/user-data/outputs
   ```

5. **Present files** to user:
   ```python
   present_files(["/mnt/user-data/outputs/..."])
   ```

## Available Voices

Run `vox voices` to see all preset voices. Some commonly used:

| Voice | Description |
|-------|-------------|
| Chelsie | Default female voice |
| Ethan | Male voice |

Custom voices can be registered via `clone --register`.

## How It Works

### TTS Workflow
1. **Text Processing**: Tokenize and normalize input text
2. **Model Inference**: Run Qwen3-TTS model via MLX on Apple Silicon GPU
3. **Audio Generation**: Generate WAV audio at 24kHz
4. **Post-Processing**: Apply speed adjustment, generate subtitles if requested

### STT Workflow
1. **Audio Loading**: Read audio file and resample if needed
2. **Model Inference**: Run Qwen3-ASR model via MLX
3. **Decoding**: Generate text with word-level timestamps
4. **Output**: Format as plain text, SRT, VTT, or JSON

### Under the Hood
- Models are downloaded from HuggingFace on first use (~1-3 GB)
- 8-bit quantization by default for memory efficiency
- bf16 mode available via `large-hq` for highest quality
- Daemon mode (`vox serve`) keeps models in memory for sub-second response

## Common Issues

**Q: First run is slow?**
A: Models are downloaded on first use (1-3 GB). Subsequent runs are much faster. Use daemon mode (`vox serve`) for instant response.

**Q: "Not Apple Silicon" error?**
A: Vox CLI requires Apple Silicon (M1/M2/M3/M4). It uses MLX which only runs on Apple's Neural Engine.

**Q: Chinese/Japanese text sounds wrong?**
A: Install language support: `pipx inject vox-cli 'misaki[zh]'` or `pipx inject vox-cli 'misaki[ja]'`

**Q: Out of memory?**
A: Use the `small` model (default) instead of `large`. Close other apps to free memory.

**Q: How to use a custom voice persistently?**
A: Register it: `vox clone --ref sample.wav --register my-voice`, then use `--voice my-voice`.

## Example Conversations

**User**: "帮我把这段文字转成语音：今天天气真好"

**Claude**:
```bash
python /mnt/skills/user/tts/scripts/vox_tts.py speak "今天天气真好" \
  --voice Chelsie -o /mnt/user-data/outputs --play
```

---

**User**: "Transcribe this audio file to SRT subtitles"

**Claude**:
```bash
python /mnt/skills/user/tts/scripts/vox_tts.py transcribe recording.wav \
  --subtitle srt -o /mnt/user-data/outputs
```

---

**User**: "用这段录音克隆一个声音，然后用它朗读一段话"

**Claude**:
```bash
# Register the cloned voice
python /mnt/skills/user/tts/scripts/vox_tts.py clone \
  --ref sample.wav --register custom-voice

# Speak with the cloned voice
python /mnt/skills/user/tts/scripts/vox_tts.py speak "这是用克隆声音朗读的文字" \
  --voice custom-voice -o /mnt/user-data/outputs --play
```

## Limitations

- **Apple Silicon only**: Requires M1/M2/M3/M4 Mac (MLX dependency)
- **macOS 13+**: Minimum OS version requirement
- **Memory**: Large model needs ~4GB RAM; small model ~2GB
- **Languages**: Best quality for English and Chinese; other languages may vary
- **Voice cloning**: Requires 3+ seconds of clear speech reference audio

## Version History

**v1.0** (Current)
- Initial release wrapping Vox CLI v0.3.3
- TTS, STT, voice cloning, voice design
- Batch processing and subtitle generation
- Daemon mode support

## References

- [Vox CLI GitHub](https://github.com/3Craft/tts)
- [MLX Audio](https://github.com/ml-explore/mlx-audio)
- [Qwen3-TTS](https://huggingface.co/Qwen/Qwen3-TTS)
