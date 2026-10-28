// three small things, all optional: the page reads fine without this file.
// 1. hero: an ascii ridge-line field of moving sine waves
// 2. bench: an ascii board that powers on, flashes, boots and gets tested, with a serial console
// 3. cards: a soft light that follows the pointer
// animations pause off-screen and in background tabs, and stay still under prefers-reduced-motion.
(() => {
  const still = matchMedia("(prefers-reduced-motion: reduce)");

  // run fn(t) at most `fps` times a second while el is on screen
  function loop(el, fps, fn) {
    // the clock only runs while the element is animating, so it starts from 0 when first seen
    let visible = false, timer = 0, elapsed = 0, last = 0;
    const tick = () => {
      timer = 0;
      if (!visible || document.hidden || still.matches) { last = 0; return; }
      const now = performance.now();
      if (last) elapsed += Math.min(now - last, 250);
      last = now;
      fn(elapsed / 1000);
      timer = setTimeout(() => requestAnimationFrame(tick), 1000 / fps);
    };
    const run = () => { if (!timer) tick(); };
    new IntersectionObserver(([e]) => { visible = e.isIntersecting; run(); }).observe(el);
    document.addEventListener("visibilitychange", run);
    still.addEventListener("change", run);
  }

  const grid = (rows, cols) => Array.from({ length: rows }, () => new Array(cols).fill(" "));
  const text = g => g.map(r => r.join("").replace(/\s+$/, "")).join("\n");

  // 1. hero signal. the first frame (t = 2.4) is baked into the html.
  const signal = document.querySelector(".signal");
  if (signal) {
    const [dotsEl, linesEl, peaksEl] = signal.querySelectorAll("pre");
    const C = 84, R = 34, L = 18;
    const dots = grid(R, C);
    for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 3) dots[y][x] = ".";
    dotsEl.textContent = text(dots);

    const frame = t => {
      const lines = grid(R, C), peaks = grid(R, C);
      const top = new Array(C).fill(R); // highest row drawn so far per column, nearest ridge first
      for (let i = L - 1; i >= 0; i--) {
        const depth = i / (L - 1), base = 12 + i * 1.15, amp = 6 + depth * 10;
        const ys = new Array(C), hs = new Array(C);
        for (let x = 0; x < C; x++) {
          const u = (x / (C - 1)) * 2 - 1, env = Math.exp(-u * u * 2.6);
          const h = env * (0.55 * Math.sin(u * 5.2 + t * 0.9 + i * 0.45)
                         + 0.3 * Math.sin(u * 11.7 - t * 1.4 + i * 0.8)
                         + 0.15 * Math.sin(u * 23 + t * 2.1 + i * 1.7));
          hs[x] = env > 0.14 ? h : NaN;
          ys[x] = Math.round(base - Math.max(h, -0.2) * amp);
        }
        const next = top.slice();
        for (let x = 0; x < C; x++) {
          if (Number.isNaN(hs[x])) continue;
          const y = ys[x], prev = x > 0 && !Number.isNaN(hs[x - 1]) ? ys[x - 1] : y, after = x < C - 1 ? ys[x + 1] : y;
          const dy = after - prev;
          const ch = dy <= -2 ? "/" : dy >= 2 ? "\\" : depth < 0.45 ? "." : "-";
          const hot = hs[x] > 0.42 && depth > 0.3;
          // fill the vertical gap to the previous column so steep slopes stay connected
          const lo = Math.min(y, prev + (prev < y ? 1 : 0)), hi = Math.max(y, prev - (prev > y ? 1 : 0));
          for (let yy = lo; yy <= hi; yy++) {
            if (yy < 0 || yy >= R || yy >= top[x]) continue;
            (hot ? peaks : lines)[yy][x] = yy === y ? ch : prev < y ? "\\" : "/";
            if (yy < next[x]) next[x] = yy;
          }
        }
        for (let x = 0; x < C; x++) top[x] = next[x];
      }
      linesEl.textContent = text(lines);
      peaksEl.textContent = text(peaks);
    };
    loop(signal, 15, t => frame(2.4 + t * 0.7));
  }

  // 2. bench. the board drawing in the html is the template; this only lights parts of it.
  const bench = document.querySelector(".bench");
  if (bench) {
    const baseEl = bench.querySelector(".b-base"), hotEl = bench.querySelector(".b-hot");
    const barEl = bench.querySelector(".b-bar"), con = bench.querySelector(".console");
    const pills = bench.querySelectorAll("[data-stage]");
    const tpl = baseEl.textContent.split("\n");
    const R = tpl.length, C = Math.max(...tpl.map(l => l.length));
    const at = (r, c) => (tpl[r] || "")[c] || " ";
    const find = s => { for (let r = 0; r < R; r++) { const c = tpl[r].indexOf(s); if (c >= 0) return [r, c]; } };

    const soc = [];
    for (let r = 0; r < R; r++) for (let c = 0; c < C; c++) if (at(r, c) === "░") soc.push([r, c]);
    const pwr = find("o pwr"), act = find("o act");
    const [mr, mc] = find("mains"), corner = tpl[mr].indexOf("┐");
    const mains = [];
    for (let c = mc + 6; c <= corner; c++) mains.push([mr, c]);
    for (let r = mr + 1; at(r, corner) !== "┴"; r++) mains.push([r, corner]);
    const [ur, uc] = find("uart"), uart = [];
    for (let c = uc + 5; c < tpl[ur].length; c++) uart.push([ur, c]);

    const stages = [
      ["power", 1.6], ["flash", 3.2], ["boot", 3.4], ["test", 2.4], ["pass", 2.2],
    ];
    const total = stages.reduce((s, [, d]) => s + d, 0);
    const script = {
      power: [[0, "bench   power off"], [0.7, "bench   power on"]],
      flash: [[0, "bench   writing image.wic.gz"], [3.0, "bench   flash ok, checksum matches"]],
      boot: [[0, "U-Boot SPL 2024.07"], [0.4, "Trying to boot from MMC1"], [0.9, "Starting kernel ..."],
             [1.3, "[    0.000000] Booting Linux on CPU 0x0"], [1.9, "[    1.903214] mmc0: new SDHC card"],
             [2.6, "[    3.411870] systemd: multi-user.target"], [3.1, "board login: root"]],
      test: [[0.2, "test    boot ............ <b>ok</b>"], [0.9, "test    network ......... <b>ok</b>"], [1.7, "test    capture ......... <b>ok</b>"]],
      pass: [[0, "<b>run %n passed</b>"]],
    };
    let run = 412, lastCycle = -1, shown = new Set(), lines = con.innerHTML.split("\n").filter(Boolean);
    let seed = 1;
    const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;

    const frame = t => {
      const cycle = Math.floor(t / total);
      if (cycle !== lastCycle) { lastCycle = cycle; shown = new Set(); run++; }
      let local = t % total, stage = stages[0][0], into = 0, dur = 1;
      for (const [s, d] of stages) { if (local < d) { stage = s; into = local; dur = d; break; } local -= d; }

      for (const [i, [when, line]] of script[stage].entries()) {
        const key = stage + i;
        if (into >= when && !shown.has(key)) {
          shown.add(key);
          lines.push(line.replace("%n", String(run).padStart(4, "0")));
          if (lines.length > 13) lines = lines.slice(-13);
          con.innerHTML = lines.join("\n");
        }
      }
      pills.forEach(p => p.classList.toggle("on", p.dataset.stage === stage));

      const base = tpl.map(l => l.padEnd(C).split("")), hot = grid(R, C);
      const light = ([r, c], ch) => { hot[r][c] = ch || at(r, c); base[r][c] = " "; };
      const on = stage !== "power" || into > 0.7;
      if (on) light(pwr);
      if (stage === "power") {
        const head = Math.floor(into / 0.7 * mains.length);
        mains.forEach((p, i) => { if (i <= head && i > head - 4) light(p); });
      }
      if (stage === "flash" || stage === "boot" || stage === "test") {
        const busy = stage === "flash" ? 0.25 : 0.45;
        soc.forEach(p => { if (rnd() < busy) light(p, rnd() < 0.5 ? "▓" : "▒"); });
        if (Math.floor(t * 6) % 2) light(act);
      }
      if (stage === "boot" || stage === "test") {
        const off = Math.floor(t * 14);
        uart.forEach((p, i) => { if (((i - off) % 7 + 7) % 7 < 2) light(p, "━"); });
      }
      if (stage === "pass") { soc.forEach(p => light(p, "▓")); light(act); }

      // keep the padding on the base layer so its width (and the console next to it) never moves
      baseEl.textContent = base.map(r => r.join("")).join("\n");
      hotEl.textContent = text(hot);
      const pct = stage === "flash" ? Math.min(1, into / (dur - 0.3)) : stage === "power" ? 0 : 1;
      const n = Math.round(pct * 24);
      barEl.textContent = `${stage.padEnd(6)} [${"█".repeat(n)}${"░".repeat(24 - n)}] ${String(Math.round(pct * 100)).padStart(3)}%`;
    };
    loop(bench, 10, frame);
  }

  // 2b. pad: the pen stroke is svg animation, so pause it off-screen and leave it written out under reduced motion
  const ink = document.querySelector(".ink");
  if (ink) {
    let visible = false;
    const sync = () => {
      if (still.matches) { ink.pauseAnimations(); ink.setCurrentTime(4.6); }
      else if (visible && !document.hidden) ink.unpauseAnimations();
      else ink.pauseAnimations();
    };
    new IntersectionObserver(([e]) => { visible = e.isIntersecting; sync(); }).observe(ink);
    document.addEventListener("visibilitychange", sync);
    still.addEventListener("change", sync);
  }

  // 2c. listening. the html carries a baked last.fm snapshot and a first frame of each drawing;
  // on the server cron refreshes /lastfm.json, which is swapped in here.
  // deck: an ascii turntable that spins up and drops the arm while something is playing.
  // genres: a six-axis ascii radar with a sweep. top artists: ascii bars that draw in.
  const fm = document.querySelector("[data-fm]");
  if (fm) {
    const $ = s => fm.querySelector(`[data-fm-${s}]`);
    const RAMP = " .,:;-=+*#%";
    const blank = (R, C) => Array.from({ length: R }, () => new Array(C).fill(" "));
    const join = g => g.map(r => r.join("").replace(/\s+$/, "")).join("\n");
    // box-drawing stroke for a segment; a row is twice as tall as a column is wide
    const stroke = (dx, dy) => {
      const a = (Math.atan2(dy * 2, dx) * 180 / Math.PI + 180) % 180;
      return a < 22.5 || a >= 157.5 ? "─" : a < 67.5 ? "╲" : a < 112.5 ? "│" : "╱";
    };
    // a set of stacked character layers where each cell belongs to at most one layer
    const layers = (R, C, n, base = []) => {
      const L = Array.from({ length: n }, (_, i) => base[i] ? base[i].map(r => r.slice()) : blank(R, C));
      L.put = (i, y, x, ch) => {
        if (y < 0 || y >= R || x < 0 || x >= C) return;
        for (const g of L) g[y][x] = " ";
        L[i][y][x] = ch;
      };
      return L;
    };
    let playing = false, genres = [], top = [];

    // deck
    const [vDim, vHi, vAcc] = fm.querySelectorAll(".vinyl pre");
    const VC = 80, VR = 34, D = 68, PIV = [76, 2], REST = Math.PI / 2, PLAY = 2.17, ARM = 27.85;
    const label = [], vBase = [blank(VR, VC), blank(VR, VC)];
    for (let y = 0; y < VR; y++) for (let x = 0; x < D; x++) {
      const u = (x + 0.5 - D / 2) / (D / 2), v = (y + 0.5 - VR / 2) / (VR / 2), r = Math.hypot(u, v), th = Math.atan2(v, u);
      if (r > 1 || (r >= 0.27 && r < 0.3)) continue;
      if (r < 0.27) { label.push([y, x, r, th]); continue; }
      if ([0.5, 0.66, 0.82].some(g => Math.abs(r - g) < 0.018)) continue; // gaps between songs
      if (r > 0.965) { vBase[1][y][x] = ":"; continue; }
      // the light streak stays put while the record turns
      const s = Math.abs(Math.cos(th + 0.6)) ** 24 * (0.4 + 0.6 * r);
      const dot = Math.floor(r * 40) % 2 ? ":" : ".";
      if (s > 0.2) vBase[1][y][x] = dot;
      else vBase[0][y][x] = dot;
    }
    // tonearm: hairline svg over the ascii, in svg units (column, row * 2), pivot top right
    const [cw, armLine, head] = fm.querySelectorAll(".v-arm line");
    const setArm = a => {
      const c = Math.cos(a), s = Math.sin(a), px = PIV[0] + 0.5, py = (PIV[1] + 0.5) * 2;
      const at = (el, d0, d1) => { el.setAttribute("x1", (px + c * d0).toFixed(2)); el.setAttribute("y1", (py + s * d0).toFixed(2)); el.setAttribute("x2", (px + c * d1).toFixed(2)); el.setAttribute("y2", (py + s * d1).toFixed(2)); };
      at(cw, -6.5, -3); at(armLine, 0, ARM - 2.5); at(head, ARM - 3, ARM);
    };
    let spin = 0, speed = 0, arm = 0, lastT = 0;
    const deck = t => {
      const dt = Math.min(0.25, Math.max(0, t - lastT)); lastT = t;
      speed += ((playing ? 3.49 : 0) - speed) * Math.min(1, dt * 1.5); // 33 rpm
      spin += speed * dt;
      arm += ((playing ? 1 : 0) - arm) * Math.min(1, dt * 2.5);
      const L = layers(VR, VC, 3, vBase);
      for (const [y, x, r, th] of label) {
        const d = Math.abs(((th - spin) % (2 * Math.PI) + 3 * Math.PI) % (2 * Math.PI) - Math.PI);
        if (r < 0.04) L.put(1, y, x, "·");
        else L.put(2, y, x, d < 0.14 ? "█" : r > 0.225 ? "▓" : r > 0.2 ? " " : "░");
      }
      for (const [rr, off] of [[0.62, 0], [0.86, 2.2], [0.74, 4.1]]) {
        const a = spin + off;
        L.put(1, Math.round(VR / 2 - 0.5 + Math.sin(a) * rr * VR / 2), Math.round(D / 2 - 0.5 + Math.cos(a) * rr * D / 2), "*");
      }
      setArm(REST + (PLAY - REST) * arm);
      vDim.textContent = join(L[0]); vHi.textContent = join(L[1]); vAcc.textContent = join(L[2]);
    };

    // genres: crisp hairline geometry in svg, the ascii is the dot field, the fill and the sweep
    const [rDim, rFill, rSw, rLbl, rHot] = fm.querySelectorAll(".radar pre"), dias = fm.querySelectorAll(".radar .dia");
    const poly = fm.querySelector(".radar .poly");
    const RC = 64, RR = 23, CX = 32, CY = 11, RY = 9, RX = 18, TAU = 2 * Math.PI;
    const axis = k => { const a = (-90 + 60 * k) * Math.PI / 180; return [Math.cos(a), Math.sin(a)]; };
    const inside = (x, y, P) => {
      let c = false;
      for (let i = 0, j = P.length - 1; i < P.length; j = i++)
        if ((P[i][1] > y) !== (P[j][1] > y) && x < (P[j][0] - P[i][0]) * (y - P[i][1]) / (P[j][1] - P[i][1]) + P[i][0]) c = !c;
      return c;
    };
    const OUT = [0, 1, 2, 3, 4, 5].map(k => [CX + axis(k)[0] * RX, CY + axis(k)[1] * RY]);
    const cells = [], rGrid = blank(RR, RC);
    for (let y = 0; y < RR; y++) for (let x = 0; x < RC; x++) if (inside(x, y, OUT)) {
      const u = (x - CX) / RX, v = (y - CY) / RY;
      cells.push([y, x, Math.hypot(u, v), Math.atan2(v, u)]);
      if (x % 2 === 0) rGrid[y][x] = "·";
    }
    rGrid[CY][CX] = "+";
    const radar = t => {
      if (genres.length !== 6) return;
      const grow = 1 - (1 - Math.min(1, t / 1.4)) ** 3, sw = (t * 0.9) % TAU;
      const L = layers(RR, RC, 5, [rGrid]);
      const P = genres.map((g, k) => {
        const [ax, ay] = axis(k), v = Math.max(0.12, g.v) * grow * (0.96 + 0.04 * Math.sin(t * 1.6 + k * 1.3));
        return [CX + ax * RX * v, CY + ay * RY * v];
      });
      for (const [y, x, rho, th] of cells) {
        const lag = ((sw - th) % TAU + TAU) % TAU, k = lag < 1.1 ? 1 - lag / 1.1 : 0;
        if (inside(x, y, P)) L.put(k > 0.45 ? 4 : 1, y, x, "··:::+"[Math.min(5, Math.floor(rho * 6))]);
        else if (k > 0.3) L.put(2, y, x, k > 0.7 ? ":" : ".");
      }
      genres.forEach((g, k) => {
        const [ax, ay] = axis(k), d = Math.abs(((Math.atan2(ay, ax) - sw) % TAU + 1.5 * TAU) % TAU - Math.PI);
        const on = d < 0.45, name = g.g.slice(0, 12), vx = CX + ax * RX, vy = Math.round(CY + ay * RY);
        const y = k === 0 ? vy - 2 : k === 3 ? vy + 2 : vy;
        const x0 = k === 0 || k === 3 ? Math.round(CX - name.length / 2) : ax > 0 ? Math.round(vx) + 3 : Math.round(vx) - 2 - name.length;
        [...name].forEach((c, i) => L.put(on ? 4 : 3, y, x0 + i, c));
        dias[k].style.setProperty("--c", P[k][0].toFixed(2));
        dias[k].style.setProperty("--r", P[k][1].toFixed(2));
        dias[k].classList.toggle("on", on);
      });
      poly.setAttribute("points", P.map(([x, y]) => `${(x + 0.5).toFixed(2)},${((y + 0.5) * 2).toFixed(2)}`).join(" "));
      [rDim, rFill, rSw, rLbl, rHot].forEach((e, i) => { e.textContent = join(L[i]); });
    };

    // top artists
    const barsEl = $("top");
    let barsFrom = null, barsDone = false;
    const bars = g => {
      const most = Math.max(1, ...top.map(a => a.n));
      barsEl.replaceChildren(...top.flatMap(a => {
        const f = Math.round(a.n / most * 30 * g), name = a.a.length > 14 ? a.a.slice(0, 13) + "…" : a.a;
        const parts = [[name.padEnd(16), "span"], ["━".repeat(f), "b"], ["─".repeat(30 - f), "i"], [String(a.n).padStart(5) + "\n", "em"]];
        return parts.map(([s, tag]) => { const e = document.createElement(tag); e.textContent = s; return e; });
      }));
    };

    // data
    const day = u => new Date(u * 1000).toLocaleDateString("en-GB", { day: "numeric", month: "short" }).toLowerCase();
    const ago = u => {
      if (!u) return "now";
      const s = Date.now() / 1000 - u, n = (v, w) => `${v} ${w}${v === 1 ? "" : "s"} ago`;
      return s < 90 ? "just now" : s < 3600 ? `${Math.round(s / 60)} min ago`
        : s < 86400 ? `${Math.round(s / 3600)} h ago` : s < 604800 ? n(Math.round(s / 86400), "day") : day(u);
    };
    const el = (tag, txt) => { const e = document.createElement(tag); e.textContent = txt; return e; };
    const read = () => JSON.parse(fm.querySelector("script[type='application/json']").textContent);
    const render = d => {
      const [last, ...rest] = d.recent;
      playing = d.now;
      const state = $("state");
      state.textContent = d.now ? "now playing" : "last played";
      state.classList.toggle("live", d.now);
      $("when").textContent = d.now ? "" : ago(last.u);
      $("track").textContent = last.t;
      $("artist").textContent = last.a;
      $("recent").replaceChildren(...rest.slice(0, 4).map(r => {
        const li = el("li", "");
        li.append(el("time", ago(r.u)), el("span", r.t), el("span", r.a));
        return li;
      }));
      if (d.genres && d.genres.length === 6) { genres = d.genres; $("genres").textContent = genres.map(g => g.g).join(", "); }
      top = d.top; barsFrom = null; barsDone = false;
      $("scrobbles").textContent = d.scrobbles.toLocaleString("en-US");
      $("artists").textContent = d.artists.toLocaleString("en-US");
      $("since").textContent = new Date(d.since * 1000).getUTCFullYear();
      if (still.matches) { arm = playing ? 1 : 0; deck(lastT); radar(99); bars(1); }
    };
    render(read());
    const refresh = () => fetch("/lastfm.json", { cache: "no-cache" })
      .then(r => r.ok ? r.json() : null).then(d => d && d.recent && d.recent.length && render(d)).catch(() => {});
    refresh();
    setInterval(() => { if (!document.hidden) refresh(); }, 120000);

    loop(fm.querySelector(".vinyl"), 12, deck);
    loop(fm.querySelector(".radar"), 12, radar);
    loop(barsEl, 30, t => {
      if (barsDone) return;
      if (barsFrom === null) barsFrom = t;
      const g = Math.min(1, (t - barsFrom) / 1.1);
      bars(1 - (1 - g) ** 3);
      barsDone = g >= 1;
    });
  }

  // 3. pointer light on cards
  if (matchMedia("(hover: hover)").matches) {
    for (const card of document.querySelectorAll(".lit")) {
      card.addEventListener("pointermove", e => {
        const r = card.getBoundingClientRect();
        card.style.setProperty("--mx", `${e.clientX - r.left}px`);
        card.style.setProperty("--my", `${e.clientY - r.top}px`);
      });
    }
  }
})();
