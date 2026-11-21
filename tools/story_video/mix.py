"""Ajoute une voix off à une vidéo « Histoire de clinique » déjà rendue par build.py.

  python3 tools/story_video/mix.py --images /chemin/table_musique --voice voix.mp3 --out ads/video/Histoire_X_voix

--images = préfixe des fichiers rendus par build.py sans voix (<préfixe>_916.mp4 et <préfixe>_45.mp4).
La musique (même nappe que build.py) remonte dans les silences et descend de ~10 dB sous la voix ;
la voix est normalisée (-16 LUFS) et commence à 0 s (les « debut » du JSON doivent être calés dessus).
"""
import argparse, importlib.util, os, re, subprocess, tempfile, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('build', os.path.join(HERE, 'build.py'))
build = importlib.util.module_from_spec(spec); spec.loader.exec_module(build)

def dur(path):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path]).decode())

def speech_intervals(voice, total):
    """intervalles où la voix parle, déduits des silences (≥ 0,35 s sous -35 dB)"""
    log = subprocess.run(['ffmpeg', '-hide_banner', '-i', voice, '-af', 'silencedetect=noise=-35dB:d=0.35', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r'silence_start: ([0-9.]+)', log)]
    ends = [float(x) for x in re.findall(r'silence_end: ([0-9.]+)', log)]
    sil = list(zip(starts, ends + [total] * (len(starts) - len(ends))))
    out, t = [], 0.0
    for a, e in sil:
        if a > t: out.append((t, a))
        t = e
    if t < total: out.append((t, total))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--images', required=True); ap.add_argument('--voice', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--duck', type=float, default=0.33, help='gain de la musique sous la voix (0,33 ≈ -9,6 dB)')
    ap.add_argument('--music', type=float, default=0.85, help='gain global de la musique')
    a = ap.parse_args()
    tmp = tempfile.mkdtemp()
    total = dur(f'{a.images}_916.mp4')
    vdur = dur(a.voice)
    sr = 48000
    music = os.path.join(tmp, 'm.wav'); build.make_music(total, music, .32)
    with wave.open(music) as w: y = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32767
    t = np.arange(len(y)) / sr
    target = np.ones_like(t)
    for s, e in speech_intervals(a.voice, vdur):
        target[(t >= s - 0.15) & (t <= e + 0.35)] = a.duck
    env = np.empty_like(target); g = 1.0; da = 1 / (0.25 * sr); dr = 1 / (0.9 * sr)
    for i, x in enumerate(target):
        g = max(x, g - da) if x < g else min(x, g + dr); env[i] = g
    y *= env
    mduck = os.path.join(tmp, 'm_duck.wav')
    with wave.open(mduck, 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((y * 32767).astype(np.int16).tobytes())
    vnorm = os.path.join(tmp, 'v.wav')
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', a.voice, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000', '-ac', '2', vnorm])
    mix = os.path.join(tmp, 'mix.wav')
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', vnorm, '-i', mduck, '-filter_complex',
                           f'[0:a]apad[v];[1:a]aresample=48000,aformat=channel_layouts=stereo,volume={a.music}[m];'
                           '[v][m]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.89:level=false[a]',
                           '-map', '[a]', '-t', str(total), '-c:a', 'pcm_s16le', mix])
    for tag in ('916', '45'):
        out = f'{a.out}_{tag}.mp4'
        subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', f'{a.images}_{tag}.mp4', '-i', mix, '-map', '0:v', '-map', '1:a',
                               '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', str(total), '-movflags', '+faststart', out])
        print(out)
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-ss', '1', '-i', f'{a.out}_45.mp4', '-frames:v', '1', '-q:v', '3', f'{a.out}_45.jpg'])

if __name__ == '__main__':
    main()
