// Автотесты ключевой логики приложения (без браузера):
//   node test/run-tests.js
// Загружает инлайн-скрипт index.html в песочницу vm и проверяет:
//   - нормализацию кодов (чистка управляющих символов, обрезка 31 символа)
//   - защиту от дублей
//   - экранирование esc() (XSS)
//   - CSV-экспорт (BOM, CRLF, разделитель ";")
//   - TXT-экспорт (BOM, CRLF)
//   - историю (одна запись на сессию)
//   - наличие файлов, перечисленных в precache sw.js
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.error('FAIL: inline script not found'); process.exit(1); }

function elementStub() {
  return {
    textContent: '', className: '', value: '', innerHTML: '', dataset: {},
    style: {},
    classList: { add() {}, remove() {}, toggle() {} },
    addEventListener() {}, appendChild() {}, removeChild() {}, select() {}, click() {},
  };
}

const store = {};
const nav = {
  serviceWorker: { register: () => Promise.resolve({ addEventListener() {}, update() {} }) },
  clipboard: {}, vibrate() {}, share() {}, canShare: () => false, standalone: false,
};
const context = {
  console,
  document: {
    getElementById: () => elementStub(),
    querySelectorAll: () => [],
    documentElement: { dataset: {}, classList: { add() {}, remove() {} } },
  },
  localStorage: {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: (k) => { delete store[k]; },
  },
  navigator: nav,
  window: { navigator: nav, addEventListener() {}, location: { reload() {} } },
  matchMedia: () => ({ matches: false }),
  confirm: () => true,
  setTimeout, clearTimeout, setInterval: () => 0, clearInterval,
  Blob: class { constructor() { this.parts = []; } },
  File: class { constructor() { this.parts = []; } },
  URL: { createObjectURL: () => 'blob:x', revokeObjectURL() {} },
  AudioContext: function () {},
};
vm.createContext(context);
vm.runInContext(m[1], context);

// codes объявлена через let — доступна только внутри песочницы
function run(expr) { return vm.runInContext(expr, context); }
const { addCode, esc, buildCsvContent, buildFileContent, saveSessionToHistory } = context;

let passed = 0;
function check(name, fn) {
  try { fn(); passed++; console.log('  ✓ ' + name); }
  catch (e) { console.error('  ✗ ' + name + '\n    ' + e.message); process.exitCode = 1; }
}

console.log('Тест: нормализация и дубли');
check('управляющие символы вычищаются, код обрезается до 31 символа', () => {
  run('codes.length = 0');
  assert.strictEqual(addCode('\u001C\u001D0104655008543958215XleDipIREINt', 'light'), true);
  assert.strictEqual(run('codes.length'), 1);
  assert.strictEqual(run('codes[0].text'), '0104655008543958215XleDipIREINt');
  assert.strictEqual(run('codes[0].text.length'), 31);
});
check('длинный код обрезается до 31 символа', () => {
  run('codes.length = 0');
  addCode('A'.repeat(45), 'build');
  assert.strictEqual(run('codes[0].text.length'), 31);
});
check('повторный код не добавляется (защита от дублей)', () => {
  run('codes.length = 0');
  addCode('ABC123', 'light');
  assert.strictEqual(addCode('ABC123', 'light'), false);
  assert.strictEqual(run('codes.length'), 1);
});
check('пустой код отклоняется', () => {
  run('codes.length = 0');
  assert.strictEqual(addCode('', 'light'), false);
  assert.strictEqual(run('codes.length'), 0);
});

console.log('Тест: esc() (XSS-экранирование)');
check('экранирует < > & " \'', () => {
  assert.strictEqual(esc('<script>'), '&lt;script&gt;');
  assert.strictEqual(esc('a&b'), 'a&amp;b');
  assert.strictEqual(esc('"q"'), '&quot;q&quot;');
  assert.strictEqual(esc("it's"), 'it&#x27;s');
});

console.log('Тест: CSV-экспорт');
check('BOM в начале, CRLF, разделитель ";", строка с кодами', () => {
  run('codes.length = 0');
  run('codes.push({ text: "ABC123", cat: "light" })');
  const csv = buildCsvContent();
  assert.strictEqual(csv.charCodeAt(0), 0xFEFF, 'нет BOM');
  assert.ok(csv.includes('\r\n'), 'нет CRLF');
  assert.ok(csv.includes('1;ABC123'), 'нет строки данных');
  assert.ok(!csv.includes('QR коды Честного знака\n'), 'CSV не должен быть TXT-форматом');
});

console.log('Тест: TXT-экспорт');
check('BOM и CRLF присутствуют', () => {
  const txt = buildFileContent();
  assert.strictEqual(txt.charCodeAt(0), 0xFEFF, 'нет BOM');
  assert.ok(txt.includes('\r\n'), 'нет CRLF');
});

console.log('Тест: история');
check('одна запись на сессию (upsert по sessionId)', () => {
  run('codes.length = 0');
  run('codes.push({ text: "ONE", cat: "light" })');
  saveSessionToHistory();
  run('codes.push({ text: "TWO", cat: "light" })');
  saveSessionToHistory();
  const h = JSON.parse(store['ssq-history']);
  assert.strictEqual(h.length, 1, 'должна быть 1 запись, а не ' + h.length);
  assert.strictEqual(h[0].count, 2);
});

console.log('Тест: precache-файлы sw.js существуют');
check('все URL из PRECACHE присутствуют в проекте', () => {
  const sw = fs.readFileSync(path.join(ROOT, 'sw.js'), 'utf8');
  const urls = [...sw.matchAll(/BASE \+ '([^']+)'/g)].map((x) => x[1]);
  assert.ok(urls.length >= 6, 'мало файлов в precache');
  for (const u of urls) {
    assert.ok(fs.existsSync(path.join(ROOT, u)), 'нет файла: ' + u);
  }
});

console.log('\n' + (process.exitCode ? 'ЕСТЬ ОШИБКИ' : 'ВСЕ ТЕСТЫ ПРОЙДЕНЫ (' + passed + ')'));
