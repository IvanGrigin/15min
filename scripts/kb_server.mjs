#!/usr/bin/env node
/**
 * Локальный сервер базы знаний (TriliumNext Trilium) БЕЗ docker:
 * production-сборка из checkout github.com/TriliumNext/trilium, запущенная node.
 *
 * Контракт: Docs/KNOWLEDGE_BASE.md. Инстанс проекта 15min слушает только
 * 127.0.0.1:8481 (noAuthentication допустим только для loopback).
 *
 * Раскладка (checkout ищется по кандидатам, данные — отдельный каталог):
 *   TRILIUM_CHECKOUT | <repo>/../tools/trilium | <repo>/../igrigin/tools/trilium
 *   TRILIUM_DATA_DIR | <каталог рядом с checkout>/trilium-data-15min
 *
 * При первом запуске сам создаёт каталог данных с config.ini и инициализирует
 * свежую БД через POST /api/setup/new-document.
 */
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const PORT = process.env.TRILIUM_PORT ?? '8481';
const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const candidates = [
  process.env.TRILIUM_CHECKOUT,
  path.resolve(repoRoot, '..', 'tools', 'trilium'),
  path.resolve(repoRoot, '..', 'igrigin', 'tools', 'trilium'),
].filter(Boolean);
const checkout = candidates.find((dir) => existsSync(path.join(dir, 'apps', 'server', 'dist', 'main.cjs')));

if (!checkout) {
  process.stderr.write(
    `kb-server: не найден собранный Trilium (искал: ${candidates.join(', ')})\n` +
      'Разовая подготовка (см. Docs/KNOWLEDGE_BASE.md):\n' +
      '  git clone https://github.com/TriliumNext/trilium.git ../tools/trilium\n' +
      '  cd ../tools/trilium && pnpm install --frozen-lockfile && pnpm run --filter server build\n',
  );
  process.exit(1);
}

const dataDir = process.env.TRILIUM_DATA_DIR ?? path.resolve(checkout, '..', 'trilium-data-15min');
const freshDatabase = !existsSync(path.join(dataDir, 'document.db'));

if (!existsSync(path.join(dataDir, 'config.ini'))) {
  mkdirSync(dataDir, { recursive: true });
  writeFileSync(
    path.join(dataDir, 'config.ini'),
    `[General]\ninstanceName=15min-kb\nnoAuthentication=true\n\n[Network]\nhost=127.0.0.1\nport=${PORT}\n`,
  );
}

const entry = path.join(checkout, 'apps', 'server', 'dist', 'main.cjs');
const child = spawn(process.execPath, [entry], {
  env: { ...process.env, TRILIUM_DATA_DIR: dataDir, TRILIUM_ENV: 'production', TRILIUM_PORT: PORT },
  stdio: 'inherit',
});
child.on('exit', (code) => process.exit(code ?? 0));

if (freshDatabase) {
  // Свежая БД: дождаться сервера и инициализировать документ.
  const base = `http://127.0.0.1:${PORT}`;
  (async () => {
    for (let attempt = 0; attempt < 30; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      const ok = await fetch(`${base}/api/health-check`).then((r) => r.ok).catch(() => false);
      if (!ok) continue;
      const setup = await fetch(`${base}/api/setup/new-document`, { method: 'POST' }).catch(() => null);
      if (setup?.ok) process.stderr.write('kb-server: новая БД инициализирована\n');
      return;
    }
    process.stderr.write('kb-server: сервер не ответил, инициализируйте БД вручную (POST /api/setup/new-document)\n');
  })();
}
