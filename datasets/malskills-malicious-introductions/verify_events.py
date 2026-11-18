"""Capture primary-source availability and exact evidence anchors, not full articles."""
import concurrent.futures
import hashlib
import html.parser
import json
import re
from pathlib import Path

import collect_history as collector

ROOT=Path(__file__).resolve().parent
SOURCES=[
 {'id':'SNYK-CLAWDHUB','url':'https://snyk.io/articles/clawdhub-malicious-campaign-ai-agent-skills/','title':'Snyk clawdhub campaign investigation','event_date':'2026-02-02','identities':['zaycv/clawhub'],'required_anchors':['Ddoy233','openclawcli','zaycv','91.92.242.30'],'supports':'将 zaycv/clawhub 与假 CLI 分发事件关联，列出 Ddoy233/openclawcli、加密 ZIP、glot 引导及恶意下载 IP。报告没有给出首个发布版本号。'},
 {'id':'SNYK-TOXICSKILLS','url':'https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/','title':'Snyk ToxicSkills investigation','publication_date':'2026-02-05','identities':['zaycv/clawhud','zaycv/clawhub1','aslaep123/polymarket-traiding-bot','aslaep123/base-agent','aslaep123/bybit-agent','moonshine-100rze/moltbook-lm8','pepe276/publish-dist'],'required_anchors':['polymarket-traiding-bot','base-agent','bybit-agent','moltbook-lm8','publish-dist'],'supports':'明确列出这些 owner/slug；这是独立安全事件关联，不证明其任意历史版本都恶意，也没有完整发布序列。'},
 {'id':'KOI-CLAW-HAVOC','url':'https://www.paloaltonetworks.com/blog/security-operations/clawhavoc-ai-agent-skills-poisoning/','title':'Koi ClawHavoc investigation republished by Palo Alto Networks','publication_date':'2026-02-01','reported_update_date':'2026-02-16','identities':[],'required_anchors':['91.92.242.30','better-polymarket','glot.io'],'supports':'提供攻击链、主机 IOC 和部分技能名称；仅名称或发布者相似不能单独证明具体 owner/slug 及首次版本。'},
]

class Extract(html.parser.HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_data(self,data):self.parts.append(data)

def main():
 results=[]
 for source in SOURCES:
  item=dict(source)
  try:
   data=collector.raw_get.__globals__['requests'].get(source['url'],proxies=collector.urllib.request.getproxies(),timeout=(15,40)).content
   # Keep the local raw response outside the distributable evidence set.
   work=ROOT/'work/event_pages';work.mkdir(parents=True,exist_ok=True);(work/(source['id']+'.html')).write_bytes(data)
   parser=Extract();parser.feed(data.decode('utf-8',errors='replace'));text=' '.join(parser.parts)
   anchors={a:a.lower() in text.lower() for a in source['required_anchors']}
   item.update(response_sha256=hashlib.sha256(data).hexdigest(),anchor_presence=anchors,status='primary_source_content_verified' if all(anchors.values()) else 'content_not_verified')
  except Exception as error:item.update(status='unavailable',error=type(error).__name__)
  results.append(item)
 collector.api.authenticate()
 for number,skill in [(108,'zaycv/clawhub'),(124,'zaycv/linkedin-job-application'),(138,'zaycv/autoupdater'),(154,'zaycv/deepresearch')]:
  item={'id':f'CLAWHUB-ISSUE-{number}','url':f'https://github.com/openclaw/clawhub/issues/{number}','identities':[skill],'title':'ClawHub security incident issue','supports':'发布在官方项目问题区的事件记录；需区分初始报告与维护者确认，不将所有社区评论等同于官方通告。'}
  try:
   issue=collector.api.api(f'/repos/openclaw/clawhub/issues/{number}')
   comments=collector.api.api(f'/repos/openclaw/clawhub/issues/{number}/comments?per_page=100')
   item.update(created_at=issue['created_at'],closed_at=issue['closed_at'],state=issue['state'],reporter=issue['user']['login'],reported_author_association=issue['author_association'],body_sha256=hashlib.sha256((issue.get('body') or '').encode()).hexdigest(),title_observed=issue['title'])
   owner,slug=skill.split('/')
   item['identity_present_in_report']=owner.lower() in (issue.get('body') or '').lower() and slug.lower() in (issue.get('body') or '').lower()
   item['project_response']=[{'url':c['html_url'],'login':c['user']['login'],'association':c['author_association'],'created_at':c['created_at'],'body_sha256':hashlib.sha256(c['body'].encode()).hexdigest(),'mentions_mitigation':bool(re.search(r'banned|hidden|takedown|removed|mitigated',c['body'],re.I))} for c in comments if c['author_association'] in ['OWNER','MEMBER','COLLABORATOR','CONTRIBUTOR']]
   item['status']='primary_project_issue_verified' if item['identity_present_in_report'] else 'identity_not_verified'
  except Exception as error:item.update(status='unavailable',error=str(error)[:120])
  results.append(item)
 checks=[]
 for repo in ['openclaw/skills','clawdbot/skills',collector.REPOSITORY]:
  try:
   info=collector.api.api('/repos/'+repo,cache=False)
   checks.append({'repository':repo,'status':'accessible','repository_id':info['id'],'full_name':info['full_name'],'default_branch':info['default_branch']})
  except Exception as error:checks.append({'repository':repo,'status':str(error)})
 collector.save(ROOT/'source/event_sources.json',results)
 collector.save(ROOT/'source/repository_availability.json',checks)
 print(json.dumps({'events':[{'id':x['id'],'status':x['status']} for x in results],'repositories':checks}))

if __name__=='__main__':main()
