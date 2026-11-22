"""Render the self-contained poster locally; block page network requests."""
from pathlib import Path
import argparse
import hashlib
import json
import os
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent


def render(browser_path=None):
    (HERE / 'qa').mkdir(exist_ok=True)
    candidates = [Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'Google/Chrome/Application/chrome.exe',
                  Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / 'Microsoft/Edge/Application/msedge.exe']
    executable = str(browser_path) if browser_path else next((str(p) for p in candidates if p.is_file()), None)
    print('Starting local Chromium export.', flush=True)
    with sync_playwright() as p:
        print('Browser driver ready.', flush=True)
        browser = p.chromium.launch(headless=True, executable_path=executable, timeout=20000,
                                   args=['--allow-file-access-from-files', '--disable-background-networking',
                                         '--disable-component-update', '--disable-sync', '--no-first-run'])
        page = browser.new_page(viewport={'width': 3180, 'height': 4495}, device_scale_factor=1)
        print('Local browser ready.', flush=True)
        blocked, errors = [], []
        def route(r):
            if r.request.url.startswith(('http:', 'https:')):
                blocked.append(r.request.url); r.abort()
            else:
                r.continue_()
        page.route('**/*', route)
        page.on('pageerror', lambda exc: errors.append(str(exc)))
        page.emulate_media(media='print')
        page.goto((HERE / 'poster.html').as_uri(), wait_until='load')
        page.evaluate('document.fonts.ready')
        print('Page and local fonts loaded.', flush=True)
        metrics = page.evaluate(r'''() => {
          const box = e => {const b=e.getBoundingClientRect();return {x:b.x,y:b.y,width:b.width,height:b.height,right:b.right,bottom:b.bottom}};
          const sections=[...document.querySelector('.poster').children].map(e=>({name:e.className,...box(e),scrollHeight:e.scrollHeight,clientHeight:e.clientHeight}));
          const roles=[...document.querySelectorAll('[data-size-role]')].map(e=>({role:e.dataset.sizeRole,text:e.textContent.trim(),css_pt:parseFloat(getComputedStyle(e).fontSize)*.75,...box(e)}));
          const charts=[...document.querySelectorAll('.chart')].map(e=>({id:e.dataset.figure,...box(e)}));
          const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);
          const unresolved=[];
          for(const e of document.querySelectorAll('svg *'))for(const a of e.attributes){
            const refs=[...a.value.matchAll(/url\(#([^)]*)\)/g)].map(m=>m[1]);
            if(a.localName==='href'&&a.value.startsWith('#'))refs.push(a.value.slice(1));
            for(const ref of refs)if(!document.getElementById(ref))unresolved.push(ref);
          }
          const overlaps=[];
          for(const selector of ['.poster','.column','.background-data','figure','.key-findings','.findings-list']){
            for(const parent of document.querySelectorAll(selector)){
              const kids=[...parent.children];
              for(let i=1;i<kids.length;i++){
                const a=box(kids[i-1]),b=box(kids[i]);
                if(a.bottom>b.y+1 && Math.min(a.right,b.right)>Math.max(a.x,b.x)+1)overlaps.push({parent:parent.className,before:kids[i-1].className,after:kids[i].className,overlap_px:a.bottom-b.y});
              }
            }
          }
          const clone=document.querySelector('.poster').cloneNode(true);
          clone.querySelectorAll('svg,header,h2,h3,.figure-title,table').forEach(e=>e.remove());
          const textOverflows=[...document.querySelectorAll('h1,h2,h3,p,figcaption,.author strong,.author span,th,td')].filter(e=>e.scrollWidth>e.clientWidth+1).map(e=>({text:e.textContent.trim(),scrollWidth:e.scrollWidth,clientWidth:e.clientWidth}));
          const columns=[...document.querySelectorAll('.column')].map(e=>({number:e.dataset.column,...box(e),scrollHeight:e.scrollHeight,clientHeight:e.clientHeight,heading:e.querySelector('h2').textContent,figures:[...e.querySelectorAll('.chart')].map(f=>f.dataset.figure),lastChild:e.lastElementChild.className,children:[...e.children].map(k=>({tag:k.tagName,className:k.className,...box(k)}))}));
          const posterText=document.querySelector('.poster').textContent;
          return {poster:box(document.querySelector('.poster')),sections,roles,charts,overlaps,columns,
            header_removed_blocks:document.querySelectorAll('.study-design,.scope-row,.definition-row,.design-bottom,.research-question,.study-line').length,
            forbidden_visible_phrases:['VERSION 2','VERSION 3','READY FOR TEAM REVIEW','accompanying manifest','RESEARCH QUESTION','National context','Association / migration snapshots'].filter(t=>posterText.includes(t)),
            key_findings_column:document.querySelector('.key-findings').closest('.column').dataset.column,
            text_overflows:textOverflows,
            duplicate_ids:ids.filter((x,i)=>ids.indexOf(x)!==i),unresolved_svg_references:unresolved,
            loaded_fonts:[...document.fonts].map(f=>({family:f.family,weight:f.weight,status:f.status})),
            claims:[...document.querySelectorAll('[data-claim]')].map(e=>({id:e.dataset.claim,text:e.textContent})),
            non_chart_body_words:clone.textContent.trim().split(/\s+/).length,
            author_names:[...document.querySelectorAll('.author strong')].map(e=>e.textContent),
            author_ids:[...document.querySelectorAll('.author span')].map(e=>e.textContent),
            key_findings:document.querySelectorAll('.findings-list>p').length};
        }''')
        page.evaluate("document.querySelectorAll('.chart').forEach(e=>e.removeAttribute('href'))")
        page.pdf(path=str(HERE / 'poster.pdf'), print_background=True, prefer_css_page_size=True,
                 display_header_footer=False, tagged=True)
        metrics.update(blocked_requests=blocked, javascript_errors=errors, browser_version=browser.version)
        metrics['input_sha256'] = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in ['poster.html', 'poster.css']}
        metrics['pdf_sha256'] = hashlib.sha256((HERE / 'poster.pdf').read_bytes()).hexdigest()
        (HERE / 'qa/layout.json').write_text(json.dumps(metrics, indent=2) + '\n', encoding='utf-8', newline='\n')
        browser.close()
    print(json.dumps({'columns': [{k: c[k] for k in ['number','width','height','scrollHeight','clientHeight','heading','figures','lastChild']} for c in metrics['columns']], 'overlaps':metrics['overlaps'], 'text_overflows':metrics['text_overflows'], 'header_removed_blocks':metrics['header_removed_blocks'],'forbidden_visible_phrases':metrics['forbidden_visible_phrases']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', type=Path)
    render(parser.parse_args().browser)
