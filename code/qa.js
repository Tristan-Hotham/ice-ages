// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server <port>; set PORT).
// MapLibre comes from a local npm copy (the CDN is not reachable from the build container); fonts are blocked here.
// NOML=1 blocks MapLibre too, to check the page falls back to its own canvas map.
const { chromium } = require("playwright");
const ML = process.env.MAPLIBRE_DIST || "/tmp/ml/node_modules/maplibre-gl/dist";
const fs = require("fs");
(async () => {
  fs.mkdirSync("qa", { recursive: true });
  const b = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"] });
  const errs = [];
  const sizes = process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 860]] : [["desktop", 1280, 900], ["phone", 390, 844]];
  for (const [nm, vw, vh] of sizes) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/googleapis|gstatic/, r => r.abort());
    if (process.env.NOML) await p.route(/maplibre-gl/, r => r.abort());
    else {
      await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.js/, r => r.fulfill({ path: ML + "/maplibre-gl.js", contentType: "application/javascript" }));
      await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.css/, r => r.fulfill({ path: ML + "/maplibre-gl.css", contentType: "text/css" }));
    }
    if (process.env.NOTILES) await p.route(/img\/relief/, r => r.abort());
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to load resource|AJAXError/i.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8811) + "/index.html", { waitUntil: "load" });
    await p.waitForTimeout(3500);
    const tag = process.env.NOML ? "noml_" : process.env.NOTILES ? "notiles_" : "";
    await p.screenshot({ path: `qa/${tag}${nm}_top.png` });
    const idle = () => p.evaluate(() => new Promise(r => { if (!window.map || !map.loaded) return r(); let done = false; const fin = () => { if (!done) { done = true; r(); } }; map.once("idle", fin); map.triggerRepaint(); setTimeout(fin, 40000); }));
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(500); if (!process.env.NOML && /atlas|map/.test(sel)) await idle(); await p.locator(sel).screenshot({ path: `qa/${tag}${nm}_${f}.png` }); };
    await shot("#atlas", "map");
    const setSt = async k => { await p.evaluate(k => { const i = MK.indexOf(k); const r = document.getElementById("st"); r.value = i; r.dispatchEvent(new Event("input")); }, k); await p.waitForTimeout(700); };
    await setSt("mis6"); await p.click('#refRow [data-r="lgm"]'); await shot("#atlas", "map_mis6_lgm");
    await p.click('#refRow [data-r="lgm"]'); await p.click('#refRow [data-r="max"]'); await setSt("mis5a"); await shot("#atlas", "map_mis5a_max");
    await p.click('#refRow [data-r="max"]'); await p.click('#seaRow [data-s="60"]'); await setSt("lgm"); await shot("#atlas", "map_lgm_sea60");
    await p.click('#seaRow [data-s="120"]');
    await p.click("#play"); await p.waitForTimeout(2000); await p.click("#play");
    await setSt("lgm");
    // search and click
    await p.fill("#q", "Chicago"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2500); await shot("#atlas", "search_chicago");
    const sideTxt = await p.locator("#side").innerText(); console.log(nm, "side after Chicago:", sideTxt.replace(/\s+/g, " ").slice(0, 260));
    if (!process.env.NOML) {
      await p.evaluate(() => map.jumpTo({ center: [2, 54], zoom: 3.6 })); await p.waitForTimeout(800);
      const r = await p.evaluate(() => { const b = map.getContainer().getBoundingClientRect(), xy = map.project([2.5, 54.5]); return [b.left + xy.x, b.top + xy.y]; });
      await p.mouse.click(r[0], r[1]); await p.waitForTimeout(1200); await shot("#atlas", "click_northsea");
      console.log(nm, "side after North Sea click:", (await p.locator("#side").innerText()).replace(/\s+/g, " ").slice(0, 300));
      await p.click(".lyrBtn"); await p.waitForTimeout(300); await shot("#map", "layers_panel"); await p.click(".lyrBtn");
    } else {
      const bx = await p.locator("#map canvas.fb").boundingBox(); await p.mouse.click(bx.x + bx.width * .47, bx.y + bx.height * .25); await p.waitForTimeout(800); await shot("#atlas", "fallback_click");
    }
    for (const c of ["areaChart", "southChart", "countryChart", "cityTable", "shelfChart"]) await shot("#" + c, c);
    if (nm === "phone" && !process.env.NOML) {
      await p.click("#theme"); await p.waitForTimeout(1500); await p.evaluate(() => map.jumpTo(HOME())); await shot("#atlas", "dark_map"); await shot("#areaChart", "dark_area");
      await p.locator("#atlas").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500); await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
      await p.click(".mfs-btn"); await p.waitForTimeout(600);
    }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
