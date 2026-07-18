#!/usr/bin/env node
/**
 * CLI базы знаний проекта (TriliumNext Trilium, ETAPI).
 *
 * Иерархия адресуется человекочитаемым путём: "15min / 30 Регрессии".
 * Сегменты разделяются " / ", сопоставление по точному title.
 *
 * Использование (контракт: Docs/KNOWLEDGE_BASE.md):
 *   node scripts/kb.mjs info
 *   node scripts/kb.mjs ensure "15min / 20 Семейства шаблонов"
 *   node scripts/kb.mjs put    "15min / 20 Семейства шаблонов / Делимость" --stdin
 *   node scripts/kb.mjs get    "15min / 00 Обзор"
 *   node scripts/kb.mjs append "15min / 90 Журнал" "делимость: влита ветка, 140 тестов OK"
 *   node scripts/kb.mjs tree   ["15min"]
 *   node scripts/kb.mjs search "хрупк"
 *   node scripts/kb.mjs sync-out "15min" knowledge   # БЗ -> markdown-дерево (для git)
 *   node scripts/kb.mjs sync-in  "15min" knowledge   # markdown-дерево -> БЗ
 *
 * Окружение: TRILIUM_URL (по умолчанию http://127.0.0.1:8481),
 * TRILIUM_ETAPI_TOKEN (обязателен; создаётся в Options → ETAPI).
 * Токен не логируется и не должен попадать в git.
 */

const BASE_URL = (process.env.TRILIUM_URL ?? 'http://127.0.0.1:8481').replace(/\/$/, '');
// Локальный инстанс работает с noAuthentication=true (loopback-only), поэтому
// значение по умолчанию — заглушка; для docker/VPS задаётся настоящий токен.
const TOKEN = process.env.TRILIUM_ETAPI_TOKEN ?? 'local-noauth';

function fail(message) {
  process.stderr.write(`kb: ${message}\n`);
  process.exit(1);
}

async function etapi(path, { method = 'GET', body, contentType = 'application/json' } = {}) {
  const response = await fetch(`${BASE_URL}/etapi${path}`, {
    method,
    headers: {
      Authorization: TOKEN,
      ...(body === undefined ? {} : { 'Content-Type': contentType }),
    },
    body: body === undefined ? undefined : contentType === 'application/json' ? JSON.stringify(body) : body,
  });
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    fail(`${method} ${path} -> ${response.status} ${text.slice(0, 300)}`);
  }
  const raw = await response.text();
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

function splitPath(path) {
  const segments = String(path ?? '').split('/').map((segment) => segment.trim()).filter(Boolean);
  if (segments.length === 0) fail('пустой путь; ожидается "Раздел / Подраздел"');
  return segments;
}

async function childByTitle(parentId, title) {
  const parent = await etapi(`/notes/${encodeURIComponent(parentId)}`);
  for (const childId of parent.childNoteIds ?? []) {
    const child = await etapi(`/notes/${encodeURIComponent(childId)}`);
    if (child.title === title) return child;
  }
  return null;
}

async function createNote(parentNoteId, title, content = '') {
  const created = await etapi('/create-note', {
    method: 'POST',
    body: { parentNoteId, title, type: 'code', mime: 'text/markdown', content },
  });
  return created.note;
}

/** Находит заметку по пути; создаёт недостающие сегменты при create=true. */
async function resolvePath(path, { create = false } = {}) {
  let current = { noteId: 'root', title: 'root' };
  for (const segment of splitPath(path)) {
    let next = await childByTitle(current.noteId, segment);
    if (!next) {
      if (!create) fail(`не найдено: "${segment}" в "${current.title}"`);
      next = await createNote(current.noteId, segment);
    }
    current = next;
  }
  return current;
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString('utf8');
}

/** Название заметки <-> имя файла: запрещаем только разделители пути. */
function fileNameOf(title) {
  return title.replaceAll('/', '∕').trim();
}

/**
 * БЗ -> каталог markdown-файлов (зеркало для git):
 * заметка с детьми -> каталог "<title>/" (своё содержимое -> "<title>/_note.md"),
 * лист -> файл "<title>.md".
 */
async function syncOut(noteId, dir) {
  const { mkdir, writeFile } = await import('node:fs/promises');
  await mkdir(dir, { recursive: true });
  const note = await etapi(`/notes/${encodeURIComponent(noteId)}`);
  for (const childId of note.childNoteIds ?? []) {
    const child = await etapi(`/notes/${encodeURIComponent(childId)}`);
    const content = await etapi(`/notes/${encodeURIComponent(childId)}/content`);
    const text = typeof content === 'string' ? content : '';
    if ((child.childNoteIds ?? []).length > 0) {
      const childDir = `${dir}/${fileNameOf(child.title)}`;
      await mkdir(childDir, { recursive: true });
      if (text.trim()) await writeFile(`${childDir}/_note.md`, text);
      await syncOut(childId, childDir);
    } else {
      await writeFile(`${dir}/${fileNameOf(child.title)}.md`, text);
    }
  }
}

