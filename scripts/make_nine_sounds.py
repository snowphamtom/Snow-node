"""Nine Circles: 9 distinct sounds, one per circle.
8s title + 9x17s circles + 7s outro = 168.0s. Each circle has its own sonic
identity; the set descends in pitch and thins toward Treachery's frozen silence.
"""
import numpy as np, wave

SR = 44100
DUR = 168.0
N = int(SR * DUR)
rng = np.random.default_rng(11)
bounds = [0.0, 8.0] + [8.0 + 17.0 * k for k in range(1, 10)] + [168.0]
roots = [55.0 * 2 ** (-k / 12.0) for k in range(9)]  # semitone descent, 9 circles

def lp(x, ms=20.0):
    k = max(1, int(SR * ms / 1000.0))
    return np.convolve(x, np.ones(k) / k, mode='same')

def sines(tt, freqs, amps, seed):
    r = np.random.default_rng(seed)
    s = np.zeros_like(tt)
    for f, a in zip(freqs, amps):
        s += a * np.sin(2 * np.pi * f * tt + r.uniform(0, 6.28))
    return s

def strike(tt, t0, root, ratios, amps, decay=3.0, base=0.0):
    s = np.zeros_like(tt)
    i0 = int(t0 * SR)
    L = len(tt) - i0
    if L <= 0:
        return s
    tl = np.arange(L) / SR
    d = np.exp(-tl * decay)
    r = np.random.default_rng(int(t0 * 10))
    for ratio, a in zip(ratios, amps):
        s[i0:] += base + a * d * np.sin(2 * np.pi * root * ratio * tl + r.uniform(0, 6.28))
    return s

def circle_sound(idx, root):
    """idx 0..8. Returns 17s mono."""
    M = int(17 * SR)
    tt = np.arange(M) / SR
    r = np.random.default_rng(200 + idx)
    if idx == 0:  # LIMBO - hollow wind
        wind = lp(r.standard_normal(M), ms=120.0)
        wind *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.06 * tt)
        s = 0.11 * wind / (np.abs(wind).max() + 1e-9)
        s += sines(tt, [root, root * 2.0], [0.14, 0.05], 201)
    elif idx == 1:  # LUST - breathy swirl
        br = r.standard_normal(M)
        br = lp(br, ms=8.0) - lp(br, ms=60.0)  # bandy
        swirl = 0.5 + 0.5 * np.sin(2 * np.pi * 0.13 * tt)
        s = 0.10 * br / (np.abs(br).max() + 1e-9) * swirl
        s += sines(tt, [root, root * 1.005, root * 2.01], [0.09, 0.09, 0.04], 202) * (0.6 + 0.4 * swirl)
    elif idx == 2:  # GLUTTONY - low gurgle
        wob = 1 + 0.02 * np.sin(2 * np.pi * 0.9 * tt)
        g = np.sin(2 * np.pi * root * wob * tt) * (0.45 + 0.55 * np.sin(2 * np.pi * 6.3 * tt) ** 2)
        s = 0.20 * g + 0.07 * lp(r.standard_normal(M), ms=80.0)
    elif idx == 3:  # GREED - metallic strikes
        s = np.zeros(M)
        for t0 in np.arange(1.0, 17.0, 4.2):
            s += strike(tt, t0, root, [1, 2.76, 5.40, 8.93], [0.16, 0.10, 0.06, 0.03], decay=2.2)
        s += sines(tt, [root * 8.1, root * 12.2], [0.012, 0.008], 204)
    elif idx == 4:  # WRATH - FM growl + turbulence
        mod = np.sin(2 * np.pi * root * 1.5 * tt)
        car = np.sin(2 * np.pi * root * 2.0 * tt + 8.0 * mod)
        s = 0.16 * np.tanh(2.0 * car)
        turb = lp(r.standard_normal(M), ms=15.0)
        gate = (0.5 + 0.5 * np.sin(2 * np.pi * 2.7 * tt)) ** 2
        s += 0.10 * turb / (np.abs(turb).max() + 1e-9) * gate
    elif idx == 5:  # HERESY - dissonant cluster
        s = sines(tt, [root, root * 1.0595, root * 1.1225, root * 0.5],
                  [0.11, 0.11, 0.09, 0.10], 206)
        s *= 0.8 + 0.2 * np.sin(2 * np.pi * 0.4 * tt)
    elif idx == 6:  # VIOLENCE - impacts
        s = np.zeros(M)
        t0 = 0.8
        rr = np.random.default_rng(207)
        while t0 < 16.0:
            s += strike(tt, t0, 52.0, [1, 1.5], [0.34, 0.12], decay=5.0)
            nb = int(0.25 * SR)
            i0 = int(t0 * SR)
            if i0 + nb < M:
                s[i0:i0 + nb] += 0.16 * lp(r.standard_normal(nb), ms=6.0)
            t0 += rr.uniform(1.6, 3.1)
    elif idx == 7:  # FRAUD - deceptive glides
        s = np.zeros(M)
        glides = [(0.0, 2.0, 3.5), (5.5, 3.2, 1.6), (11.0, 1.8, 4.2)]
        for t0, f0m, f1m in glides:
            i0, i1 = int(t0 * SR), int(min(t0 + 5.0, 17.0) * SR)
            tl = np.arange(i1 - i0) / SR
            f = root * np.linspace(f0m, f1m, i1 - i0)
            ph = 2 * np.pi * np.cumsum(f) / SR
            e = np.sin(np.pi * np.arange(i1 - i0) / (i1 - i0)) ** 2
            s[i0:i1] += 0.11 * e * np.sin(ph)
        s += sines(tt, [root * 6.03, root * 9.1], [0.015, 0.010], 208)
    else:  # TREACHERY - frozen, near-silence, sparse pings
        s = sines(tt, [root], [0.020], 209)
        for t0, mult in [(3.0, 16.0), (8.5, 24.0), (13.0, 19.0)]:
            s += strike(tt, t0, root, [mult], [0.11], decay=1.1)
    return s

