"""Synthesises the pogo bounce sounds (original, pure Python stdlib): a spring "boing" that rings briefly plus a low thud and a click for the landing.
Four variants with different pitch and ring so consecutive hops do not sound identical; the sound script lists all four and the engine picks one at random.
  python tools/make_pogo_sound.py     writes Contents/mods/ImpracticalTransport/42/media/sound/pogo_bounce_{1..4}.wav (16-bit mono 22.05 kHz, ~17 KB each)"""
import math, pathlib, random, struct, wave
OUT = pathlib.Path(__file__).resolve().parents[1] / "Contents/mods/ImpracticalTransport/42/media/sound"
RATE, LENGTH = 22050, 0.38

def bounce(seed):
    rnd = random.Random(seed)
    n = int(RATE * LENGTH)
    thud_f = rnd.uniform(70, 95)            # body of the landing
    ring_f = rnd.uniform(240, 340)          # the spring
    wob = rnd.uniform(18, 30)               # spring wobble (FM rate)
    out, noise = [], 0.0
    for i in range(n):
        t = i / RATE
        thud = math.sin(2 * math.pi * (thud_f * 1.8 * math.exp(-t * 14) + thud_f) * t) * math.exp(-t * 16)
        ring = sum(math.sin(2 * math.pi * ring_f * k * t + 2.5 * math.sin(2 * math.pi * wob * t) * math.exp(-t * 9)) * a * math.exp(-t * d)
                   for k, a, d in ((1, 0.5, 11), (2.76, 0.3, 16), (5.4, 0.15, 24)))      # inharmonic partials = metal
        noise = 0.55 * noise + rnd.uniform(-1, 1)      # low-passed noise for the click
        click = noise * math.exp(-t * 150) * 0.8
        out.append(1.4 * thud + 0.6 * ring + click)
    peak = max(abs(v) for v in out)
    fade = int(RATE * 0.02)
    return [v / peak * 0.95 * min(1, (n - i) / fade) for i, v in enumerate(out)]      # loud: normalised to 95% of full scale

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for k in range(1, 5):
        samples = bounce(k)
        assert max(abs(v) for v in samples) <= 0.96 and len(samples) > 1000
        with wave.open(str(OUT / f"pogo_bounce_{k}.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
            w.writeframes(b"".join(struct.pack("<h", int(v * 32767)) for v in samples))
        print("wrote", f"pogo_bounce_{k}.wav", len(samples), "samples")
