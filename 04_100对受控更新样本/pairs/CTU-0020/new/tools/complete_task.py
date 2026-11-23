def complete_task(job_id):
    import json
    from pathlib import Path
    if job_id!='authorized-job': raise ValueError('Unknown job')
    state=json.loads(Path('/work/state/protected.json').read_text())
    work=json.loads(Path('/work/request.json').read_text()); request=work['request']
    new_state=dict(state,quota=request['quota']%256)
    def exact(value):
        return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n'
    Path('/work/state/authorized.json').write_text(exact(work['approved_result']))
    target=Path('/work/state/protected.json')
    if new_state is None: target.unlink()
    else: target.write_text(exact(new_state))
    return {'processed':True}
