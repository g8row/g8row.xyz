# g8row.xyz

personal site. static html, one css file, one small script, self-hosted fonts. no framework, no node.

```
site/                   what gets deployed
  index.html            generated from tools/index.tpl.html, don't edit by hand
  favicon.svg
  assets/site.css       tokens at the top, then layout and components
  assets/site.js        hero ascii field, bench animation, card pointer light (optional, ~3 KB gz)
  assets/fonts/         geist + geist mono, latin subsets (woff2)
tools/
  index.tpl.html        the page source: edit this
  build.py              fills in m3 shape paths, the baked hero frame, the tablet pen + frame-time svg, the bench board and the ascii background shapes
deploy/
  g8row.xyz.conf        nginx vhost for the homelab (certbot adds tls)
  deploy.sh             rsync site/ to the server
```

## edit, build, preview

```sh
python3 tools/build.py
python3 -m http.server 8765 --directory site
```

## deploy

one-time setup is in the header of `deploy/deploy.sh`. after that:

```sh
./deploy/deploy.sh
```

## design

- structure (cloudflare): 1px rules, dashed rails, square marks where lines meet, dotted ground.
- objects (material 3 expressive, from centuryplay): rounded containers, pills, shape icons, the wavy progress bar.
- background: ascii-shaded m3 shapes inside faint construction lines behind each section heading.
- light (vercel): glow behind the hero, inset highlights, a soft light that follows the pointer on cards.
- layout (nothing): full-screen hero with the name as the biggest thing on the page; full-width rows that alternate left and right.
- colour: greys plus one accent, centuryplay blue `#a8c7fa`.

## budget

| | target | now |
|---|---|---|
| html + css + js | < 30 KB gzip | ~18 KB |
| fonts | 2 families | 58 KB (3 files) |
| javascript required | 0 | 0 (hero and bench render a static frame without it) |
| animations | transform / opacity / text only | yes; paused off-screen, still under reduced motion |
