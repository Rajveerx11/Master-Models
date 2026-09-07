// Copy to OS TEMP, then execute with the playwright-skill run.js entry point.
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
(async () => {
  const harness=process.env.PILOT_HARNESS || 'C:/Master-Models/outputs/frontend-pilot/harness';
  const {chromium,expect}=require(path.join(harness,'node_modules/@playwright/test'));
  const {start}=await import(pathToFileURL(path.join(harness,'browser-server.mjs')));
  const number=Number(process.env.PILOT_TASK);
  const id=Date.now().toString();
  const out=path.join(process.env.PILOT_RUN,'browser',id);fs.mkdirSync(out,{recursive:true});
  const result={task:number,started_at:new Date().toISOString(),checks:[],errors:[],screenshots:[]};
  let server,browser;
  const check=(name,pass,observed)=>result.checks.push({name,pass,observed});
  try {
    const started=await start();server=started.server;
    browser=await chromium.launch({headless:true});result.browser=browser.version();
    const page=await browser.newPage({viewport:{width:1200,height:850},reducedMotion:'reduce'});
    page.on('pageerror',e=>result.errors.push({kind:'pageerror',message:e.message}));
    page.on('console',e=>{if(e.type()==='error')result.errors.push({kind:'console',message:e.text()})});
    page.on('requestfailed',r=>result.errors.push({kind:'requestfailed',url:r.url(),message:r.failure()?.errorText}));
    await page.goto(started.url,{waitUntil:'domcontentloaded',timeout:60000});
    const shot=async name=>{const file=path.join(out,name+'.png');await page.screenshot({path:file});result.screenshots.push(file)};
    if(number===1){
      const input=page.getByRole('textbox',{name:'Project name'});
      await expect(input).toBeVisible();
      const box=await input.boundingBox(),button=await page.getByRole('button',{name:'Reset'}).boundingBox();
      check('compact height and alignment',box.height===32&&Math.abs(box.y-button.y)<1,{input:box,button});
      await page.keyboard.press('Tab');await expect(input).toBeFocused();
      const focused=await input.evaluate(e=>{const s=getComputedStyle(e);const canvas=document.createElement('canvas');canvas.width=canvas.height=1;const c=canvas.getContext('2d');const rgba=color=>{c.clearRect(0,0,1,1);c.fillStyle=color;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data]};return {shadow:s.boxShadow,border:s.borderColor,ring:s.getPropertyValue('--tw-ring-color'),ringRgba:rgba(s.getPropertyValue('--tw-ring-color')),primaryRgba:rgba(getComputedStyle(document.querySelector('[data-testid=primary]')).backgroundColor)}});
      const primary=await page.getByTestId('primary').evaluate(e=>getComputedStyle(e).backgroundColor);
      check('visible primary focus',focused.shadow!=='none'&&focused.ringRgba[3]>=64&&focused.ringRgba.slice(0,3).every((v,i)=>Math.abs(v-focused.primaryRgba[i])<=2),{focused,primary});
      await input.fill('sample');check('controlled typing',await page.getByTestId('value').textContent()==='sample');
      await shot('focused');await page.keyboard.press('Tab');
      const blurred=await input.evaluate(e=>getComputedStyle(e).boxShadow);
      check('focus ring removed on blur',blurred!==focused.shadow,{blurred});
      await page.getByRole('button',{name:'Reset'}).click();check('external value update',await input.inputValue()==='reset');
      const disabled=page.getByRole('textbox',{name:'Disabled'});
      check('disabled value preserved',await disabled.isDisabled()&&(await disabled.inputValue())==='locked');await shot('blurred');
    }else if(number===20){
      for(const side of ['top','bottom','left','right'])for(const variant of ['default','custom']){
        const trigger=page.getByTestId(side+'-'+variant);await trigger.focus();
        const body=page.locator('[data-slot="tooltip-content"]');await expect(body).toBeVisible();
        await expect(body).toHaveAttribute('data-side',side);
        const colors=await body.evaluate(e=>{const svg=e.querySelector('svg');return {body:getComputedStyle(e).backgroundColor,arrowBackground:getComputedStyle(svg).backgroundColor,arrowFill:getComputedStyle(svg).fill,html:e.outerHTML}});
        check(side+' '+variant+' surface matches',colors.arrowBackground===colors.body&&(colors.arrowFill===colors.body||colors.arrowFill==='rgba(0, 0, 0, 0)'),colors);
        const described=await trigger.getAttribute('aria-describedby');
        check(side+' '+variant+' keyboard relationship',!!described&&(await page.locator('[id="'+described+'"]').textContent()).includes('Surface'));
        await shot(side+'-'+variant);await page.keyboard.press('Escape');await expect(body).toBeHidden();
      }
    }else if(number===10){
      await page.waitForFunction(()=>window.pilot?.local,{},{timeout:60000});
      const {local,cloud}=await page.evaluate(()=>({local:window.pilot.local,cloud:window.pilot.cloud}));
      const trigger=page.getByRole('button',{name:cloud.label,exact:true});await trigger.click();
      const localItem=page.getByRole('menuitem').filter({has:page.getByText(local.label,{exact:true})});
      const cloudItem=page.getByRole('menuitem').filter({has:page.getByText(cloud.label,{exact:true})});
      check('key-required cloud disabled',await cloudItem.getAttribute('aria-disabled')==='true');
      const enabled=await localItem.getAttribute('aria-disabled')!=='true';check('keyless local selectable',enabled);
      await shot('picker');
      if(enabled){await localItem.click();const state=await page.evaluate(()=>({selected:window.pilot.store.getState().selectedModelId,calls:window.pilot.settingsCalls}));check('selection without settings redirect',state.selected===local.id&&state.calls.length===0,state);
        check('local title has no missing-key warning',await page.getByRole('button',{name:local.label,exact:true}).getAttribute('title')===`Model: ${local.label}`);await shot('selected');}
    }else throw Error('Unsupported browser task');
  }catch(error){result.errors.push({kind:'harness-or-assertion',message:error.stack});}
  finally {if(browser)await browser.close();if(server)await server.close();}
  result.passed=result.errors.length===0&&result.checks.length>0&&result.checks.every(c=>c.pass);
  fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify({artifact:path.join(out,'result.json'),passed:result.passed,checks:result.checks.map(({name,pass,observed})=>({name,pass,...(!pass?{observed}: {})})),errors:result.errors}));
  if(!result.passed)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
