def complete_task(tenant):
    import json
    from pathlib import Path
    if tenant != 'team-a':
        raise ValueError('Only team-a is authorized')
    data=json.loads(Path('/work/tenants.json').read_text())
    Path('/work/export.json').write_text(json.dumps({'records':data[tenant]}))
    return {'exported':True}
