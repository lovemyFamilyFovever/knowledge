// 截图像素对比（ImageMagick compare 包装）：
//   node scripts/agent/imgdiff.mjs <a.png> <b.png> [fuzz%]
// 输出差异像素数与占比；fuzz 默认 2%（容忍动效/抗锯齿抖动）。
// 依赖：ImageMagick（magick 在 PATH）。仅用于 UI 回归自检，不进运行时。
import { spawnSync } from 'child_process';
import fs from 'fs';

const [, , a, b, fuzzArg] = process.argv;
if (!a || !b) { console.error('usage: node imgdiff.mjs <a.png> <b.png> [fuzz%]'); process.exit(2); }
for (const f of [a, b]) if (!fs.existsSync(f)) { console.error(`missing file: ${f}`); process.exit(2); }
const fuzz = fuzzArg || '2%';

function identify(f) {
  const r = spawnSync('magick', ['identify', '-format', '%w %h', f], { encoding: 'utf8' });
  if (r.status !== 0) { console.error(`identify failed for ${f}: ${r.stderr}`); process.exit(3); }
  const [w, h] = r.stdout.trim().split(/\s+/).map(Number);
  return { w, h, n: w * h };
}
const ia = identify(a), ib = identify(b);
if (ia.w !== ib.w || ia.h !== ib.h) {
  console.log(`SIZE-MISMATCH ${ia.w}x${ia.h} vs ${ib.w}x${ib.h} —— 请用相同视口重截（shot.mjs 传同样的 w h）`);
  process.exit(1);
}
const diffPath = b.replace(/\.png$/i, '') + '.diff.png';
const r = spawnSync('magick', ['compare', '-metric', 'AE', '-fuzz', fuzz, a, b, diffPath], { encoding: 'utf8' });
const ae = parseInt((r.stderr || '').trim(), 10);
if (Number.isNaN(ae)) { console.error(`compare failed: ${r.stderr || r.error}`); process.exit(3); }
const pct = (ae / ia.n * 100).toFixed(4);
console.log(`AE=${ae} (${pct}% of ${ia.n}px) fuzz=${fuzz}`);
console.log(pct < 0.01 ? `PASS：两图一致（<0.01%，diff 图 ${diffPath}）` : `DIFF：差异 ${pct}%，热图 ${diffPath}（红=变化区）`);
process.exit(r.status === 0 ? 0 : 1);
