import unittest
from scripts.validate_frontend_execution import validate_projection,validate_decision

class EvidenceGuards(unittest.TestCase):
    def setUp(self):
        self.events=[dict(name='bash',arguments={'command':'check'},content='actual failure',metadata={'exit_code':1})]
        self.record=dict(training_eligible=False,messages=[{'role':'system'},{'role':'user'},
            dict(role='assistant',tool_calls=[dict(id='1',function={'name':'bash','arguments':{'command':'check'}})]),
            dict(role='tool',tool_call_id='1',content='actual failure',metadata={'exit_code':1}),{'role':'assistant'}])
    def test_failure_preserved(self):
        validate_projection(self.record,self.events)
        self.record['messages'][3]['content']='passed'
        with self.assertRaisesRegex(ValueError,'output changed'):validate_projection(self.record,self.events)
    def test_omitted_failure_rejected(self):
        self.record['messages']=self.record['messages'][:2]+self.record['messages'][-1:]
        with self.assertRaisesRegex(ValueError,'omitted'):validate_projection(self.record,self.events)
    def test_evidence_promotion_rejected(self):
        self.record['training_eligible']=True
        with self.assertRaisesRegex(ValueError,'ineligible'):validate_projection(self.record,self.events)
    def test_pre_edit_or_failed_final_check_rejected(self):
        events=self.events+[{'name':'edit'},dict(name='bash',metadata={'exit_code':0})]
        decision=dict(training_eligible=False,baseline_events=[1],final_check_events=[3])
        validate_decision(decision,events)
        decision['final_check_events']=[1]
        with self.assertRaisesRegex(ValueError,'after last edit'):validate_decision(decision,events)
        decision['final_check_events']=[3];events[-1]['metadata']['exit_code']=1
        with self.assertRaisesRegex(ValueError,'after last edit'):validate_decision(decision,events)

if __name__=='__main__':unittest.main()
