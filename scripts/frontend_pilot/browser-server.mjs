import {createServer} from 'vite';
import react from '@vitejs/plugin-react';
import {createRequire} from 'node:module';
import {pathToFileURL, fileURLToPath} from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

export async function start() {
  const root=path.dirname(fileURLToPath(import.meta.url));
  const snapshot=process.env.PILOT_SNAPSHOT;
  const number=Number(process.env.PILOT_TASK);
  const app=number===1?path.join(snapshot,'apps/desktop'):snapshot;
  const src=path.join(app,'src');
  const fromSource=createRequire(path.join(app,'package.json'));
  const tailwind=(await import(pathToFileURL(fromSource.resolve('@tailwindcss/vite')))).default;
  const css=path.join(root,`fixture-${number}.css`);
  const posix=p=>p.replaceAll('\\','/');
  fs.writeFileSync(css,`@import "${posix(path.join(src,number===1?'index.css':'styles/globals.css'))}";\n@source "${posix(src)}";\n@source "${posix(path.join(root,'fixtures'))}";\n`);
  const aliases=[
    {find:'fixture-component',replacement:path.join(root,`fixtures/${number}.tsx`)},
    {find:'fixture-css',replacement:css},
    {find:'@/lib/platform',replacement:path.join(root,'fixtures/platform.ts')},
    {find:'@/modules/settings/openSettingsWindow',replacement:path.join(root,'fixtures/settings.ts')},
    {find:'../lib/composer',replacement:path.join(root,'fixtures/composer.ts')},
    {find:'@/modules/ai/lib/transport',replacement:path.join(root,'fixtures/transport.ts')},
    {find:'@',replacement:src},
    ...['react','react/jsx-runtime','react/jsx-dev-runtime','react-dom','react-dom/client'].map(name=>({find:new RegExp('^'+name+'$'),replacement:fromSource.resolve(name)})),
  ];
  const server=await createServer({root,configFile:false,plugins:[react(),tailwind()],resolve:{alias:aliases},
    server:{host:'127.0.0.1',port:0,fs:{allow:[root,snapshot]},hmr:false},
    cacheDir:path.join(process.env.PILOT_RUN,'vite-cache'),
    optimizeDeps:{entries:['index.html'],include:['react','react-dom/client','react/jsx-runtime','react/jsx-dev-runtime']},logLevel:'warn'});
  await server.listen();
  return {server,url:`http://127.0.0.1:${server.httpServer.address().port}`};
}
