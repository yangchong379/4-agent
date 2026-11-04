import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from script_agent.domain import NEUTRAL, TITLES, check, estimate, validate_data, validate_request
from script_agent.engine import Agent
from script_agent.models import Action, MockModel, ModelError

def request(**extra):return {'request_id':'r','topic':'小影字幕','audience':'新手创作者','platform':'抖音','target_seconds':30,'style':'轻松',**extra}

class TestScript(unittest.TestCase):
    def setUp(self):self.data=json.loads((ROOT/'data/materials.json').read_text(encoding='utf-8'))
    def runq(self,req=None,**kw):return Agent(MockModel(),self.data,**kw).run(req or request())
    def test_duration_is_revised_and_rechecked(self):
        r=self.runq();self.assertEqual(r['status'],'completed');self.assertGreaterEqual(r['script_version'],2)
        durations=[e['observation'] for e in r['trace'] if e.get('action',{}).get('tool')=='estimate_duration' and e['observation'].get('ok')]
        self.assertFalse(durations[0]['passed']);self.assertTrue(durations[-1]['passed']);self.assertLessEqual(r['estimated_total_seconds'],30)
        self.assertEqual(r['duration_check']['script_version'],r['rule_check']['script_version'])
    def test_normal_longer_target(self):self.assertEqual(self.runq(request(target_seconds=45))['status'],'completed')
    def test_missing_audience(self):self.assertEqual(self.runq(request(audience=None))['status'],'needs_info')
    def test_missing_duration(self):self.assertEqual(self.runq(request(target_seconds=None))['status'],'needs_info')
    def test_unknown_material(self):self.assertEqual(self.runq(request(topic='量子计算硬件'))['status'],'needs_materials')
    def test_query_rewrite(self):
        r=self.runq(request(topic='自动文字上屏'));self.assertEqual(r['status'],'completed')
        matches=[e['observation'].get('matches') for e in r['trace'] if e.get('action',{}).get('tool')=='search_materials']
        self.assertEqual(matches[0],[]);self.assertTrue(matches[1])
    def test_tool_retry(self):self.assertEqual(self.runq(fault='search_materials_once')['status'],'completed')
    def test_tool_permanent(self):self.assertEqual(self.runq(fault='estimate_duration_always')['status'],'tool_failed')
    def test_step_limit_preserves_draft(self):
        r=self.runq(max_steps=3);self.assertEqual(r['status'],'incomplete_step_limit');self.assertTrue(r['storyboard']);self.assertIsNone(r['estimated_total_seconds'])
    def test_impossible_time_explicit(self):self.assertEqual(self.runq(request(target_seconds=1))['status'],'constraints_unmet')
    def test_sum_of_scenes(self):
        r=self.runq();self.assertEqual(round(sum(s['estimated_seconds'] for s in r['storyboard']),1),r['estimated_total_seconds'])
    def test_material_replace_changes_narration(self):
        self.data['materials'][0]['facts']=['支持添加贴纸。'];r=self.runq();self.assertEqual(r['status'],'completed');self.assertIn('支持添加贴纸。',''.join(s['narration'] for s in r['storyboard']))
    def test_unsupported_percentage_rejected(self):
        script={'title':TITLES[0],'scenes':[{'visual':'产品界面示意','lines':[{'text':'效率提升80%。','source_ids':['P01']}],'hold_seconds':0}]}
        r=check(script,self.data['materials'],self.data['brand_rules']);self.assertFalse(r['passed']);self.assertIn('UNSUPPORTED_FACT_OR_CITATION',{x['code'] for x in r['risks']})
    def test_wrong_source_id_rejected(self):
        script={'title':TITLES[0],'scenes':[{'visual':'产品界面示意','lines':[{'text':'支持字幕。','source_ids':['P02']}],'hold_seconds':0}]}
        self.assertFalse(check(script,self.data['materials'],self.data['brand_rules'])['passed'])
    def test_all_neutral_is_not_grounded_script(self):
        script={'title':TITLES[0],'scenes':[{'visual':'产品界面示意','lines':[{'text':NEUTRAL[0],'source_ids':[]}],'hold_seconds':0}]}
        self.assertFalse(check(script,self.data['materials'],self.data['brand_rules'])['passed'])
    def test_update_invalidates_both_checks(self):
        a=Agent(MockModel(),self.data);state={'materials':{'P01':self.data['materials'][0]},'version':1,'script':None,'duration':{'passed':True},'rules':{'passed':True},'tool_errors':0}
        args={'title':TITLES[0],'scenes':[{'visual':'产品界面示意','lines':[{'text':'支持字幕。','source_ids':['P01']}],'hold_seconds':0}]}
        self.assertTrue(a.execute(request(),state,Action('compose_script',args))['ok']);self.assertIsNone(state['duration']);self.assertIsNone(state['rules'])
    def test_false_finish_cannot_bypass_checks(self):
        class Early(MockModel):
            def choose(self,*args):return Action('finish',rationale='直接结束')
        r=Agent(Early(),self.data,max_steps=2).run(request());self.assertEqual(r['status'],'incomplete_step_limit')
    def test_model_error_not_mock_fallback(self):
        class Fail(MockModel):
            def choose(self,*args):raise ModelError('MODEL_TRANSPORT_FAILED')
        self.assertEqual(Agent(Fail(),self.data).run(request())['status'],'incomplete_model_error')
    def test_bad_input_type(self):
        with self.assertRaises(ValueError):validate_request(request(target_seconds=True))
    def test_empty_facts_rejected(self):
        self.data['materials'][0]['facts']=[]
        with self.assertRaises(ValueError):validate_data(self.data)
    def test_rule_failure_is_corrected(self):
        class BadFirst(MockModel):
            def choose(self,req,state,history):
                a=super().choose(req,state,history)
                if a.tool=='compose_script' and state['version']==0:a.arguments['scenes'][1]['lines'][0]['text']='效率提升80%。'
                return a
        r=Agent(BadFirst(),self.data).run(request())
        self.assertEqual(r['status'],'completed');self.assertTrue(any(not e['observation']['passed'] for e in r['trace'] if e.get('action',{}).get('tool')=='check_rules'))

if __name__=='__main__':unittest.main()
