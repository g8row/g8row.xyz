import math, html
# builds site/index.html from tools/index.tpl.html: m3 shape paths, the baked hero frame,
# the bench board drawing and the ascii background shapes. run: python3 tools/build.py
import os
SP = os.path.dirname(os.path.abspath(__file__)) + '/'
OUT = SP + '../site/index.html'
t = open(SP + 'index.tpl.html').read()

def shape_path(n, a, N=96):
    p = []
    for i in range(N):
        th = i / N * 2 * math.pi; r = 44 * (1 + a * math.cos(n * th)) / (1 + a)
        p.append('%.1f %.1f' % (50 + r * math.cos(th), 50 + r * math.sin(th)))
    return 'M' + 'L'.join(p) + 'Z'
SH = dict(cookie=(9, .07), clover=(4, .2), flower=(8, .12), burst=(12, .05))
for k, v in SH.items(): t = t.replace('{{%s}}' % k, shape_path(*v))
t = t.replace('{{wave}}', 'M0 8' + ''.join(' Q%d 1 %d 8 T%d 8' % (x + 10, x + 20, x + 40) for x in range(0, 800, 40)))
t = t.replace('{{hero-lines}}', open(SP + 'hero-lines.txt').read()).replace('{{hero-peaks}}', open(SP + 'hero-peaks.txt').read())

# pad: a pen stroke with pressure (short segments of varying width) revealed by a mask, plus a frame-time strip
def pad():
    N, loops, pts = 252, 7, []
    for i in range(N + 1):
        u = i / N; th = 2 * math.pi * loops * u; a = 0.75 + 0.25 * math.sin(u * 9)
        pts.append((40 + 400 * u - 20 * math.sin(th), 92 + 8 * math.sin(u * 7) - 36 * a * math.cos(th) * (0.6 + 0.4 * math.sin(math.pi * u))))
    d = 'M' + 'L'.join('%.1f %.1f' % q for q in pts)
    segs, step = [], 12
    for i in range(0, N, step):
        u = (i + step / 2) / N
        w = 1.2 + 3.2 * math.sin(math.pi * u) ** 0.6 * (0.8 + 0.2 * math.sin(u * 40))
        segs.append('<path d="M%s" stroke-width="%.1f"/>' % ('L'.join('%.1f %.1f' % q for q in pts[i:i + step + 1]), w))
    anim = 'dur="7s" repeatCount="indefinite"'
    ink = ('<svg class="ink" viewBox="0 0 480 170"><defs><pattern id="pd" width="16" height="16" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1"/></pattern>'
           '<mask id="pm" maskUnits="userSpaceOnUse"><path d="%s" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" pathLength="1" stroke-dasharray="1 2" stroke-dashoffset="1">'
           '<animate attributeName="stroke-dashoffset" values="1;0;0" keyTimes="0;.62;1" %s/></path></mask></defs>'
           '<rect width="480" height="170" fill="url(#pd)"/>'
           '<g class="strokes" mask="url(#pm)"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.82;.94;1" %s/>%s</g>'
           '<g class="tip"><animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;.62;.66;.98;1" %s/>'
           '<animateMotion path="%s" keyPoints="0;1;1" keyTimes="0;.62;1" calcMode="linear" %s/>'
           '<circle r="11" class="hover"/><circle r="3.5"/></g></svg>') % (d, anim, anim, ''.join(segs), anim, d, anim)
    seed, bars = 7, []
    def rnd():
        nonlocal seed; seed = seed * 16807 % 2147483647; return seed / 2147483647
    hs = [3.2 + 2.6 * rnd() + (1.4 * rnd() if rnd() < .15 else 0) for _ in range(96)]
    for k in (0, 480):
        for i, h in enumerate(hs):
            bars.append('M%d 56v-%d' % (k + i * 5 + 1, round(h * 5)))
    graph = ('<svg class="frames" viewBox="0 0 480 56"><path class="scroll" d="%s"/>'
             '<line x1="0" x2="480" y1="14.5" y2="14.5"/><text x="480" y="10" text-anchor="end">8.3 ms</text></svg>') % ''.join(bars)
    return ink + graph
t = t.replace('{{pad}}', pad())
t = t.replace('{{pins}}', '\n          '.join(
    ''.join('<circle class="pin" cx="%d" cy="%d" r="2.2"/>' % (254 + 10 * i, y) for i in range(13)) for y in (96, 106)))

