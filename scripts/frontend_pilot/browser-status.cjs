// Independently check the browser artifact and fail closed on stale/missing evidence.
const fs=require('node:fs');
const path=require('node:path');
const root=path.join(process.env.PILOT_RUN,'browser');
const files=fs.readdirSync(root).filter(n=>/^\d+$/.test(n)).sort((a,b)=>Number(b)-Number(a));
if(!files.length)throw Error('No browser result');
const file=path.join(root,files[0],'result.json');
const report=JSON.parse(fs.readFileSync(file,'utf8'));
if(Date.now()-Number(files[0])>180000)throw Error('Stale browser result');
process.exitCode=report.passed===true?0:1;
