"""Render only local poster files with Chromium; block all page network requests."""
from pathlib import Path
import argparse
import hashlib
import json
import os
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent


def render(browser_path=None):
    candidates=[Path(os.environ.get('PROGRAMFILES','C:/Program Files'))/'Google/Chrome/Application/chrome.exe',
        Path(os.environ.get('PROGRAMFILES(X86)','C:/Program Files (x86)'))/'Microsoft/Edge/Application/msedge.exe']
    executable=str(browser_path) if browser_path else next((str(p) for p in candidates if p.is_file()),None)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=executable,args=['--allow-file-access-from-files',
            '--disable-background-networking','--disable-component-update','--disable-sync','--no-first-run'])
        page=browser.new_page(viewport={'width':3180,'height':4495},device_scale_factor=1)
        blocked=[];errors=[]
        def route(request):
            if request.request.url.startswith(('http://','https://')):
                blocked.append(request.request.url);request.abort()
            else:request.continue_()
        page.route('**/*',route)
        page.on('pageerror',lambda exc:errors.append(str(exc)))
        page.emulate_media(media='print')
        page.goto((HERE/'poster.html').as_uri(),wait_until='load')
        page.evaluate('document.fonts.ready')
        metrics=page.evaluate('''() => {
          const box=e=>{const r=e.getBoundingClientRect(); return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom,right:r.right}};
          const poster=document.querySelector('.poster'); const footer=document.querySelector('footer');
          const columns=[...document.querySelectorAll('.column')].map(e=>({class:e.className,...box(e),scrollHeight:e.scrollHeight,clientHeight:e.clientHeight,lastChildBottom:box(e.lastElementChild).bottom}));
          const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);const duplicates=ids.filter((x,i)=>ids.indexOf(x)!==i);
          const claims=[...document.querySelectorAll('[data-claim]')].map(e=>({id:e.dataset.claim,text:e.textContent}));
          const chartBoxes=[...document.querySelectorAll('.chart')].map(e=>({name:e.dataset.view,...box(e)}));
          const overlaps=[];
          for(const col of document.querySelectorAll('.column')) {
            const children=[...col.children];
            for(let i=1;i<children.length;i++)if(box(children[i-1]).bottom>box(children[i]).y+1)overlaps.push({column:col.className,before:i-1,after:i});
          }
          const unresolved=[];
          for(const e of document.querySelectorAll('svg *'))for(const a of e.attributes){
            const refs=[...a.value.matchAll(/url\\(#([^)]*)\\)/g)].map(m=>m[1]);
            if(a.localName==='href' && a.value.startsWith('#'))refs.push(a.value.slice(1));
            for(const ref of refs)if(!document.getElementById(ref))unresolved.push(ref);
          }
          return {poster:box(poster),footer:box(footer),columns,duplicate_svg_ids:duplicates,
            chart_boxes:chartBoxes,sibling_overlaps:overlaps,unresolved_svg_references:unresolved,
            loaded_fonts:[...document.fonts].map(f=>({family:f.family,weight:f.weight,status:f.status})),claims,
            key_findings:document.querySelectorAll('.finding-grid>p').length,svg_views:document.querySelectorAll('.source-svg').length,
            author_names:[...document.querySelectorAll('.author strong')].map(e=>e.textContent)};
        }''')
        # Keep complete-source links in HTML, but prevent machine-local file://
        # hyperlinks from being embedded in the portable print PDF.
        page.evaluate("document.querySelectorAll('.chart').forEach(e=>e.removeAttribute('href'))")
        page.pdf(path=str(HERE/'poster.pdf'),print_background=True,prefer_css_page_size=True,
            display_header_footer=False,tagged=True)
        metrics.update(blocked_remote_requests=blocked,javascript_errors=errors,browser_version=browser.version)
        metrics['rendered_input_sha256']={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ['poster.html','poster.css']}
        metrics['pdf_sha256']=hashlib.sha256((HERE/'poster.pdf').read_bytes()).hexdigest()
        (HERE/'layout_check.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8',newline='\n')
        browser.close()
    print(json.dumps({k:metrics[k] for k in ['poster','footer','columns','duplicate_svg_ids','loaded_fonts']},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--browser',type=Path)
    args=parser.parse_args();render(args.browser)