/** Каталог markdown-файлов -> БЗ (создаёт/обновляет, ничего не удаляет). */
async function syncIn(parentId, dir) {
  const { readdir, readFile } = await import('node:fs/promises');
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name, 'ru'))) {
    if (entry.name.startsWith('.') || entry.name === '_note.md') continue;
    if (entry.isDirectory()) {
      const title = entry.name;
      const note = (await childByTitle(parentId, title)) ?? (await createNote(parentId, title));
      const own = await readFile(`${dir}/${entry.name}/_note.md`, 'utf8').catch(() => null);
      if (own !== null) {
        await etapi(`/notes/${encodeURIComponent(note.noteId)}/content`, { method: 'PUT', body: own, contentType: 'text/plain' });
      }
      await syncIn(note.noteId, `${dir}/${entry.name}`);
    } else if (entry.name.endsWith('.md')) {
      const title = entry.name.slice(0, -3);
      const note = (await childByTitle(parentId, title)) ?? (await createNote(parentId, title));
      const content = await readFile(`${dir}/${entry.name}`, 'utf8');
      await etapi(`/notes/${encodeURIComponent(note.noteId)}/content`, { method: 'PUT', body: content, contentType: 'text/plain' });
    }
  }
}

const [, , command, ...rest] = process.argv;

if (!command || command === 'help' || command === '--help') {
  process.stdout.write(
    'kb: info | ensure <путь> | put <путь> (--stdin | --content "...") | get <путь> | append <путь> <строка> | tree [путь] | search <запрос> | sync-out <путь> <dir> | sync-in <путь> <dir>\n',
  );
  process.exit(0);
}
if (!TOKEN) fail('TRILIUM_ETAPI_TOKEN не задан (создайте токен: Options → ETAPI)');

switch (command) {
  case 'info': {
    const info = await etapi('/app-info');
    process.stdout.write(`Trilium ${info.appVersion} (db ${info.dbVersion}) @ ${BASE_URL}\n`);
    break;
  }
  case 'ensure': {
    const note = await resolvePath(rest[0], { create: true });
    process.stdout.write(`${note.noteId}\t${note.title}\n`);
    break;
  }
  case 'put': {
    const content = rest.includes('--stdin')
      ? await readStdin()
      : rest[rest.indexOf('--content') + 1];
    if (typeof content !== 'string') fail('нет содержимого: используйте --stdin или --content "..."');
    const note = await resolvePath(rest[0], { create: true });
    await etapi(`/notes/${encodeURIComponent(note.noteId)}/content`, {
      method: 'PUT',
      body: content,
      contentType: 'text/plain',
    });
    process.stdout.write(`записано: ${note.noteId} (${content.length} байт)\n`);
    break;
  }
  case 'get': {
    const note = await resolvePath(rest[0]);
    const content = await etapi(`/notes/${encodeURIComponent(note.noteId)}/content`);
    process.stdout.write(`${typeof content === 'string' ? content : JSON.stringify(content)}\n`);
    break;
  }
  case 'append': {
    if (!rest[1]) fail('append <путь> <строка>');
    const note = await resolvePath(rest[0], { create: true });
    const existing = await etapi(`/notes/${encodeURIComponent(note.noteId)}/content`);
    const date = new Date().toISOString().slice(0, 10);
    const body = `${typeof existing === 'string' ? existing.replace(/\n$/, '') : ''}\n- ${date}: ${rest[1]}\n`;
    await etapi(`/notes/${encodeURIComponent(note.noteId)}/content`, {
      method: 'PUT',
      body,
      contentType: 'text/plain',
    });
    process.stdout.write('добавлено\n');
    break;
  }
  case 'tree': {
    const note = rest[0] ? await resolvePath(rest[0]) : { noteId: 'root', title: 'root' };
    const parent = await etapi(`/notes/${encodeURIComponent(note.noteId)}`);
    for (const childId of parent.childNoteIds ?? []) {
      const child = await etapi(`/notes/${encodeURIComponent(childId)}`);
      process.stdout.write(`${child.noteId}\t${child.title}\n`);
    }
    break;
  }
  case 'search': {
    if (!rest[0]) fail('search <запрос>');
    const found = await etapi(`/notes?search=${encodeURIComponent(rest[0])}&limit=30`);
    for (const note of found.results ?? []) process.stdout.write(`${note.noteId}\t${note.title}\n`);
    break;
  }
  case 'sync-out': {
    if (!rest[1]) fail('sync-out <путь> <каталог>');
    const note = await resolvePath(rest[0], { create: true });
    await syncOut(note.noteId, rest[1]);
    process.stdout.write(`выгружено в ${rest[1]}\n`);
    break;
  }
  case 'sync-in': {
    if (!rest[1]) fail('sync-in <путь> <каталог>');
    const note = await resolvePath(rest[0], { create: true });
    await syncIn(note.noteId, rest[1]);
    process.stdout.write(`загружено из ${rest[1]}\n`);
    break;
  }
  default:
    fail(`неизвестная команда: ${command} (см. kb.mjs help)`);
}
