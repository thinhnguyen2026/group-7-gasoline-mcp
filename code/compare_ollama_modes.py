"""Run one matched Ollama pair with and without live MCP database tools."""
import asyncio, hashlib, json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
from ollama import AsyncClient
from mcp import Client

CODE = Path(__file__).resolve().parent
ROOT = CODE / 'results'
ROOT.mkdir(exist_ok=True)
sys.path.insert(0,str(CODE))
from mcp_helpers import result_value
from jsonschema import validate

MODEL = 'qwen3:0.6b'
PROMPT = ('What was the average U.S. regular gasoline price in 2015 compared with 2020? '
          'Report both annual prices, the dollar and percentage change from 2015 to 2020, '
          'units, and any relevant methodology caution.')
SYSTEM = ('Answer the question concisely. Use available tools to retrieve the two annual '
          'source prices and their comparison when tools are provided. If tools are not '
          'provided, answer from your existing knowledge. Clearly state uncertainty and do '
          'not invent access to sources or databases. Do not infer causes from two observations.')
OPTIONS = {'temperature':0,'num_predict':2048,'seed':7}

async def run(mode):
    log = {'mode':mode,'model':MODEL,'prompt':PROMPT,'system_prompt':SYSTEM,
           'think':True,'options':OPTIONS,'started_utc':datetime.now(timezone.utc).isoformat(),
           'calls':[],'rounds':[],'status':'INCOMPLETE'}
    out = ROOT / f'rerun_{mode}.json'
    started = time.perf_counter()
    llm = AsyncClient(host='http://127.0.0.1:11434',timeout=360)
    messages = [{'role':'system','content':SYSTEM},{'role':'user','content':PROMPT}]
    async def exchange(client=None):
        definitions = (await client.list_tools()).tools if client else []
        schemas={d.name:d.input_schema for d in definitions}
        tools=[{'type':'function','function':{'name':d.name,'description':d.description,
                 'parameters':d.input_schema}} for d in definitions]
        log['tool_definitions']=tools
        seen=set()
        for _ in range(4 if client else 1):
            kwargs={'model':MODEL,'messages':messages,'think':True,'options':OPTIONS}
            if client: kwargs['tools']=tools
            response=await llm.chat(**kwargs)
            log['rounds'].append(response.model_dump(mode='json',exclude_none=True))
            messages.append(response.message.model_dump(exclude_none=True))
            if response.done_reason=='length':
                log['answer']=response.message.content
                log['status']='TOKEN_LIMIT'
                return
            calls=response.message.tool_calls or []
            if not calls:
                log['answer']=response.message.content
                log['status']='ANSWER_RECEIVED'
                return
            if client is None: raise RuntimeError('No-tools response unexpectedly requested a tool')
            for call in calls:
                name,args=call.function.name,call.function.arguments
                if name not in schemas: raise ValueError('Unknown tool')
                validate(args,schemas[name])
                signature=json.dumps([name,args],sort_keys=True)
                if signature in seen or len(log['calls'])>=6: raise RuntimeError('Tool loop limit')
                seen.add(signature)
                value=result_value(await client.call_tool(name,args))
                log['calls'].append({'tool':name,'arguments':args,'result':value})
                messages.append({'role':'tool','tool_name':name,'content':json.dumps(value)})
        raise RuntimeError('Round limit')
    try:
        models=await llm.list()
        log['model_digest']=next(m.digest for m in models.models if m.model==MODEL)
        if mode=='with_mcp':
            async with Client('http://127.0.0.1:5000/mcp') as client: await exchange(client)
        else: await exchange()
    except Exception as exc:
        log['error']=repr(exc)
        log['status']='ERROR'
    finally:
        log['elapsed_seconds']=round(time.perf_counter()-started,3)
        log['finished_utc']=datetime.now(timezone.utc).isoformat()
        out.write_text(json.dumps(log,indent=2),encoding='utf-8')
        print(json.dumps({k:log.get(k) for k in ('mode','status','answer','error','elapsed_seconds')},indent=2))
    return log

if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in {'without_mcp','with_mcp'}:
        raise SystemExit('Usage: python compare_ollama_modes.py without_mcp|with_mcp')
    asyncio.run(run(sys.argv[1]))
