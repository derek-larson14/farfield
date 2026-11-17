import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS=Path(__file__).resolve().parents[1]/'skills/farfield/scripts'
sys.path.insert(0,str(SCRIPTS))
import library
import social
import audio

class MemoryTest(unittest.TestCase):
    def test_failed_discovery_retries_but_success_survives_failed_recheck(self):
        with tempfile.TemporaryDirectory() as root:
            url='https://example.org/post'
            library.record(root,url,'test','Article','discovered')
            library.record(root,url,'test','Article','failed')
            self.assertFalse(library.lookup(root,url)['already_read'])
            raw=Path(root)/'raw.txt';raw.write_text('Evidence')
            library.record(root,url,'test','Article','read',revision='v1',raw=raw)
            library.record(root,url,'test','Article','failed')
            self.assertTrue(library.lookup(root,url+'?utm_source=news#top','v1')['already_read'])
            self.assertFalse(library.lookup(root,url,'v2')['already_read'])
            self.assertFalse(library.lookup(root,url)['previously_shown'])
            library.record(root,url,'test','Article','shown',revision='v1',raw=raw,brief='briefs/today.md')
            self.assertTrue(library.lookup(root,url)['previously_shown'])
            raw.unlink()
            self.assertIsNone(library.lookup(root,url)['cached_raw'])
            self.assertTrue(library.lookup(root,url)['already_read'])
            self.assertIn('Article',(Path(root)/'reading-history.md').read_text())
    def test_semantic_query_is_not_stripped(self):
        self.assertNotEqual(library.canonical('https://example.org/?id=1'),library.canonical('https://example.org/?id=2'))
        with self.assertRaises(ValueError): library.canonical('https://example.org/feed?token=secret')

class SocialTest(unittest.TestCase):
    def test_default_off_and_dry_run_never_call_provider(self):
        with tempfile.TemporaryDirectory() as root, patch.object(social,'request') as call:
            with self.assertRaises(ValueError): social.search(root,'evals','2026-11-01','2026-11-08')
            result=social.search(root,'evals','2026-11-01','2026-11-08',True)
            self.assertFalse(result['paid_request_sent']);call.assert_not_called()
            self.assertIn('x_search',result['request']['tools'][0]['parameters'])
    def test_bad_budget_blocks_paid_call_and_repeat_is_blocked(self):
        with tempfile.TemporaryDirectory() as root, patch.object(social.radar,'keys',return_value={'OPENROUTER_API_KEY':'fake'}):
            (Path(root)/'social.json').write_text(json.dumps({'enabled':True,'monthly_limit_usd':5}))
            with patch.object(social,'request',return_value={'data':{'limit':None,'limit_remaining':20}}) as call:
                with self.assertRaises(ValueError): social.search(root,'evals','2026-11-01','2026-11-08')
                self.assertEqual(call.call_count,1)
            with patch.object(social,'request',side_effect=[{'data':{'limit':5,'limit_remaining':5}},{'output':[],'usage':{'cost':.2}}]) as call:
                out=social.search(root,'evals','2026-11-01','2026-11-08')
                self.assertEqual(out['status'],'unverified-leads')
                self.assertEqual(call.call_count,2)
            with patch.object(social,'request',return_value={'data':{'limit':5,'limit_remaining':4.8}}) as call:
                with self.assertRaises(ValueError): social.search(root,'evals','2026-11-01','2026-11-08')
                self.assertEqual(call.call_count,1)
    def test_daily_cap_is_not_a_monthly_cap(self):
        with tempfile.TemporaryDirectory() as root, patch.object(social.radar,'keys',return_value={'OPENROUTER_API_KEY':'fake'}):
            (Path(root)/'social.json').write_text('{"enabled":true,"monthly_limit_usd":5}')
            with patch.object(social,'request',return_value={'data':{'limit':5,'limit_remaining':5,'limit_reset':'daily'}}) as call:
                with self.assertRaises(ValueError): social.search(root,'evals','2026-11-01','2026-11-08')
                self.assertEqual(call.call_count,1)

    def test_dates_and_cost_math(self):
        with self.assertRaises(ValueError): social.payload('test','2026-11-08','2026-11-01')
        self.assertAlmostEqual(social.estimate(20,2,10000,1000,1),.151)
        self.assertAlmostEqual(social.estimate(100,10,50000,3000,2),.728)
    def test_timeout_reserves_attempt_without_retry(self):
        with tempfile.TemporaryDirectory() as root, patch.object(social.radar,'keys',return_value={'OPENROUTER_API_KEY':'fake'}):
            (Path(root)/'social.json').write_text('{"enabled":true,"monthly_limit_usd":5}')
            with patch.object(social,'request',side_effect=[{'data':{'limit':5,'limit_remaining':5}},TimeoutError()]):
                with self.assertRaises(TimeoutError): social.search(root,'evals','2026-11-01','2026-11-08')
            records=list((Path(root)/'state/social').glob('*.json'))
            self.assertEqual(json.loads(records[0].read_text())['status'],'failed-cost-unknown')

class AudioCacheTest(unittest.TestCase):
    def test_cloud_model_selection_and_payload(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(audio.use(root,'openrouter','microsoft/mai-transcribe-2')['model'],'microsoft/mai-transcribe-2')
            with self.assertRaises(ValueError): audio.use(root,'openrouter','invented/model')
            sample=Path(root)/'sample.mp3';sample.write_bytes(b'audio')
            class Reply:
                def __enter__(self): return self
                def __exit__(self,*args): pass
                def read(self): return b'{"text":"hello", "usage":{"cost":0.01}}'
            with patch.object(audio.urllib.request,'urlopen',return_value=Reply()) as request:
                self.assertEqual(audio.openrouter_chunk(sample,'fake','elevenlabs/scribe-v2'),('hello',.01))
                payload=json.loads(request.call_args.args[0].data)
                self.assertEqual(payload['model'],'elevenlabs/scribe-v2')
    def test_cached_clip_is_not_reused_as_full_episode(self):
        import hashlib
        with tempfile.TemporaryDirectory() as root:
            audio.use(root,'openrouter','microsoft/mai-transcribe-2')
            url='https://example.org/audio.mp3'
            key=json.dumps([url,'openrouter','microsoft/mai-transcribe-2',120])
            folder=Path(root)/'evidence/raw';folder.mkdir(parents=True)
            raw=folder/(hashlib.sha256(key.encode()).hexdigest()[:20]+'.transcript.txt');raw.write_text('transcript')
            raw.with_suffix('.json').write_text('{"backend":"openrouter","usd":0.1}')
            with patch.object(audio.urllib.request,'urlopen') as request,patch.object(audio.radar,'keys',return_value={}):
                self.assertTrue(audio.transcribe(root,url,max_secs=120)['cached'])
                with self.assertRaises(ValueError): audio.transcribe(root,url)
                request.assert_not_called()