segs = []
# title: sparse fade of limbo's wind
segs.append(circle_sound(0, roots[0])[:int(8 * SR)] * 0.5)
for k in range(9):
    segs.append(circle_sound(k, roots[k]))
# outro: treachery's tail, decaying
out = circle_sound(8, roots[8])[:int(7 * SR)] * np.linspace(1, 0.15, int(7 * SR))
segs.append(out)

mix = np.zeros(N)
pos = 0
XF = int(2.0 * SR)  # 2s crossfade
for j, sg in enumerate(segs):
    n0 = pos
    n1 = pos + len(sg)
    if j > 0:  # crossfade with previous tail
        ov = min(XF, len(sg), n0)
        fade_out = np.linspace(1, 0, ov)
        fade_in = np.linspace(0, 1, ov)
        mix[n0 - ov:n0] *= fade_out
        sg = sg.copy()
        sg[:ov] *= fade_in
        n0 -= ov
    mix[n0:n0 + len(sg)] += sg[:max(0, min(len(sg), N - n0))]
    pos = n0 + len(sg)
    if pos >= N:
        break
mix = mix[:N]

stereo = np.stack([mix, mix], axis=1)
wob = 0.02 * np.sin(2 * np.pi * 0.11 * np.arange(N) / SR)
stereo[:, 0] *= 1 + wob
stereo[:, 1] *= 1 - wob
fi, fo = int(3 * SR), int(5 * SR)
stereo[:fi] *= np.linspace(0, 1, fi)[:, None]
stereo[-fo:] *= np.linspace(1, 0, fo)[:, None]
peak = np.abs(stereo).max()
stereo *= 10 ** (-3 / 20) / peak
pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)
with wave.open('/tmp/nine_sounds.wav', 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('wrote /tmp/nine_sounds.wav', f'{len(pcm)/SR:.1f}s')
