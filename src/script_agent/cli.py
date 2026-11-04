import argparse
import json
from pathlib import Path
import sys
from .engine import Agent
from .models import ChatModel, MockModel

def main(argv=None):
    p=argparse.ArgumentParser(description='Grounded editable short-video script')
    p.add_argument('--input',required=True);p.add_argument('--data',default='data/materials.json');p.add_argument('--output',default='.runtime/result.json')
    p.add_argument('--model',choices=['mock','live'],default='mock');p.add_argument('--max-steps',type=int,default=32)
    p.add_argument('--fault',choices=['search_materials_once','search_materials_always','estimate_duration_once','estimate_duration_always','check_rules_once','check_rules_always'])
    a=p.parse_args(argv)
    try:
        read=lambda path:json.loads(Path(path).read_text(encoding='utf-8-sig'))
        model=MockModel() if a.model=='mock' else ChatModel()
        r=Agent(model,read(a.data),a.max_steps,a.fault).run(read(a.input))
        path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':r['status'],'mode':r['mode'],'estimated_total_seconds':r['estimated_total_seconds'],'output':str(path)},ensure_ascii=False))
        return 0 if r['status']=='completed' else 3 if r['status'].startswith('incomplete_') else 2
    except (ValueError,OSError) as exc:
        print(json.dumps({'error':str(exc),'error_type':type(exc).__name__},ensure_ascii=False),file=sys.stderr);return 4
