import argparse
import copy
from datetime import datetime,timezone
import io
import json
from pathlib import Path
import platform
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from script_agent.domain import check, digest
from script_agent.engine import Agent
from script_agent.models import ChatModel, MockModel

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def source_digest():return digest({str(p.relative_to(ROOT)).replace('\\','/'):p.read_text(encoding='utf-8') for folder in ('src','tests','scripts') for p in sorted((ROOT/folder).rglob('*.py'))})
def cases():
    return [('normal',{'target_seconds':45},'completed',None,None,32),('duration_revision',{},'completed',None,None,32),('short_target',{'target_seconds':5},'completed',None,None,32),('missing',{'audience':None},'needs_info',None,None,32),('missing_duration',{'target_seconds':None},'needs_info',None,None,32),('no_materials',{'topic':'量子计算硬件'},'needs_materials',None,None,32),('rewrite',{'topic':'自动文字上屏'},'completed',None,None,32),('tool_retry',{},'completed','search_materials_once',None,32),('tool_failure',{},'tool_failed','estimate_duration_always',None,32),('impossible',{'target_seconds':1},'constraints_unmet',None,None,32),('replaced',{},'completed',None,'replace',32),('step_limit',{},'incomplete_step_limit',None,None,3)]

def evaluate(mode,destination,case_names=None):
    selected=cases()
    if case_names is not None:
        if not case_names or len(case_names)!=len(set(case_names)) or set(case_names)-{c[0] for c in selected}:raise ValueError('nonempty unique known case names required')
        selected=[c for c in selected if c[0] in case_names]
    dest=Path(destination)
    if dest.exists():raise ValueError('Choose a new evidence directory; never overwrite')
    dest.mkdir(parents=True);base=json.loads((ROOT/'data/materials.json').read_text(encoding='utf-8'));started=time.monotonic();records=[]
    for name,changes,expected,fault,variant,limit in selected:
        req={'request_id':name,'topic':'小影字幕','audience':'新手创作者','platform':'抖音','target_seconds':30,'style':'轻松',**changes};data=copy.deepcopy(base)
        if variant=='replace':data['materials'][0]['facts']=['支持添加贴纸。']
        model=MockModel() if mode=='mock' else ChatModel();r=Agent(model,data,max_steps=limit,fault=fault).run(req)
        folder=dest/name;write(folder/'input.json',req);write(folder/'dataset.json',data);write(folder/'result.json',r);write(ROOT/'examples/inputs'/f'{name}.json',req)
        checks={'expected_status':r['status']==expected,'bounded':r['model_calls']<=limit,'no_publication':r['published'] is False}
        if r['status']=='completed':
            script={'title':r['title'],'scenes':[{k:s[k] for k in ('visual','lines','hold_seconds')} for s in r['storyboard']]}
            checks.update(actual_checks_passed=r['duration_check']['passed'] and r['rule_check']['passed'],same_version=r['duration_check']['script_version']==r['rule_check']['script_version']==r['script_version'],exact_scene_sum=round(sum(s['estimated_seconds'] for s in r['storyboard']),1)==r['estimated_total_seconds'],within_duration=r['estimated_total_seconds']<=req['target_seconds'],grounded_facts=check(script,r['retrieved_materials'],data['brand_rules'])['passed'],material_sources_present=bool(r['source_material_ids']))
        if mode=='mock' and name=='duration_revision':checks['actual_failed_then_rechecked']=r['script_version']>=2 and any(e.get('observation',{}).get('over_by_seconds',0)>0 for e in r['trace'])
        if name=='replaced' and r['status']=='completed':checks['replacement_uses_new_fact']=any(line['text']=='支持添加贴纸。' for s in r['storyboard'] for line in s['lines'])
        record={'case':name,'expected':expected,'actual':r['status'],'estimated_seconds':r['estimated_total_seconds'],'script_version':r['script_version'],'checks':checks,'passed':all(checks.values()),'result':f'{name}/result.json'};records.append(record)
        print(f"{name}: {'PASS' if record['passed'] else 'FAIL'} ({r['status']}, seconds={r['estimated_total_seconds']}, version={r['script_version']})",flush=True)
    summary={'mode':'offline_mock' if mode=='mock' else 'live_model','model':r['model'],'generated_at_utc':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),'source_sha256':source_digest(),'duration_seconds':round(time.monotonic()-started,3),'passed':sum(r['passed'] for r in records),'total':len(records),'cases':records,'boundary':'Synthetic material and deterministic time estimation. Live may draft within time initially: inspect trace for actual corrections; do not fabricate a forced overrun.'}
    if mode=='mock':
        stream=io.StringIO();t=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')));(dest/'tests.txt').write_text(stream.getvalue(),encoding='utf-8');summary['unit_tests']={'run':t.testsRun,'passed':t.wasSuccessful(),'failures':len(t.failures),'errors':len(t.errors)}
    write(dest/'summary.json',summary)
    lines=['# 实际生成及检查报告','',f"模式{summary['mode']}，{summary['passed']}/{summary['total']}场景通过。",'','Mock仅证明流程；真实模型可能首稿即达标，不能假称一定发生超时修正。每组目录有输入、素材、实际分镜及完整Trace。','','| 场景 | 实际状态 | 秒数 | 版本 | 检查 | 输出及Trace |','|---|---|---|---|---|---|']
    lines += [f"| {r['case']} | {r['actual']} | {r['estimated_seconds']} | {r['script_version']} | {'PASS' if r['passed'] else 'FAIL'} | [result]({r['result']}) |" for r in records]
    (dest/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return 0 if summary['passed']==summary['total'] and summary.get('unit_tests',{}).get('passed',True) else 1

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model',choices=['mock','live'],default='mock');p.add_argument('--output',default='examples/runs/mock');p.add_argument('--cases',nargs='+');a=p.parse_args();raise SystemExit(evaluate(a.model,a.output,a.cases))
