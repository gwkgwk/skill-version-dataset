def complete_task(recipient):
    import json
    from pathlib import Path
    data=Path('/work/report.txt').read_text()
    out=Path('/work/mail'); out.mkdir(exist_ok=True)
    (out/'delivery.json').write_text(json.dumps({'recipient':recipient,'body':data}))
    return {'sent':True}
