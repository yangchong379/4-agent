import hashlib
import json
import math
import re

NEUTRAL=['今天看看这个功能。','跟着画面一起看。','你可以按需要继续编辑。','现在试着写下你的想法。']
VISUALS=['产品界面示意','字幕局部特写','创作者出镜','结尾文字卡']
TITLES=['小影功能演示','一个功能小技巧','看看这个功能']

TOPIC_ALIASES = {
    '字幕': '字幕', '文字上屏': '字幕', '自动文字上屏': '字幕',
    '字幕样式': '字幕样式', '手动调整字幕样式': '字幕样式',
    '贴纸': '贴纸', '添加贴纸': '贴纸',
    '剪辑': '通用功能', '视频': '通用功能', '视频剪辑': '通用功能',
}
FEATURE_FACTS = {
    '字幕': {'支持字幕', '支持字幕样式', '支持手动调整字幕样式'},
    '字幕样式': {'支持字幕样式', '支持手动调整字幕样式'},
    '贴纸': {'支持贴纸', '支持添加贴纸'},
}
TOPIC_SEARCH_HINTS = {'字幕': '字幕样式', '字幕样式': '字幕样式', '贴纸': '贴纸', '通用功能': '小影'}


def topic_requirement(topic):
    """Resolve the supported feature vocabulary from the immutable user topic."""
    normalized = topic.strip().strip('。！？?!')
    feature = normalized.removeprefix('小影').strip()
    for suffix in ('使用教程', '功能介绍', '功能演示', '教程', '功能', '演示'):
        if feature.endswith(suffix):
            feature = feature.removesuffix(suffix).strip()
            break
    if not feature and normalized.startswith('小影'):
        return '通用功能'
    return TOPIC_ALIASES.get(feature)


def supports_topic(fact, requirement):
    return requirement == '通用功能' or fact.strip().rstrip('。.!！') in FEATURE_FACTS.get(requirement, ())


def topic_facts(materials, topic):
    requirement = topic_requirement(topic)
    return [(material['id'], fact) for material in materials for fact in material['facts']
            if supports_topic(fact, requirement)]

def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def validate_request(raw):
    keys={'request_id','topic','audience','platform','target_seconds','style'}
    if not isinstance(raw,dict) or set(raw)-keys:raise ValueError('unknown input fields')
    req={k:raw.get(k) for k in sorted(keys)}
    if not isinstance(req['request_id'],str) or not 1<=len(req['request_id'])<=100:raise ValueError('request_id required')
    for k in ('topic','audience','platform','style'):
        if req[k] is not None and (not isinstance(req[k],str) or len(req[k])>200):raise ValueError('invalid '+k)
        if isinstance(req[k],str):req[k]=req[k].strip()
    if req['target_seconds'] is not None and (type(req['target_seconds']) is not int or not 1<=req['target_seconds']<=180):raise ValueError('target_seconds must be integer 1..180')
    return req

def missing(req):return [k for k in ('topic','audience','platform','target_seconds','style') if req.get(k) in (None,'')]

def validate_data(data):
    if not isinstance(data,dict) or set(data)!={'description','materials','brand_rules'} or not isinstance(data['materials'],list):raise ValueError('invalid material dataset')
    seen=set()
    for m in data['materials']:
        if set(m)!={'id','product','keywords','facts'} or not isinstance(m['id'],str) or not m['id'] or m['id'] in seen or m['product']!='小影' or not isinstance(m['keywords'],list) or not m['keywords'] or not all(isinstance(x,str) and x for x in m['keywords']) or not isinstance(m['facts'],list) or not m['facts'] or not all(isinstance(x,str) and 0<len(x)<=200 for x in m['facts']):raise ValueError('invalid material')
        seen.add(m['id'])
    rules=data['brand_rules']
    if not isinstance(rules,dict) or set(rules)!={'version','prohibited_phrases','characters_per_second','minimum_scene_seconds'} or rules['characters_per_second']!=4 or rules['minimum_scene_seconds']!=2 or not isinstance(rules['prohibited_phrases'],list) or not all(isinstance(x,str) for x in rules['prohibited_phrases']):raise ValueError('unsupported brand/timing rules')
    return data