# bench board: 46 columns, the js lights parts of it
inner = 34
rows = ["  mains " + "─" * 9 + "┐", " " * 17 + "│", "   ┌" + "─" * 13 + "┴" + "─" * 20 + "┐"]
for c in [" ▓▓ ▓▓ usb              ┌──┐ eth ", "                        └──┘     ",
          "  ┌──────────┐  ::::::::::::::   ", "  │░░░░░░░░░░│  ::::::::::::::   ",
          "  │░░ soc  ░░│                   ", "  │░░░░░░░░░░│   o pwr    o act  ",
          "  └──────────┘                   "]:
    rows.append("   │" + c.ljust(inner) + "│")
u = " [sd]                    uart "
rows.append("   │" + u + "─" * (inner - len(u)) + "┼" + "─" * 7)
rows.append("   └" + "─" * inner + "┘")
assert all(len(r) <= 46 for r in rows), [len(r) for r in rows]
assert rows[2][17] == "┴" and rows[0][17] == "┐"
t = t.replace('{{board}}', '\n'.join(r.rstrip() for r in rows))

# background decoration: an ascii-shaded m3 shape inside construction lines
RAMP = " .,:;-=+*#%"
DECO = dict(cookie=(9, .1), clover=(4, .3), flower=(8, .16))
def deco(name, side, fs=10, nrows=34):
    n, a = DECO[name]
    cw = fs * 0.6; H = nrows * fs; R = 0.42 * H; cols = int(2 * R * 1.3 / cw); W = cols * cw
    L = (-0.55, -0.7, 0.6); ln = math.sqrt(sum(v * v for v in L)); L = [v / ln for v in L]
    out = []
    for row in range(nrows):
        s = ''
        for col in range(cols):
            x = (col + .5) * cw - W / 2; y = (row + .5) * fs - H / 2
            rho = math.hypot(x, y); th = math.atan2(y, x)
            e = R * (1 + a * math.cos(n * th)) / (1 + a)
            if rho < e:
                tt = rho / e; z = math.sqrt(max(0, 1 - tt * tt)) * 1.2
                nx, ny = x / e, y / e; nl = math.sqrt(nx * nx + ny * ny + z * z)
                b = max(0, (nx * L[0] + ny * L[1] + z * L[2]) / nl)
                s += '%' if tt > 0.93 else RAMP[1 + min(len(RAMP) - 2, int(b * (len(RAMP) - 2) + .5))]
            else:
                s += ' '
        out.append(s.rstrip())
    cx, cy = W / 2, H / 2; r1 = R + 8; r2 = R * 1.32
    ang = math.radians(-28); dx, dy = math.cos(ang) * 2000, math.sin(ang) * 2000
    marks = [(cx, cy), (cx - r1, cy), (cx + r1, cy), (cx, cy - r1), (cx, cy + r1)]
    svg = ('<svg viewBox="0 0 %.0f %.0f" style="overflow:visible">' % (W, H) +
           '<line x1="-3000" y1="%.1f" x2="3000" y2="%.1f"/>' % (cy, cy) +
           '<line x1="%.1f" y1="-1500" x2="%.1f" y2="1500"/>' % (cx, cx) +
           '<line class="dash" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (cx - dx, cy - dy, cx + dx, cy + dy) +
           '<circle cx="%.1f" cy="%.1f" r="%.1f"/>' % (cx, cy, r1) +
           '<circle class="dash" cx="%.1f" cy="%.1f" r="%.1f"/>' % (cx, cy, r2) +
           ''.join('<rect x="%.1f" y="%.1f" width="7" height="7"/>' % (mx - 3.5, my - 3.5) for mx, my in marks) +
           '</svg>')
    lbl = '<span class="lbl" style="left:%.0fpx;top:%.0fpx;transform:translateX(-50%%)">%s · n %d · a %.2f</span>' % (cx, cy + r2 + 10, name, n, a)
    return ('<div class="deco" aria-hidden="true"><div class="glyph %s" style="width:%.0fpx;height:%.0fpx">%s<pre style="--fs:%dpx">\n%s</pre>%s</div></div>'
            % (side, W, H, svg, fs, '\n'.join(out), lbl))
t = t.replace('{{deco-work}}', deco('clover', 'r')).replace('{{deco-bench}}', deco('flower', 'l')).replace('{{deco-exp}}', deco('cookie', 'r', nrows=30))
assert '{{' not in t, t[t.index('{{'):t.index('{{') + 30]
open(OUT, 'w').write(t)
print('ok', len(t))
