"""Build offline creature voices. Requires numpy, scipy and ffmpeg.

CC0 sources are cached under .local/monster_audio; see the shipped credits.
Run: python tools/build_monster_audio.py [--download]
"""
from pathlib import Path
import subprocess
import sys
import urllib.request

import numpy as np
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.local/monster_audio'
DEST = ROOT / 'game/assets/audio/monsters'
SR = 44100
SOURCES = ['1544', '0682', '1659', '0305', '1299']


def read(number, start, duration, pitch=1.0):
    result = subprocess.run([
        'ffmpeg', '-v', 'error', '-ss', str(start), '-i', str(CACHE / (number + '.mp3')),
        '-t', str(duration), '-af', 'asetrate=%s,aresample=%s' % (48000 * pitch, SR),
        '-ac', '1', '-f', 'f32le', '-'], check=True, stdout=subprocess.PIPE)
    return np.frombuffer(result.stdout, dtype=np.float32).copy()


def band(x, low, high):
    return sosfilt(butter(3, [low, high], btype='bandpass', fs=SR, output='sos'), x)


def normalize(x):
    return x / max(np.max(np.abs(x)), 0.00001)


def throat(duration, base, seed, pain=False):
    """Original rough vocal tract: irregular pulses, formants and breath."""
    rng = np.random.RandomState(seed)
    t = np.arange(int(SR * duration)) / SR
    u = t / duration
    contour = (1 + .6 * np.sin(np.pi * u)) * (1 - .48 * u)
    frequency = base * contour * (1 + .04 * np.sin(t * 70) + .025 * np.sin(t * 117))
    phase = np.cumsum(frequency) / SR * 2 * np.pi
    pulses = sum(np.sin(phase * k + .12 * np.sin(t * 31)) / k for k in range(1, 19))
    voice = .5 * band(pulses, 220, 700) + band(pulses, 900 if pain else 650, 2100)
    voice += .17 * band(rng.normal(0, 1, len(t)), 300, 3200)
    return normalize(voice) * np.sin(np.pi * u) ** .65 * (1 + .16 * np.sin(t * 93))


def write(name, x):
    x = band(x, 90, 6500)
    # Consistent audible bodies without clipping; soften edits and leave no long tails.
    x = normalize(x)
    rms = np.sqrt(np.mean(x * x))
    x *= min(.82, .19 / max(rms, .0001))
    fade = min(int(SR * .012), len(x) // 4)
    x[:fade] *= np.linspace(0, 1, fade)
    x[-fade:] *= np.linspace(1, 0, fade)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SR),
                    '-ac', '1', '-i', '-', '-c:a', 'libvorbis', '-q:a', '5',
                    str(DEST / (name + '.ogg'))], input=x.astype(np.float32).tobytes(), check=True)
    print(name, round(len(x) / SR, 2), flush=True)


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    DEST.mkdir(parents=True, exist_ok=True)
    for number in SOURCES:
        if not (CACHE / (number + '.mp3')).exists():
            if '--download' not in sys.argv:
                raise SystemExit('Missing CC0 source %s; run with --download.' % number)
            urllib.request.urlretrieve('https://bigsoundbank.com/UPLOAD/mp3/' + number + '.mp3',
                                       CACHE / (number + '.mp3'))
    for i in range(3):
        # Isolate the quieter crying dog between the foreground barks.
        cry = band(read('1544', [2.12, 2.88, 5.65][i], [.65, .68, .57][i], .94 - i * .025), 380, 5200)
        write('wolf_hurt_%d' % i, cry)
        write('wolf_attack_%d' % i, read('0682', [.02, .46, .92][i], .56, .72 + i * .035))
        write('wolf_death_%d' % i, read('1544', [2.10, 2.85, 5.6][i], .94, .78 + i * .02))
        grunt = read('1659', [.35, 2.15, 4.0][i], .58, .76 + i * .03)
        write('boar_attack_%d' % i, grunt)
        for event, duration in [('hurt', .53), ('death', 1.04)]:
            squeal = throat(duration, 360 + i * 31, 40 + i, True)
            n = min(len(squeal), len(grunt))
            squeal[:n] += normalize(grunt[:n]) * .32
            write('boar_%s_%d' % (event, i), squeal)
        for event, duration, base in [('hurt', .68, 155), ('attack', .63, 100), ('death', 1.25, 110)]:
            scream = throat(duration, base + i * 9, 80 + i, event != 'attack') * .72
            creak = normalize(read('0305', .12 + i * .22, duration * .7, .62 + i * .035))
            twigs = normalize(read('1299', .15 + i * .9, .25, .8))
            n = min(len(scream), len(creak))
            scream[:n] += creak[:n] * .50
            n = min(len(scream), len(twigs))
            scream[:n] += twigs[:n] * .25
            # Brief early reflection makes a hollow wooden throat.
            scream += np.concatenate([np.zeros(1100), scream[:-1100]]) * .18
            write('mossling_%s_%d' % (event, i), scream)


if __name__ == '__main__':
    main()
