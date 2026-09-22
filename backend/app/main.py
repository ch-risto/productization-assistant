import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from openai import OpenAIError, RateLimitError
from . import store, workflow, odoo
from .data import ROOT
from .schemas import AnalyzeRequest, CreateCardRequest, CardEdit, VersionRequest, ProfileRequest

load_dotenv(ROOT/'.env')


@asynccontextmanager
async def lifespan(app):
    store.init()
    # A crashed process cannot still own a pending export. Reconcile before any new write.
    with store.db(write=True) as c:
        c.execute("UPDATE exports SET status='uncertain' WHERE status='pending'")
    yield


app=FastAPI(title='Palvelupaja',lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','testserver'])


@app.middleware('http')
async def local_origin(request:Request,call_next):
    if request.method in ('POST','PUT','DELETE','PATCH'):
        origin=request.headers.get('origin')
        if origin and origin not in ('http://localhost:8000','http://127.0.0.1:8000','http://localhost:5173','http://127.0.0.1:5173'):
            return JSONResponse({'detail':'Tuntematon alkuperä.'},status_code=403)
    return await call_next(request)


@app.exception_handler(ValueError)
async def value_error(request,exc):
    return JSONResponse({'detail':str(exc)},status_code=409 if isinstance(exc,workflow.Conflict) else 422)


@app.exception_handler(KeyError)
async def missing(request,exc):
    return JSONResponse({'detail':str(exc)},status_code=404)


@app.exception_handler(odoo.IntegrationError)
async def integration_error(request,exc):
    return JSONResponse({'detail':str(exc)},status_code=502)


@app.exception_handler(OpenAIError)
async def llm_error(request,exc):
    if isinstance(exc, RateLimitError) and getattr(exc, 'code', '') in ('credit_balance_exhausted', 'insufficient_quota'):
        return JSONResponse({'detail':'OpenAI-projektin saldo tai käyttökiintiö on loppu. Tarkista API-projektin laskutus. Tallennettu työ säilyi; esimerkkitila on käytettävissä.'},status_code=502)
    return JSONResponse({'detail':'OpenAI-kutsu epäonnistui. Tarkista avain, mallin käyttöoikeus ja palvelun saatavuus. Tallennettu työ säilyi.'},status_code=502)


@app.get('/api/health')
def health():
    return {'ok':True,'odoo_mode':os.getenv('ODOO_MODE','fixture'),'llm_ready':bool(os.getenv('LLM_API_KEY')),'model':os.getenv('LLM_MODEL','gpt-4.1-mini')}


@app.get('/api/data')
def get_data():
    return workflow.snapshot()


@app.put('/api/profile')
def profile(body:ProfileRequest):
    with store.db(write=True) as c:
        c.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',('target_profile',body.text))
    return {'text':body.text}


@app.post('/api/runs')
def analyze(body:AnalyzeRequest):
    return workflow.run_analysis(body.mode)


@app.get('/api/runs')
def list_runs():
    with store.db() as c:
        return [json.loads(r['payload']) for r in c.execute('SELECT payload FROM runs ORDER BY created_at DESC LIMIT 20')]


@app.get('/api/runs/{run_id}')
def run(run_id:str):
    return workflow.get_run(run_id)


@app.post('/api/cards')
def create(body:CreateCardRequest):
    return workflow.create_card(body.run_id,body.idea_id)


@app.get('/api/cards')
def cards():
    with store.db() as c:
        return [json.loads(r['payload']) for r in c.execute('SELECT payload FROM cards ORDER BY rowid DESC')]


@app.get('/api/cards/{card_id}')
def card(card_id:str):
    return workflow.get_card(card_id)


@app.put('/api/cards/{card_id}')
def edit(card_id:str,body:CardEdit):
    return workflow.edit_card(card_id,body)


@app.post('/api/cards/{card_id}/approve')
def approve(card_id:str,body:VersionRequest):
    return workflow.approve(card_id,body.expected_version)


@app.post('/api/cards/{card_id}/export')
def export(card_id:str,body:VersionRequest):
    return workflow.export_card(card_id,body.expected_version)


dist=ROOT/'frontend/dist'
if dist.exists():
    app.mount('/',StaticFiles(directory=dist,html=True),name='frontend')
