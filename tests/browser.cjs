// Run with Playwright installed: node tests/browser.cjs (Chrome path via CHROME).
const {chromium}=require('playwright');
const {spawn}=require('node:child_process');const path=require('node:path');
const assert=require('node:assert/strict');
(async()=>{
 const fixture=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'browser_fixture.py')],{cwd:path.join(__dirname,'..')});
 fixture.stderr.on('data',d=>process.stderr.write(d));
 const config=await new Promise((resolve,reject)=>{let output='';fixture.stdout.on('data',d=>{output+=d;if(output.includes('\n')){try{resolve(JSON.parse(output.split('\n')[0]));}catch(e){reject(e);}}});fixture.on('error',reject);fixture.on('exit',code=>reject(Error('fixture exited '+code)));});
 let browser;
 try{
  browser=await chromium.launch({headless:true,...(process.env.CHROME?{executablePath:process.env.CHROME}:{})});
  const page=await browser.newPage({viewport:{width:390,height:844}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const values={no:{title:'Varmepumpe',flow:'Tur',log:'Kompressorlogg',heater:'Elektriske varmeelementer',settings:'Oppsett av varmepumpesiden'},de:{title:'Wärmepumpe',flow:'Vorlauf',log:'Verdichterprotokoll',heater:'Elektrische Heizstäbe',settings:'Wärmepumpe einrichten'},en:{title:'heat pump',flow:'Flow',log:'Compressor log',heater:'Electric heaters',settings:'Heat pump setup'}};
  for(const lang of ['no','de','en','de','no']){
   await page.goto(config.base+'/');await page.selectOption('#language',lang);
   assert.deepEqual(await page.locator('#language option').evaluateAll(a=>a.map(x=>x.value)),['no','de','en']);
   await page.waitForFunction(()=>document.getElementById('tur').textContent.includes('32'));
   assert((await page.locator('body').innerText()).includes(values[lang].title));
   await page.evaluate(()=>update());assert((await page.locator('body').innerText()).includes(values[lang].flow));
   assert(!(await page.locator('body').innerText()).match(/[\u0e00-\u0e7f]/));
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'mobile overflow: '+lang);
   await page.goto(config.base+'/logg.html');await page.waitForSelector('#subpage-language');
   assert((await page.locator('body').innerText()).includes(values[lang].log));
   assert((await page.locator('body').innerText()).includes(values[lang].heater));
   await page.goto(config.base+'/kurver.html');await page.waitForSelector('#subpage-language');
   const button=page.locator('[data-action="in"]');await button.click();await page.locator('[data-action="prev"]').click();await page.locator('[data-action="now"]').click();
   await page.goto(config.base+'/feil.html');await page.waitForSelector('#subpage-language');assert.deepEqual(await page.locator('#subpage-language option').evaluateAll(a=>a.map(x=>x.value)),['no','de','en']);
   console.log('PASS mobile '+lang+': main, refresh, log, heaters, graph navigation');
  }
  await page.goto(config.base+'/setup/');
  for(const lang of ['no','de','en']){await page.selectOption('#language',lang);assert((await page.locator('h1').innerText()).includes(values[lang].settings));}
  await page.fill('#setup-key',config.key);await page.click('#connect');await page.waitForSelector('#settings:visible');
  assert.equal(await page.locator('input[name=bsb_host]').inputValue(),'127.0.0.1');
  assert.deepEqual(await page.locator('#language option').evaluateAll(a=>a.map(x=>x.value)),['no','de','en']);
  assert.deepEqual(errors,[]);console.log('PASS setup languages, unlock, options, no JavaScript errors');
  // Check the actual repeating timer, with virtual time rather than a 30-second wait.
  await page.clock.install();
  await page.goto(config.base+'/');await page.waitForFunction(()=>document.getElementById('tur').textContent.includes('32'));
  let requests=0;page.on('request',r=>{if(r.url().includes('heatpump-latest'))requests++;});
  await page.clock.fastForward(31000);await page.waitForTimeout(200);
  assert(requests>0,'automatic refresh did not run');console.log('PASS automatic 30-second refresh');
 }finally{if(browser)await browser.close();fixture.kill('SIGTERM');}
})().catch(e=>{console.error(e);process.exitCode=1;});
