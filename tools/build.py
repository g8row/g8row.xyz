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
DECO = dict(cookie=(9, .1), clover=(4, .3), flower=(8, .16), burst=(12, .07))
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
t = t.replace('{{deco-music}}', deco('burst', 'l', nrows=30))


# listening: a last.fm snapshot (tools/lastfm.json) baked in with a first frame of each drawing.
# site.js redraws the same things live; keep the two in step.
import json, datetime
fm = json.load(open(SP + 'lastfm.json'))
esc = html.escape
rnd = lambda v: math.floor(v + 0.5)  # js Math.round
day = lambda u: datetime.datetime.fromtimestamp(u, datetime.timezone.utc).strftime('%-d %b').lower() if u else 'now'
RMP = " .,:;-=+*#%"
blank = lambda R, C: [[' '] * C for _ in range(R)]
join = lambda g: '\n'.join(''.join(r).rstrip() for r in g)
def stroke(dx, dy):
    a = (math.degrees(math.atan2(dy * 2, dx)) + 180) % 180
    return '─' if a < 22.5 or a >= 157.5 else '╲' if a < 67.5 else '│' if a < 112.5 else '╱'
def layers(R, C, n, base=()):
    L = [[r[:] for r in base[i]] if i < len(base) else blank(R, C) for i in range(n)]
    def put(i, y, x, ch):
        if 0 <= y < R and 0 <= x < C:
            for g in L: g[y][x] = ' '
            L[i][y][x] = ch
    return L, put

# deck, record still and the arm resting
VC, VR, D, PIV, REST, ARM = 80, 34, 68, (76, 2), math.pi / 2, 27.85
L, put = layers(VR, VC, 3)
for y in range(VR):
    for x in range(D):
        u = (x + .5 - D / 2) / (D / 2); v = (y + .5 - VR / 2) / (VR / 2); r = math.hypot(u, v); th = math.atan2(v, u)
        if r > 1 or .27 <= r < .3: continue
        if r < .27:
            d = abs((th % (2 * math.pi) + 3 * math.pi) % (2 * math.pi) - math.pi)
            put(1, y, x, '·') if r < .04 else put(2, y, x, '█' if d < .14 else '▓' if r > .225 else ' ' if r > .2 else '░')
            continue
        if any(abs(r - g) < .018 for g in (.5, .66, .82)): continue
        if r > .965: put(1, y, x, ':'); continue
        sp = abs(math.cos(th + .6)) ** 24 * (.4 + .6 * r)
        dot = ':' if math.floor(r * 40) % 2 else '.'
        if sp > .2: put(1, y, x, dot)
        else: put(0, y, x, dot)
for rr, off in ((.62, 0), (.86, 2.2), (.74, 4.1)):
    put(1, rnd(VR / 2 - .5 + math.sin(off) * rr * VR / 2), rnd(D / 2 - .5 + math.cos(off) * rr * D / 2), '*')
px, py, c_, s_ = PIV[0] + .5, (PIV[1] + .5) * 2, math.cos(REST), math.sin(REST)
ln = lambda cls, d0, d1: '<line class="%s" x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"/>' % (cls, px + c_ * d0, py + s_ * d0, px + c_ * d1, py + s_ * d1)
t = t.replace('{{v-arm}}', '<svg class="v-arm" viewBox="0 0 %d %d" preserveAspectRatio="none">%s%s%s<circle cx="%.1f" cy="%.1f" r="2.4"/><circle class="dot" cx="%.1f" cy="%.1f" r=".7"/></svg>'
              % (VC, VR * 2, ln('cw', -6.5, -3), ln('arm', 0, ARM - 2.5), ln('head', ARM - 3, ARM), px, py, px, py))
for k, g in zip(('v-dim', 'v-hi', 'v-acc'), L): t = t.replace('{{%s}}' % k, join(g))

# genres radar, fully grown, no sweep. svg units: x = column, y = row * 2 (cells are twice as tall as wide)
RC, RR, CX, CY, RY, RX = 64, 23, 32, 11, 9, 18
def axis(k):
    a = math.radians(-90 + 60 * k); return math.cos(a), math.sin(a)
