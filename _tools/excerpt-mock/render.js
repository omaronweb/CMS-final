// node render.js — screenshots each panel of mock.html into docs/img (2x)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 820, height: 800 }, deviceScaleFactor: 2 });
  await p.goto('file://' + path.join(__dirname, 'mock.html')); await p.waitForTimeout(500);
  for (const id of ['home', 'search', 'list'])
    await (await p.$('#' + id)).screenshot({ path: path.join(__dirname, '../../docs/img/excerpt-' + id + '.png') });
  await b.close();
})();
