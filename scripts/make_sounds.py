#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""สร้างไฟล์เสียงทั้งหมดของเกมใหม่ในแนวชิปทูน 8-bit

Usage:  python scripts/make_sounds.py
Writes: Assets/Sound/FX/{jump,coin_pickup,hurt,explosion,level_complete}.wav
        Assets/Sound/walen.ogg   (ต้องมี ffmpeg ใน PATH)

ทุกเสียงสังเคราะห์ขึ้นเองจากคลื่น pulse / triangle / noise ไม่ได้ใช้ไฟล์เสียง
จากที่อื่น อยากปรับโทนเสียงก็แก้ตัวเลขในไฟล์นี้แล้วรันใหม่ได้เลย
"""
import os
import shutil
import subprocess
import sys
import wave

import numpy as np

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FX_DIR = os.path.join(ROOT, "Assets", "Sound", "FX")
BGM_PATH = os.path.join(ROOT, "Assets", "Sound", "walen.ogg")

rng = np.random.default_rng(20261017)


# --------------------------------------------------------------- ออสซิลเลเตอร์
def _phase(freq):
    """freq เป็น array ความถี่รายแซมเปิล -> เฟสสะสม (หน่วยเป็นรอบ)"""
    return np.cumsum(np.asarray(freq, dtype=np.float64)) / SR


def pulse(freq, duty=0.5):
    """คลื่นสี่เหลี่ยมปรับความกว้างพัลส์ได้ — เสียงหลักของชิปทูน"""
    return np.where(_phase(freq) % 1.0 < duty, 1.0, -1.0)


def triangle(freq):
    """คลื่นสามเหลี่ยม — ใช้ทำเบสแบบ NES"""
    return 4.0 * np.abs(_phase(freq) % 1.0 - 0.5) - 1.0


def noise(n, hold_hz=None):
    """ไวต์นอยซ์ ถ้าใส่ hold_hz จะค้างค่าเป็นขั้น ๆ ให้ได้กลิ่น 8-bit"""
    if hold_hz is None:
        return rng.uniform(-1.0, 1.0, n)
    hold = max(1, int(SR / hold_hz))
    return np.repeat(rng.choice([-1.0, 1.0], int(np.ceil(n / hold)) + 1), hold)[:n]


def noise_sweep(n, hz_start, hz_end):
    """นอยซ์ที่ค่อย ๆ หยาบขึ้น (ลดอัตราค้างค่า) ใช้ทำเสียงระเบิด"""
    rates = np.geomspace(hz_start, hz_end, n)
    step = rates / SR
    idx = np.floor(np.cumsum(step)).astype(np.int64)
    table = rng.uniform(-1.0, 1.0, idx[-1] + 2)
    return table[idx]


# ------------------------------------------------------------------- เอนเวโลป
def ad(n, attack=0.002, power=2.5):
    """ขึ้นเร็ว ลงแบบเอ็กซ์โปเนนเชียล"""
    a = min(int(attack * SR), n)
    e = np.empty(n)
    if a:
        e[:a] = np.linspace(0.0, 1.0, a)
    if n - a:
        e[a:] = (1.0 - np.linspace(0.0, 1.0, n - a)) ** power
    return e


def hold(n, attack=0.004, release=0.05):
    """ดังค้างแล้วค่อยปล่อย ใช้กับโน้ตในเพลง"""
    e = np.ones(n)
    a = min(int(attack * SR), n)
    r = min(int(release * SR), n - a)
    if a:
        e[:a] = np.linspace(0.0, 1.0, a)
    if r:
        e[n - r:] = np.linspace(1.0, 0.0, r) ** 1.5
    return e


def crush(x, bits=5):
    """ลดความละเอียดบิตให้ได้เสียงหยาบแบบเครื่องเกมเก่า"""
    lv = 2 ** (bits - 1)
    return np.round(x * lv) / lv


def const(value, n):
    return np.full(n, float(value))


def sweep(f0, f1, n):
    return np.geomspace(f0, f1, n)


# ------------------------------------------------------------------ เขียนไฟล์
# ความดัง (rms) ของไฟล์ชุดเดิม — ปรับของใหม่ให้เท่ากัน จะได้ไม่ต้องไปแก้
# volume_db ที่ตั้งไว้แล้วใน audio_manager.tscn กับ enemy.tscn
TARGET_RMS = {
    "jump.wav": 0.2025,
    "coin_pickup.wav": 0.1914,
    "hurt.wav": 0.1430,
    "explosion.wav": 0.4583,
    "level_complete.wav": 0.1746,
}
PEAK_CEIL = 0.95


def write_wav(path, mono):
    x = np.asarray(mono, dtype=np.float64)
    x = x / (np.max(np.abs(x)) or 1.0)
    target = TARGET_RMS.get(os.path.basename(path))
    if target:
        rms = np.sqrt((x ** 2).mean()) or 1.0
        gain = min(target / rms, PEAK_CEIL / (np.max(np.abs(x)) or 1.0))
        x = x * gain
    else:
        x = x * PEAK_CEIL
    x = np.clip(x, -1.0, 1.0)
    pcm = (x * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("  %-24s %6.3f s  rms %.3f  peak %.2f" % (os.path.basename(path), len(x) / SR, float(np.sqrt((x ** 2).mean())), float(np.max(np.abs(x)))))


# ====================================================================== SFX ==
def sfx_jump():
    """กระโดด: พัลส์แคบ ๆ กวาดเสียงสูงขึ้นเร็ว ๆ"""
    n = int(0.17 * SR)
    f = sweep(190, 780, n)
    f *= 1.0 + 0.02 * np.sin(np.linspace(0, 38, n))      # สั่นนิด ๆ ให้มีชีวิต
    body = pulse(f, duty=0.125) * ad(n, 0.001, 2.2)
    click = noise(int(0.008 * SR)) * ad(int(0.008 * SR), 0.0005, 5.0) * 0.35
    out = body
    out[:len(click)] += click
    return crush(out * 0.9, 5)


def sfx_coin():
    """เก็บเหรียญ: อาร์เพจจิโอสามตัวโน้ตพุ่งขึ้น"""
    notes = [(1319, 0.045), (1661, 0.045), (1976, 0.13)]  # E6 G#6 B6
    out = []
    for f0, dur in notes:
        n = int(dur * SR)
        out.append(pulse(const(f0, n), duty=0.25) * ad(n, 0.001, 1.6))
    sig = np.concatenate(out)
    tail = np.linspace(1.0, 0.0, len(sig)) ** 0.4          # ให้หางเสียงจางลง
    return crush(sig * tail, 5)


def sfx_hurt():
    """เจ็บ: สี่เหลี่ยมดิ่งลง + นอยซ์ซ้อน ฟังแล้วรู้ว่าโดนอะไรเข้า"""
    n = int(0.26 * SR)
    f = sweep(520, 95, n)
    tone = pulse(f, duty=0.5) * 0.75
    grit = noise(n, hold_hz=5200) * 0.45
    return crush((tone + grit) * ad(n, 0.0015, 1.9), 4)


def sfx_explosion():
    """ศัตรูระเบิด: นอยซ์หยาบขึ้นเรื่อย ๆ + ซับเบสดิ่งลง"""
    n = int(0.46 * SR)
    body = noise_sweep(n, 9000, 480) * ad(n, 0.001, 1.5)
    sub = triangle(sweep(110, 32, n)) * ad(n, 0.004, 2.6) * 0.65
    crack = noise(int(0.02 * SR)) * ad(int(0.02 * SR), 0.0003, 4.0) * 0.5
    out = body + sub
    out[:len(crack)] += crack
    return crush(out * 0.85, 5)


def sfx_level_complete():
    """ผ่านด่าน: แฟนแฟร์สั้น ๆ ปิดท้ายด้วยคอร์ดค้าง"""
    seq = [(523, 0.10), (659, 0.10), (784, 0.10), (1047, 0.10),
           (784, 0.08), (1047, 0.08), (1319, 0.16)]
    parts = []
    for f0, dur in seq:
        n = int(dur * SR)
        lead = pulse(const(f0, n), duty=0.5) * hold(n, 0.003, 0.03)
        bass = triangle(const(f0 / 4.0, n)) * hold(n, 0.004, 0.03) * 0.5
        parts.append(lead + bass)
    # คอร์ด C เมเจอร์ค้างท้าย
    n = int(0.58 * SR)
    chord = np.zeros(n)
    for f0 in (1047, 1319, 1568):
        chord += pulse(const(f0, n), duty=0.5) / 3.0
    chord += triangle(const(262, n)) * 0.55
    parts.append(chord * ad(n, 0.005, 1.1))
    return crush(np.concatenate(parts) * 0.8, 5)


# ====================================================================== BGM ==
BPM = 132
STEPS_PER_BAR = 16
STEP_N = int(SR * 60.0 / BPM / 4.0)          # ความยาว 1 ตัวเขบ็ตสองชั้น

_NAMES = {"c": 0, "c#": 1, "db": 1, "d": 2, "d#": 3, "eb": 3, "e": 4, "f": 5,
          "f#": 6, "gb": 6, "g": 7, "g#": 8, "ab": 8, "a": 9, "a#": 10, "bb": 10, "b": 11}


def midi(name):
    s = name.strip().lower()
    i = len(s) - 1
    while s[i].isdigit():
        i -= 1
    return 12 * (int(s[i + 1:]) + 1) + _NAMES[s[:i + 1]]


def hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def parse(pattern):
    """'a4:2 -:4 c5:2' -> [(midi|None, steps), ...]"""
    out = []
    for tok in pattern.split():
        name, _, steps = tok.partition(":")
        out.append((None if name == "-" else midi(name), int(steps)))
    return out


CHORDS = {
    "Am": ("a2", [0, 3, 7]),
    "F":  ("f2", [0, 4, 7]),
    "C":  ("c3", [0, 4, 7]),
    "G":  ("g2", [0, 4, 7]),
    "E":  ("e2", [0, 4, 7]),
}

LEAD_A = [
    "a4:2 c5:2 e5:4 d5:4 c5:4",
    "f4:2 a4:2 c5:4 a4:4 g4:4",
    "g4:2 c5:2 e5:4 g5:4 e5:4",
    "d5:2 b4:2 g4:4 b4:4 d5:4",
    "e5:2 a5:2 g5:2 e5:2 c5:4 d5:4",
    "c5:2 f5:2 e5:2 c5:2 a4:4 g4:4",
    "b4:2 d5:2 g5:2 d5:2 b4:4 g4:4",
    "a4:4 e5:4 a5:6 -:2",
]
LEAD_A2 = LEAD_A[:6] + [
    "d5:2 g5:2 b5:2 g5:2 d5:4 b4:4",
    "a5:4 e5:4 a4:8",
]
LEAD_B = [
    "a5:2 a5:2 g5:2 f5:2 e5:4 f5:4",
    "g5:2 g5:2 e5:2 c5:2 g5:4 e5:4",
    "b5:2 b5:2 a5:2 g5:2 d5:4 g5:4",
    "c6:2 b5:2 a5:2 g5:2 a5:8",
    "f5:2 a5:2 c6:2 a5:2 g5:4 f5:4",
    "e5:2 g5:2 c6:2 g5:2 e5:4 c5:4",
    "b4:2 e5:2 g#5:2 b5:2 g#5:4 e5:4",
    "b5:4 g#5:4 e5:8",
]
CH_A = ["Am", "F", "C", "G", "Am", "F", "G", "Am"]
CH_B = ["F", "C", "G", "Am", "F", "C", "E", "E"]
CH_INTRO = ["Am", "F", "C", "G"]


def add(buf, start, sig, gain=1.0):
    end = min(len(buf), start + len(sig))
    if end > start:
        buf[start:end] += sig[:end - start] * gain


def render_lead(buf, bar0, bars, patterns):
    for i, pat in enumerate(patterns):
        base = (bar0 + i) * STEPS_PER_BAR * STEP_N
        cur = 0
        for note, steps in parse(pat):
            n = steps * STEP_N
            if note is not None:
                duty = 0.25 if (i % 2 == 0) else 0.5
                sig = pulse(const(hz(note), n), duty) * hold(n, 0.004, 0.045)
                add(buf, base + cur, sig)
            cur += n


def render_bass(buf, bar0, chords):
    for i, ch in enumerate(chords):
        root = midi(CHORDS[ch][0])
        base = (bar0 + i) * STEPS_PER_BAR * STEP_N
        shape = [0, 0, 7, 0, 0, 0, 12, 0]        # ลายเบสเขบ็ตชั้นเดียว
        for k, off in enumerate(shape):
            n = 2 * STEP_N
            sig = triangle(const(hz(root + off), n)) * hold(n, 0.003, 0.03)
            add(buf, base + k * 2 * STEP_N, sig)


def render_arp(buf, bar0, chords):
    for i, ch in enumerate(chords):
        rootname, triad = CHORDS[ch]
        root = midi(rootname) + 24
        base = (bar0 + i) * STEPS_PER_BAR * STEP_N
        order = triad + [triad[1] + 12]
        for k in range(STEPS_PER_BAR):
            n = STEP_N
            note = root + order[k % len(order)]
            sig = pulse(const(hz(note), n), 0.125) * ad(n, 0.001, 2.0)
            add(buf, base + k * STEP_N, sig)


def render_drums(buf, bar0, bars, fill_last=False):
    for i in range(bars):
        base = (bar0 + i) * STEPS_PER_BAR * STEP_N
        for s in (0, 8):                                    # กระเดื่อง
            n = int(0.11 * SR)
            k = triangle(sweep(150, 42, n)) * ad(n, 0.001, 2.4)
            add(buf, base + s * STEP_N, k, 0.95)
        for s in (4, 12):                                   # สแนร์
            n = int(0.10 * SR)
            sn = noise(n, hold_hz=7000) * ad(n, 0.001, 2.2)
            add(buf, base + s * STEP_N, sn, 0.5)
        for s in range(0, STEPS_PER_BAR, 2):                # ไฮแฮต
            n = int(0.028 * SR)
            h = noise(n, hold_hz=14000) * ad(n, 0.0005, 3.2)
            add(buf, base + s * STEP_N, h, 0.22 if s % 4 else 0.3)
        if fill_last and i == bars - 1:                     # รัวปิดท่อน
            for k, s in enumerate((12, 13, 14, 15)):
                n = int(0.07 * SR)
                t = noise(n, hold_hz=6000) * ad(n, 0.001, 2.0)
                add(buf, base + s * STEP_N, t, 0.35 + 0.12 * k)


def make_bgm():
    """เพลงวน 52 ห้อง ~95 วินาที: intro -> A -> A' -> B -> A -> B -> A'"""
    plan = [
        ("intro", CH_INTRO, None, 4, False),
        ("A",  CH_A, LEAD_A,  8, False),
        ("A2", CH_A, LEAD_A2, 8, True),
        ("B",  CH_B, LEAD_B,  8, False),
        ("A",  CH_A, LEAD_A,  8, True),
        ("B",  CH_B, LEAD_B,  8, False),
        ("A2", CH_A, LEAD_A2, 8, True),
    ]
    total_bars = sum(p[3] for p in plan)
    n_total = total_bars * STEPS_PER_BAR * STEP_N
    lead = np.zeros(n_total)
    arp = np.zeros(n_total)
    bass = np.zeros(n_total)
    drums = np.zeros(n_total)

    bar = 0
    for name, chords, patterns, bars, fill in plan:
        render_bass(bass, bar, chords)
        render_arp(arp, bar, chords)
        if patterns is not None:
            render_lead(lead, bar, bars, patterns)
            render_drums(drums, bar, bars, fill)
        elif bars >= 3:
            render_drums(drums, bar + 2, bars - 2)   # กลองเข้าครึ่งหลังของ intro
        bar += bars

    mix_l = 0.34 * lead + 0.17 * arp + 0.30 * bass + 0.30 * drums
    mix_r = 0.34 * lead + 0.17 * arp + 0.30 * bass + 0.30 * drums
    # แพนเล็กน้อยให้มีมิติ: เมโลดี้ขวา อาร์เพจจิโอซ้าย
    mix_l += 0.07 * arp - 0.05 * lead
    mix_r += 0.07 * lead - 0.05 * arp

    st = np.stack([mix_l, mix_r], axis=1)
    st = np.tanh(st * 1.15)                      # ซอฟต์คลิปกันเสียงแตก
    st = st / np.max(np.abs(st)) * 0.82
    return total_bars, st


def write_bgm(stereo):
    tmp = os.path.join(os.path.dirname(BGM_PATH), "_bgm_tmp.wav")
    pcm = (np.clip(stereo, -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(tmp, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("  !! ffmpeg not found - left a temporary wav at", tmp)
        return False
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", tmp,
                    "-c:a", "libvorbis", "-q:a", "3", BGM_PATH], check=True)
    os.remove(tmp)
    print("  %-24s %6.2f s  %.0f KB" % (os.path.basename(BGM_PATH),
                                        len(stereo) / SR,
                                        os.path.getsize(BGM_PATH) / 1024))
    return True


def main():
    print("SFX:")
    write_wav(os.path.join(FX_DIR, "jump.wav"), sfx_jump())
    write_wav(os.path.join(FX_DIR, "coin_pickup.wav"), sfx_coin())
    write_wav(os.path.join(FX_DIR, "hurt.wav"), sfx_hurt())
    write_wav(os.path.join(FX_DIR, "explosion.wav"), sfx_explosion())
    write_wav(os.path.join(FX_DIR, "level_complete.wav"), sfx_level_complete())

    print("BGM:")
    bars, stereo = make_bgm()
    print("  %d bars @ %d BPM" % (bars, BPM))
    write_bgm(stereo)


if __name__ == "__main__":
    sys.exit(main())