def inside(x, y, P):
    c = False; j = len(P) - 1
    for i in range(len(P)):
        if (P[i][1] > y) != (P[j][1] > y) and x < (P[j][0] - P[i][0]) * (y - P[i][1]) / (P[j][1] - P[i][1]) + P[i][0]: c = not c
        j = i
    return c
sv = lambda pts: ' '.join('%.2f,%.2f' % (x + .5, (y + .5) * 2) for x, y in pts)
OUTER = [(CX + axis(k)[0] * RX, CY + axis(k)[1] * RY) for k in range(6)]
G = fm['genres']; assert len(G) == 6
P = [(CX + axis(k)[0] * RX * max(.12, g['v']), CY + axis(k)[1] * RY * max(.12, g['v'])) for k, g in enumerate(G)]
L, put = layers(RR, RC, 5)
for y in range(RR):
    for x in range(RC):
        if not inside(x, y, OUTER): continue
        rho = math.hypot((x - CX) / RX, (y - CY) / RY)
        if inside(x, y, P): put(1, y, x, '··:::+'[min(5, math.floor(rho * 6))])
        elif x % 2 == 0: put(0, y, x, '·')
put(0, CY, CX, '+') if not inside(CX, CY, P) else None
dias = ''
for k, g in enumerate(G):
    ax, ay = axis(k); name = g['g'][:12]; vx = CX + ax * RX; vy = rnd(CY + ay * RY)
    y = vy - 2 if k == 0 else vy + 2 if k == 3 else vy
    x0 = rnd(CX - len(name) / 2) if k in (0, 3) else rnd(vx) + 3 if ax > 0 else rnd(vx) - 2 - len(name)
    for i, c in enumerate(name): put(3, y, x0 + i, c)
    dias += '<i class="dia" style="--c:%.2f;--r:%.2f"></i>' % P[k]
svg = ('<svg class="r-svg" viewBox="0 0 %d %d" preserveAspectRatio="none">' % (RC, RR * 2) +
       ''.join('<polygon class="ring%s" points="%s"/>' % ('' if f == 1 else ' in', sv([(CX + (x - CX) * f, CY + (y - CY) * f) for x, y in OUTER])) for f in (1 / 3, 2 / 3, 1)) +
       ''.join('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"/>' % (CX + .5, (CY + .5) * 2, x + .5, (y + .5) * 2) for x, y in OUTER) +
       '<polygon class="poly" points="%s"/></svg>' % sv(P))
for k, g in zip(('r-dim', 'r-fill', 'r-sw', 'r-lbl', 'r-hot'), L): t = t.replace('{{%s}}' % k, esc(join(g)))
t = t.replace('{{r-dias}}', svg + dias).replace('{{fm-genres}}', esc(', '.join(g['g'] for g in G)))

# text
last = fm['recent'][0]
t = t.replace('{{fm-json}}', json.dumps(fm, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'))
t = t.replace('{{fm-live}}', ' live' if fm['now'] else '').replace('{{fm-state}}', 'now playing' if fm['now'] else 'last played')
t = t.replace('{{fm-when}}', '' if fm['now'] else day(last['u']))
t = t.replace('{{fm-track}}', esc(last['t'])).replace('{{fm-artist}}', esc(last['a']))
t = t.replace('{{fm-recent}}', ''.join('<li><time>%s</time><span>%s</span><span>%s</span></li>' % (day(r['u']), esc(r['t']), esc(r['a'])) for r in fm['recent'][1:5]))
most = max([a['n'] for a in fm['top']] + [1])
def bar(a):
    f = rnd(a['n'] / most * 30); name = a['a'] if len(a['a']) <= 14 else a['a'][:13] + '…'
    return '<span>%s</span><b>%s</b><i>%s</i><em>%s\n</em>' % (esc(name.ljust(16)), '━' * f, '─' * (30 - f), str(a['n']).rjust(5))
t = t.replace('{{fm-bars}}', ''.join(bar(a) for a in fm['top']))
t = t.replace('{{fm-scrobbles}}', '{:,}'.format(fm['scrobbles'])).replace('{{fm-artists}}', '{:,}'.format(fm['artists']))
t = t.replace('{{fm-since}}', datetime.datetime.fromtimestamp(fm['since'], datetime.timezone.utc).strftime('%Y'))
assert '{{' not in t, t[t.index('{{'):t.index('{{') + 30]
open(OUT, 'w').write(t)
print('ok', len(t))