def validate_script(args):
    if not isinstance(args,dict) or set(args)!={'title','scenes'} or not isinstance(args['title'],str) or len(args['title'])>100 or not isinstance(args['scenes'],list) or not 1<=len(args['scenes'])<=8:raise ValueError('title and 1..8 scenes required')
    for s in args['scenes']:
        if not isinstance(s,dict) or set(s)!={'visual','lines','hold_seconds'} or s['visual'] not in VISUALS or type(s['hold_seconds']) is not int or not 0<=s['hold_seconds']<=15 or not isinstance(s['lines'],list) or not 1<=len(s['lines'])<=4:raise ValueError('invalid scene')
        for line in s['lines']:
            if not isinstance(line,dict) or set(line)!={'text','source_ids'} or not isinstance(line['text'],str) or not 1<=len(line['text'])<=200 or not isinstance(line['source_ids'],list) or len(line['source_ids'])>10 or any(not isinstance(x,str) for x in line['source_ids']) or len(line['source_ids'])!=len(set(line['source_ids'])):raise ValueError('invalid narration line')
    return args

def estimate(script,target):
    scenes=[]
    for i,s in enumerate(script['scenes'],1):
        count=len(re.findall(r'\w',''.join(x['text'] for x in s['lines'])))
        spoken=math.ceil(count/4*10)/10
        seconds=round(max(2,spoken)+s['hold_seconds'],1)
        scenes.append({'scene':i,'spoken_characters':count,'spoken_seconds':spoken,'hold_seconds':s['hold_seconds'],'estimated_seconds':seconds})
    total=round(sum(s['estimated_seconds'] for s in scenes),1)
    return {'passed':total<=target,'estimated_total_seconds':total,'target_seconds':target,'over_by_seconds':round(max(0,total-target),1),'scenes':scenes,'method':'Synthetic 4 spoken characters/second, min 2 seconds per shot plus explicit holds. Not TTS measurement.'}

def check(script, materials, rules, *, topic):
    risks=[];sources={m['id']:m for m in materials};grounded=[]
    requirement = topic_requirement(topic)
    if script['title'] not in TITLES:risks.append({'code':'TITLE_NOT_APPROVED','location':'title'})
    for i,s in enumerate(script['scenes'],1):
        for j,line in enumerate(s['lines'],1):
            text,ids=line['text'],line['source_ids'];location=f'scene {i} line {j}'
            if text in NEUTRAL and not ids:continue
            if not ids or any(mid not in sources or text not in sources[mid]['facts'] for mid in ids):risks.append({'code':'UNSUPPORTED_FACT_OR_CITATION','location':location,'text':text})
            else:
                grounded.append(text)
                if not supports_topic(text, requirement):
                    risks.append({'code':'OFF_TOPIC_FACT','location':location,'text':text,'topic':topic})
            if any(p in text for p in rules['prohibited_phrases']):risks.append({'code':'BRAND_PROHIBITED_CLAIM','location':location,'text':text})
    if not grounded:risks.append({'code':'NO_GROUNDED_PRODUCT_FACT'})
    if not any(supports_topic(fact, requirement) for fact in grounded):
        risks.append({'code':'TOPIC_EVIDENCE_MISSING','topic':topic})
    if any(s['visual']=='字幕局部特写' for s in script['scenes']) and not any(supports_topic(fact, '字幕') for fact in grounded):risks.append({'code':'UNSUPPORTED_VISUAL_CONTEXT'})
    return {'passed':not risks,'risks':risks,'rule_version':rules['version'],'note':'Exact citations, topic vocabulary and approved neutral lines are checked.'}
