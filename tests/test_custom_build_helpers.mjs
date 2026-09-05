import test from 'node:test';
import assert from 'node:assert/strict';
import {resolve} from 'node:path';
import {render,validate} from '../skills/engineering/openclaw-custom-build-validation/scripts/report.mjs';
import {check,compare} from '../skills/engineering/openclaw-custom-build-validation/scripts/check-update.mjs';
const fixtureSkill = resolve('/fixture','skills/engineering/openclaw-custom-build-validation');
const sample = () => ({schema:'openclaw.custom-build-report/v1',runId:'12345678-1234-1234-1234-123456789abc',baseSha:'a'.repeat(40),candidateSha:'b'.repeat(40),candidateTree:'c'.repeat(40),patches:[],result:'passed',cleanup:'complete',tests:[{surface:'CLI startup',result:'passed',proof:'runtime'}],artifacts:[{component:'CLI',sha256:'d'.repeat(64),platform:'Windows'}],summary:'Observed startup passed.'});
test('renders and roundtrips the exact report identity',()=>{
 const r=sample(), body=render(r); assert.deepEqual(JSON.parse(body.split('<!-- openclaw-custom-build-report:v1\n')[1].split('\n-->')[0]),r);
});
test('rejects false pass, unknown keys and wrong identity',()=>{
 for(const mutate of [r=>r.tests=[],r=>r.tests[0].result='blocked',r=>r.token='secret',r=>r.candidateSha='main',r=>r.tests[0].proof='guessed']) { const r=sample(); mutate(r); assert.throws(()=>validate(r)); }
});
test('escapes envelope terminators and unicode roundtrip',()=>{
 const r=sample();r.summary='--> <script> & Olá';const body=render(r);assert.equal(body.split('-->').length,2);assert.ok(body.includes('\\u003e'));assert.ok(body.includes('Olá'));
});
test('UTF8 limit is enforced',()=>{const r=sample();r.tests=Array.from({length:30},()=>({surface:'á'.repeat(2000),result:'passed',proof:'automated'}));assert.throws(()=>render(r),/byte limit/);});
test('candidate and cleanup remain separate',()=>{const r=sample();r.cleanup='failed';assert.equal(validate(r).result,'passed');});
test('update comparison respects local edits and tree identity',()=>{
 assert.equal(compare({dirty:true,localTree:'a',remoteTree:'a'}),'local-modifications');
 assert.equal(compare({dirty:false,localTree:'a',remoteTree:'a'}),'current');
 assert.equal(compare({dirty:false,localTree:'a',remoteTree:'b'}),'source-differs');
 assert.equal(compare({dirty:false,localTree:'a'}),'untracked');
});
test('update checker never accesses remote for dirty checkout',()=>{
 const run=(bin,args)=>{assert.equal(bin,'git');const op=args[2];if(op==='remote')return 'origin https://github.com/TheAngryPit/TheAngrySkills.git (fetch)';if(op==='status')return '?? skill';if(args.includes('--show-toplevel'))return '/fixture';return 'a'.repeat(40);};
 assert.equal(check(run,fixtureSkill).status,'local-modifications');
});
test('unknown source and failures fail closed without leaking errors',()=>{
 assert.equal(check(()=>{throw new Error('secret');},'/fixture').status,'check-failed');
 assert.equal(check(()=>'/other','/fixture').status,'different-source');
});
test('clean source resolves canonical revision once and compares directory tree',()=>{
 const calls=[];
 const run=(bin,args)=>{
  calls.push([bin,args]);
  if(bin==='git') {
   if(args[2]==='remote')return 'origin git@github.com:TheAngryPit/TheAngrySkills.git (fetch)';
   if(args[2]==='status')return '';
   if(args.includes('--show-toplevel'))return '/fixture';
   return args.at(-1).startsWith('HEAD:')?'d'.repeat(40):'a'.repeat(40);
  }
  const endpoint=args[1];
  if(endpoint.endsWith('/TheAngrySkills'))return JSON.stringify({full_name:'TheAngryPit/TheAngrySkills',default_branch:'main'});
  if(endpoint.includes('/commits/'))return JSON.stringify({sha:'b'.repeat(40)});
  assert.ok(endpoint.endsWith('?ref='+'b'.repeat(40)));
  return JSON.stringify([{path:'skills/engineering/openclaw-custom-build-validation',type:'dir',sha:'d'.repeat(40)}]);
 };
 const result=check(run,fixtureSkill);assert.equal(result.status,'current');assert.equal(result.canonicalCommit,'b'.repeat(40));
 assert.equal(calls.filter(([bin])=>bin==='gh').length,3);
 assert.ok(calls.every(([bin,args])=>bin!=='gh'||args[0]==='api'&&!args.includes('--method')));
});
test('a sibling copy cannot inherit canonical tree provenance or access the network',()=>{
 const run=(bin,args)=>{
  assert.equal(bin,'git');
  if(args.includes('--show-toplevel'))return '/fixture';
  if(args[2]==='remote')return 'origin https://github.com/TheAngryPit/TheAngrySkills.git (fetch)';
  assert.fail('Unsupported copy must stop before inspecting the canonical tree');
 };
 assert.equal(check(run,resolve('/fixture','other-copy')).status,'untracked');
});
test('gitless copies are untracked but access and executable failures remain unknown',()=>{
 const failure=(status,stderr)=>()=>{throw Object.assign(new Error('private detail'),{status,stderr});};
 assert.equal(check(failure(128,Buffer.from('fatal: not a git repository (or any of the parent directories): .git\n')),fixtureSkill).status,'untracked');
 for(const run of [failure(128,'fatal: detected dubious ownership in repository'),failure(128,'fatal: cannot change directory: Permission denied'),failure(null,''),failure(1,'fatal: not a git repository')]) {
  const result=check(run,fixtureSkill);assert.equal(result.status,'check-failed');assert.ok(!JSON.stringify(result).includes('private detail'));
 }
});
test('failed and not-evaluated reports cannot conceal observations',()=>{
 const failed=sample();failed.tests[0].result='failed';assert.throws(()=>validate(failed));
 failed.result='failed';assert.equal(validate(failed).result,'failed');
 const empty=sample();empty.result='not-evaluated';assert.throws(()=>validate(empty));empty.tests=[];assert.equal(validate(empty).result,'not-evaluated');
});
