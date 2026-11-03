"""Run reproducible tests and record environment versions. No network access."""
from pathlib import Path
import datetime, importlib.metadata, json, platform, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
results={}
def run(label,cmd):
    result=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
    (OUT/(label+'.log')).write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
    print(result.stdout)
    results[label]={'returncode':result.returncode,'passed':result.returncode==0}
    if result.returncode: print(result.stderr,file=sys.stderr)
    return result.returncode
code=run('pytest',[sys.executable,'-m','pytest','-q','tests/test_core.py','tests/test_i18n.py'])
if shutil.which('node'):
    code|=run('i18n_runtime',['node','tests/i18n_runtime.test.js'])
    code|=run('cross_language',[sys.executable,'tests/cross_language.py'])
    script="const fs=require('fs'),F=require('./fenix_core.js'),r=F.selfTests();fs.writeFileSync('results/js_self_tests.json',JSON.stringify(r,null,2)+'\\n');console.log(JSON.stringify(r,null,2));if(r.passed!==r.total)process.exit(1);"
    code|=run('js_self_tests',['node','-e',script])
else:
    results['cross_language']={'skipped':'Node.js not installed'}
    results['js_self_tests']={'skipped':'Node.js not installed'}
packages={}
for name in ['numpy','scipy','pytest','playwright']:
    try: packages[name]=importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError: pass
summary={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'software':'FENIX Lab 1.1.0 (numerical core 1.0.0)','python':sys.version,'platform':platform.platform(),
    'packages':packages,'results':results,'all_executed_suites_passed':code==0,
    'browser_test_report':'browser_i18n.json and browser_smoke.json are from separately executed optional UI tests.'}
(OUT/'verification_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sys.exit(code)
