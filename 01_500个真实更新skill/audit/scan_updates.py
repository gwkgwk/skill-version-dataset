"""Static triage only. Reads artifacts as data; never imports or executes them."""
import csv
import argparse
import difflib
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
RULES = [
    ('download_execute', 'high', r'(?:curl|wget)\b.{0,300}\|\s*(?:sudo\s+)?(?:ba)?sh\b|(?:iex|Invoke-Expression)\b.{0,200}(?:DownloadString|iwr|Invoke-WebRequest)|(?:DownloadString|iwr|Invoke-WebRequest).{0,200}\|\s*iex\b'),
    ('decode_execute', 'high', r'(?:exec|eval)\s*\(.{0,150}(?:b64decode|base64|fromhex)|(?:base64\s+(?:-d|--decode)|b64decode).{0,150}\|\s*(?:ba)?sh|powershell.{0,100}-(?:enc|encodedcommand)\b'),
    ('private_key_material', 'high', r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    ('prompt_authority_override', 'high', r'(?:ignore|disregard|override).{0,65}(?:previous|prior|system|developer|safety).{0,50}(?:instructions?|prompts?|polic(?:y|ies))|忽略.{0,20}(?:系统|先前|之前).{0,20}(?:指令|提示)|(?:bypass|disable).{0,30}(?:safety|security)\s+(?:checks?|filters?|polic(?:y|ies))'),
    ('concealment', 'high', r'(?:do not|don.t|never)\s+(?:tell|inform|notify|alert)\s+(?:the\s+)?user|(?:hide|conceal).{0,45}(?:from\s+(?:the\s+)?user|activity|execution)|不要.{0,12}(?:告诉|通知)用户'),
    ('credential_read', 'medium', r'(?:~/|\$HOME/|/home/[^/ ]+/|/root/)?\.ssh/(?:id_|authorized_keys)|\.aws/credentials|/etc/(?:shadow|passwd)|(?:Login Data|Cookies\.sqlite|cookies\.sqlite)|(?:cat|read|open|Get-Content).{0,65}(?:\.env\b|credentials|private.key)|(?:printenv|os\.environ(?:\b|\[)|process\.env\b)'),
    ('upload_or_post', 'medium', r'\b(?:curl|wget)\b.{0,180}(?:--upload-file|--data(?:-binary|-raw)?\s+@|-T\s+|-F\s+|--form\s+|-X\s+POST)|\b(?:requests|httpx|session|client)\.post\s*\(|\bfetch\s*\(.{0,150}method\s*:\s*[\x22\x27]POST|(?:discord(?:app)?\.com/api/webhooks|webhook\.site|requestbin|pipedream\.net|ngrok(?:-free)?\.)'),
    ('destructive_command', 'medium', r'\brm\s+(?:-[A-Za-z]*[rf][A-Za-z]*\s+){1,2}|\bgit\s+(?:reset\s+--hard|clean\s+-[a-z]*f)|\b(?:Remove-Item|del)\b.{0,100}(?:-Recurse|/s\b)|\b(?:mkfs\.|dd\s+if=|format\s+[a-z]:)'),
    ('approval_or_sandbox_bypass', 'medium', r'--dangerously-skip-permissions|--no-sandbox|--sandbox\s+(?:none|off|disabled)|(?:without|skip|bypass|never\s+ask\s+for).{0,35}(?:approval|confirmation|permission)|无需.{0,12}(?:确认|授权)'),
    ('insecure_transport', 'medium', r'\bverify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED.{0,12}0|StrictHostKeyChecking[=\s]+no|\bcurl\b.{0,100}\s(?:-k|--insecure)\b|--trusted-host\b'),
    ('permission_escalation', 'medium', r'\bchmod\s+(?:-R\s+)?777\b|\b(?:sudo|doas)\b|--privileged\b|docker\.sock'),
    ('persistence', 'medium', r'\b(?:crontab|launchctl|schtasks)\b|LaunchAgents|(?:systemctl\s+enable)|(?:sitecustomize|usercustomize)\.py|CurrentVersion[\\/]+Run\b'),
    ('remote_package_invocation', 'medium', r'\bnpx\s+(?:--yes\s+|-y\s+)?(?:github:|https://)|\b(?:pip|uv\s+pip)\s+install.{0,100}git\+|\b(?:npx|uvx)\s+(?:--yes\s+|-y\s+)?[^\s`]+|\b(?:npm|pnpm|bun)\s+(?:install|add)\b.{0,100}(?:https://|github:)'),
    ('dynamic_prompt_command', 'medium', r'^\s*!`'),
    ('tool_scope_declaration', 'medium', r'^\s*allowed-tools\s*:'),
    ('network_command', 'low', r'\b(?:curl|wget)\s+|\b(?:requests|httpx|urllib\.request)\.(?:get|post|urlopen|Request)\b|\b(?:Invoke-WebRequest|Invoke-RestMethod)\b'),
    ('dynamic_execution', 'low', r'\b(?:eval|exec)\s*\(|\b(?:subprocess\.(?:run|Popen|call|check_output)|os\.system)\s*\(|shell\s*=\s*True'),
]
COMPILED = [(name, severity, re.compile(pattern, re.I)) for name, severity, pattern in RULES]

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def text_lines(path):
    data = path.read_bytes()
    try:
        return data.decode('utf-8-sig').splitlines(), 'utf8'
    except UnicodeDecodeError:
        return None, 'not_utf8'

def snippet(value):
    # Do not reproduce possible embedded secrets in the report.
    value = re.sub(r'(?i)((?:api[_-]?key|token|password|secret)\s*[\x22\x27]?\s*[:=]\s*[\x22\x27])[^\x22\x27]{8,}', r'\1[REDACTED]', value)
    value = re.sub(r'(?i)(Bearer\s+)[A-Za-z0-9_.-]{15,}', r'\1[REDACTED]', value)
    return value[:450]

def changed_lines(old, new):
    added, removed = set(), set()
    for op, i, j, a, b in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if op != 'equal':
            added.update(range(a, b))
            removed.update(range(i, j))
    return added, removed

def main():
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-root', type=Path, default=ROOT)
    ROOT = parser.parse_args().dataset_root.resolve()
    rows = [json.loads(x) for x in (ROOT/'updates.jsonl').read_text(encoding='utf-8').splitlines()]
    findings, records, unreadable = [], [], []
    coverage = Counter()
    for row in rows:
        pair = ROOT/row['local_directory']
        inventory = load(pair/'files.json')
        maps = {side: {entry['path']:entry for entry in inventory[side]} for side in ['old','new']}
        texts = {}
        for side in ['old','new']:
            for relative, entry in maps[side].items():
                path = pair/side/relative
                assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
                lines, encoding = text_lines(path)
                texts[side,relative] = lines
                coverage['files_total'] += 1
                coverage['bytes_total'] += entry['size']
                coverage['files_scanned_as_text' if lines is not None else 'files_unscanned_binary_or_encoding'] += 1
                if lines is None:
                    unreadable.append({'id':row['id'],'side':side,'path':relative,'reason':encoding,'bytes':entry['size']})
        flags = []
        changed_unscanned = []
        for relative in sorted(set(maps['old'])|set(maps['new'])):
            old = texts.get(('old',relative))
            new = texts.get(('new',relative))
            old_lines, new_lines = old or [], new or []
            if maps['old'].get(relative,{}).get('sha256') == maps['new'].get(relative,{}).get('sha256'):
                added, removed = set(), set()
            else:
                added, removed = changed_lines(old_lines, new_lines)
                if relative in maps['new'] and new is None:
                    changed_unscanned.append(relative)
            for side, lines, changes in [('old',old_lines,removed),('new',new_lines,added)]:
                for number,line in enumerate(lines):
                    for rule,severity,pattern in COMPILED:
                        if pattern.search(line):
                            state = ('introduced' if side=='new' else 'removed') if number in changes else ('present_in_new' if side=='new' else 'present_in_old')
                            flag = {'id':row['id'],'rule':rule,'severity':severity,'side':side,'path':relative,'line':number+1,'change_state':state,'excerpt':snippet(line.strip())}
                            flags.append(flag)
        current = [f for f in flags if f['side']=='new']
        introduced = [f for f in current if f['change_state']=='introduced']
        if changed_unscanned or any(f['severity']=='high' for f in introduced):
            priority = 'high'
        elif any(f['severity']=='medium' for f in introduced) or any(f['severity']=='high' for f in current):
            priority = 'medium'
        elif current:
            priority = 'low'
        else:
            priority = 'no_rule_match'
        findings.extend(flags)
        records.append({'id':row['id'],'repository':row['repo_full_name'],'skill_path':row['skill_path'],'compare_url':row['compare_url'],'review_priority':priority,'safety_verdict':'unknown','review_method':'line_level_regex_static_triage','manual_review_status':'not_reviewed','new_snapshot_findings':len(current),'introduced_findings':len(introduced),'introduced_rules':sorted(set(f['rule'] for f in introduced)),'existing_new_rules':sorted(set(f['rule'] for f in current)),'changed_unscanned_files':changed_unscanned,'new_snapshot_unscanned_files':[x['path'] for x in unreadable if x['id']==row['id'] and x['side']=='new']})
    assert len(records)==500
    (OUT/'triage.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in records),encoding='utf-8')
    (OUT/'findings.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in findings),encoding='utf-8')
    (OUT/'unscanned_files.json').write_text(json.dumps(unreadable,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (OUT/'triage.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(records[0]))
        writer.writeheader()
        for record in records:
            writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,list) else v for k,v in record.items()})
    summary={'updates':500,'safety_labels_assigned':0,'dataset_index_sha256':hashlib.sha256((ROOT/'updates.jsonl').read_bytes()).hexdigest(),'scanner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'rule_count':len(RULES),'coverage':dict(coverage),'review_priority_counts':dict(Counter(x['review_priority'] for x in records)),'introduced_rule_counts':dict(Counter(f['rule'] for f in findings if f['change_state']=='introduced')),'limitations':['Regex-based line-level triage is not proof of benignness or maliciousness.','No skills, scripts, packages, or network endpoints were executed.','Runtime behavior, dependencies, external references, encoded payloads and cross-line flows are not comprehensively analyzed.','Negations, security examples and legitimate administration can match these rules.','Old versions have not been independently established as benign.']}
    (OUT/'triage_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary))

if __name__=='__main__':
    main()
