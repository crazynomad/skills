#!/usr/bin/env python3
"""
Vox TTS/STT wrapper for Claude Code skills.
Thin wrapper around the `vox` CLI (https://github.com/3Craft/tts).

Requirements:
- Apple Silicon Mac (M1/M2/M3/M4)
- Python 3.10+
- vox-cli installed via pipx: pipx install /path/to/tts
"""

import argparse
import os
import shutil
import subprocess
import sys


def check_vox():
    """Check if vox CLI is installed and accessible."""
    vox_path = shutil.which("vox")
    if vox_path:
        print(f"[OK] vox found at: {vox_path}")
        result = subprocess.run(["vox", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] Version: {result.stdout.strip()}")
        return True
    else:
        print("[ERROR] vox CLI not found.")
        print()
        print("Install via pipx (recommended):")
        print("  brew install pipx && pipx ensurepath")
        print("  git clone https://github.com/3Craft/tts.git /tmp/vox-tts")
        print("  cd /tmp/vox-tts && pipx install .")
        print()
        print("Or install via pip:")
        print("  pip install -e /path/to/tts")
        return False


def run_vox(args):
    """Run vox command with given arguments."""
    cmd = ["vox"] + args
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def cmd_speak(args):
    """Text-to-speech."""
    vox_args = ["speak", args.text]
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        vox_args.extend(["-o", args.output])
    if args.voice:
        vox_args.extend(["-v", args.voice])
    if args.model:
        vox_args.extend(["-m", args.model])
    if args.speed:
        vox_args.extend(["-s", str(args.speed)])
    if args.instruct:
        vox_args.extend(["-i", args.instruct])
    if args.play:
        vox_args.append("-p")
    if args.subtitle:
        vox_args.extend(["--subtitle", args.subtitle])
    return run_vox(vox_args)


def cmd_transcribe(args):
    """Speech-to-text."""
    if not os.path.isfile(args.audio):
        print(f"[ERROR] Audio file not found: {args.audio}")
        return 1
    vox_args = ["transcribe", args.audio]
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        vox_args.extend(["-o", args.output])
    if args.subtitle:
        vox_args.extend(["--subtitle", args.subtitle])
    if args.language:
        vox_args.extend(["--language", args.language])
    return run_vox(vox_args)


def cmd_clone(args):
    """Voice cloning."""
    if not args.ref:
        print("[ERROR] --ref (reference audio file) is required for voice cloning")
        return 1
    if not os.path.isfile(args.ref):
        print(f"[ERROR] Reference audio file not found: {args.ref}")
        return 1

    vox_args = ["clone"]
    if args.text:
        vox_args.append(args.text)
    vox_args.extend(["--ref", args.ref])
    if args.register:
        vox_args.extend(["--register", args.register])
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        vox_args.extend(["-o", args.output])
    return run_vox(vox_args)


def cmd_design(args):
    """Voice design from description."""
    vox_args = ["design", args.text, "--desc", args.desc]
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        vox_args.extend(["-o", args.output])
    return run_vox(vox_args)


def cmd_batch(args):
    """Batch TTS from file."""
    if not os.path.isfile(args.file):
        print(f"[ERROR] Text file not found: {args.file}")
        return 1
    vox_args = ["batch", args.file]
    if args.voice:
        vox_args.extend(["-v", args.voice])
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        vox_args.extend(["-o", args.output])
    return run_vox(vox_args)


def cmd_voices(args):
    """List available voices."""
    return run_vox(["voices"])


def main():
    parser = argparse.ArgumentParser(
        description="Vox TTS/STT wrapper - local speech synthesis and recognition on Apple Silicon"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # check
    subparsers.add_parser("check", help="Check if vox CLI is installed")

    # speak
    p_speak = subparsers.add_parser("speak", help="Text-to-speech")
    p_speak.add_argument("text", help="Text to synthesize")
    p_speak.add_argument("-o", "--output", help="Output directory")
    p_speak.add_argument("-v", "--voice", help="Voice name (default: Chelsie)")
    p_speak.add_argument("-m", "--model", choices=["small", "large", "large-hq"],
                         help="Model size (default: small)")
    p_speak.add_argument("-s", "--speed", type=float, help="Speech speed multiplier")
    p_speak.add_argument("-i", "--instruct", help="Emotion/style instruction")
    p_speak.add_argument("--play", action="store_true", help="Play audio after generation")
    p_speak.add_argument("--subtitle", choices=["srt", "vtt"], help="Generate subtitle file")

    # transcribe
    p_trans = subparsers.add_parser("transcribe", help="Speech-to-text")
    p_trans.add_argument("audio", help="Audio file path")
    p_trans.add_argument("-o", "--output", help="Output directory")
    p_trans.add_argument("--subtitle", choices=["srt", "vtt", "json"], help="Output format")
    p_trans.add_argument("--language", help="Source language (auto-detect by default)")

    # clone
    p_clone = subparsers.add_parser("clone", help="Voice cloning")
    p_clone.add_argument("text", nargs="?", help="Text to synthesize (optional if --register)")
    p_clone.add_argument("--ref", required=True, help="Reference audio file (3+ seconds)")
    p_clone.add_argument("--register", help="Register as reusable voice name")
    p_clone.add_argument("-o", "--output", help="Output directory")

    # design
    p_design = subparsers.add_parser("design", help="Voice design from description")
    p_design.add_argument("text", help="Text to synthesize")
    p_design.add_argument("--desc", required=True, help="Voice description in natural language")
    p_design.add_argument("-o", "--output", help="Output directory")

    # batch
    p_batch = subparsers.add_parser("batch", help="Batch TTS from text file")
    p_batch.add_argument("file", help="Text file, one utterance per line")
    p_batch.add_argument("-v", "--voice", help="Voice name")
    p_batch.add_argument("-o", "--output", help="Output directory")

    # voices
    subparsers.add_parser("voices", help="List available voices")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "check":
        sys.exit(0 if check_vox() else 1)

    # For all other commands, check vox is installed first
    if not shutil.which("vox"):
        print("[ERROR] vox CLI not found. Run with 'check' command for install instructions.")
        sys.exit(1)

    commands = {
        "speak": cmd_speak,
        "transcribe": cmd_transcribe,
        "clone": cmd_clone,
        "design": cmd_design,
        "batch": cmd_batch,
        "voices": cmd_voices,
    }

    sys.exit(commands[args.command](args))


if __name__ == "__main__":
    main()
