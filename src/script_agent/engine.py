from dataclasses import asdict
import copy
from .domain import (NEUTRAL, TITLES, TOPIC_SEARCH_HINTS, VISUALS, check, digest, estimate,
                     missing, topic_facts, topic_requirement, validate_data, validate_request, validate_script)
from .models import ModelError, ModelProtocolError

class Agent:
    def __init__(self,model,data,max_steps=32,fault=None):
        if type(max_steps) is not int or not 1<=max_steps<=100:raise ValueError('max_steps must be 1..100')
        self.model=model;self.data=validate_data(data);self.max_steps=max_steps;self.fault=fault;self.counts={}

    def execute(self,req,state,action):
        name,args=action.tool,action.arguments
        expected={'inspect_request':set(),'search_materials':{'query'},'compose_script':{'title','scenes'},'estimate_duration':set(),'check_rules':set(),'finish':set()}
        if name not in expected or not isinstance(args,dict) or set(args)!=expected[name]:return {'ok':False,'code':'INVALID_TOOL_ARGUMENTS'}
        self.counts[name]=self.counts.get(name,0)+1
        if self.fault in (name+'_once',name+'_always') and (self.fault.endswith('_always') or self.counts[name]==1):
            state['tool_errors']+=1;return {'ok':False,'code':'TOOL_UNAVAILABLE','tool':name}
        if name=='inspect_request':return {'ok':True,'request':req,'missing_fields':missing(req),'brand_rules':self.data['brand_rules'],'approved_neutral_lines':NEUTRAL,'approved_titles':TITLES,'visual_options':VISUALS,'scope':'Facts must be exact retrieved material statements. Narration is editable but edits require fresh checks.'}
        if name=='search_materials':
            if not isinstance(args['query'],str) or not 1<=len(args['query'].strip())<=200:return {'ok':False,'code':'INVALID_QUERY'}
            query = args['query'].strip()
            state['queries'].add(query)
            requirement = topic_requirement(req['topic'] or '')
            matches = [material for material in self.data['materials'] if requirement and (
                any(keyword in query for keyword in material['keywords']) or
                any(query in fact for fact in material['facts']))]
            for m in matches:state['materials'][m['id']]=copy.deepcopy(m)
            evidence = topic_facts(state['materials'].values(), req['topic'] or '')
            return {'ok':True, 'matches':matches, 'query':query, 'required_feature':requirement,
                    'topic_evidence':[{'source_id':mid,'fact':fact} for mid,fact in evidence],
                    'suggested_query':TOPIC_SEARCH_HINTS.get(requirement) if not evidence else None,
                    'note':'Retrieval keywords are discovery only. Use cited facts that support the original topic.'}
        if name=='compose_script':
            if missing(req):return {'ok':False,'code':'MISSING_INPUT'}
            if not state['materials']:return {'ok':False,'code':'MATERIAL_LOOKUP_REQUIRED'}
            if not topic_facts(state['materials'].values(), req['topic']):
                return {'ok':False, 'code':'TOPIC_EVIDENCE_MISSING', 'topic':req['topic'],
                        'suggested_query':TOPIC_SEARCH_HINTS.get(topic_requirement(req['topic']))}
            try:script=copy.deepcopy(validate_script(args))
            except ValueError as exc:return {'ok':False,'code':'INVALID_SCRIPT','reason':str(exc)}
            state['version']+=1;state['script']=script;state['duration']=None;state['rules']=None
            return {'ok':True,'script_version':state['version'],'script':script,'checks_invalidated':True,'next_required':'Estimate duration AND check rules for this exact version.'}
        if name in ('estimate_duration','check_rules'):
            if not state['script']:return {'ok':False,'code':'SCRIPT_REQUIRED'}
            if name == 'estimate_duration':
                result = estimate(state['script'], req['target_seconds'])
            else:
                result = check(state['script'], state['materials'].values(), self.data['brand_rules'], topic=req['topic'])
            result={'ok':True,'script_version':state['version'],**result}
            state['duration' if name=='estimate_duration' else 'rules']=result
            return result
        if name=='finish':
            status=None
            if missing(req):status='needs_info'
            elif state['tool_errors']>=2:status='tool_failed'
            elif len(state['queries'])>=2 and not topic_facts(state['materials'].values(), req['topic']):status='needs_materials'
            elif state['duration'] and state['rules']:
                if state['duration']['passed'] and state['rules']['passed']:status='completed'
                elif state['version']>=2:status='constraints_unmet'
            if not status:return {'ok':False,'code':'FINISH_REQUIRES_EVIDENCE','reason':'Look up material or validate the latest draft. On failed checks revise and recheck, or after a revised failure explicitly stop.'}
            state['status']=status;return {'ok':True,'code':'FINISHED','status':status}

    def run(self,raw):
        req=validate_request(raw)
        state={'run_id':req['request_id'],'materials':{},'queries':set(),'version':0,'script':None,'duration':None,'rules':None,'tool_errors':0,'status':None}
        history=[];error=None;stop='incomplete_step_limit'
        for step in range(1,self.max_steps+1):
            try:action=self.model.choose(req,copy.deepcopy(state),copy.deepcopy(history))
            except ModelProtocolError as exc:
                history.append({'step':step,'model_error':str(exc),'recoverable':True,'diagnostics':exc.diagnostics});continue
            except ModelError as exc:
                error=str(exc);stop='incomplete_model_error';history.append({'step':step,'model_error':error});break
            observation=self.execute(req,state,action);history.append({'step':step,'action':asdict(action),'observation':copy.deepcopy(observation)})
            if state['status']:stop='finished';break
        for i,event in enumerate(history):event['next_action']=history[i+1].get('action',{}).get('tool','model_error') if i+1<len(history) else 'stop'
        status=state['status'] or stop;script=state['script'];duration=state['duration'];rules=state['rules']
        scenes=[]
        if script:
            for i,s in enumerate(script['scenes']):
                scenes.append({'scene':i+1,**s,'narration':' '.join(x['text'] for x in s['lines']),'estimated_seconds':duration['scenes'][i]['estimated_seconds'] if duration else None})
        risks=copy.deepcopy(rules['risks']) if rules else [{'code':'RULES_NOT_CHECKED'}]
        if status == 'needs_materials':
            risks.append({'code':'TOPIC_EVIDENCE_MISSING','topic':req['topic']})
        if duration and not duration['passed']:risks.append({'code':'DURATION_EXCEEDED','over_by_seconds':duration['over_by_seconds']})
        if script and not duration:risks.append({'code':'DURATION_NOT_CHECKED'})
        return {'schema_version':'1.0','mode':self.model.mode,'model':self.model.name,'request':req,'status':status,'stop_reason':stop,'error':error,'title':script['title'] if script else None,'storyboard':scenes,'estimated_total_seconds':duration['estimated_total_seconds'] if duration else None,'source_material_ids':sorted({mid for s in scenes for line in s['lines'] for mid in line['source_ids']}),'retrieved_materials':list(state['materials'].values()),'script_version':state['version'],'duration_check':duration,'rule_check':rules,'risks':risks,'missing_fields':missing(req),'uncompleted_reason':None if status=='completed' else {'status':status,'missing_fields':missing(req),'tool_errors':state['tool_errors'],'risks':risks,'hint':'补充信息/素材，或修订后重新检查。'},'dataset_sha256':digest(self.data),'model_calls':len(history),'max_steps':self.max_steps,'trace':history,'editable':True,'published':False,'boundary':'Synthetic product facts and timing. Exact fact/neutral-line grammar restricts creativity. Duration is estimate, not audio/video measurement. Mock is not real model evidence.'}
