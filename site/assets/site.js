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
