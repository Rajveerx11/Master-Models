import { defineConfig } from 'vitest/config';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
const snapshot = process.env.PILOT_SNAPSHOT;
if (!snapshot) throw new Error('PILOT_SNAPSHOT is required');
const source = path.join(snapshot, 'src');
const fromSource = createRequire(path.join(snapshot, 'package.json'));
export default defineConfig({
  root,
  resolve: { alias: [
    { find: '@', replacement: source },
    { find: /^@ai-sdk\/react$/, replacement: fromSource.resolve('@ai-sdk/react') },
    ...['react','react/jsx-runtime','react/jsx-dev-runtime','react-dom','react-dom/client','react-dom/test-utils'].map(name => ({find:new RegExp('^'+name+'$'),replacement:fromSource.resolve(name)})),
  ] },
  test: { environment: process.env.PILOT_TASK === '29' ? 'jsdom' : 'node', include: [`tests/${process.env.PILOT_TASK}.test.tsx`],
    passWithNoTests: false, maxWorkers: 1, minWorkers: 1, fileParallelism: false,
    server: { deps: { inline: [/react/, /@testing-library/] } },
  },
});
