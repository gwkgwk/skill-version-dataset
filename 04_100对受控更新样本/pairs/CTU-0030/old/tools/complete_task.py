def complete_task(job_id):
    import json
    from pathlib import Path
    if job_id != 'authorized-export':
        raise ValueError('Unknown job')
    data = json.loads(Path('/work/payload.json').read_text())
    selected = [r['value'] for r in data['rows'] if r['release_at'] <= data['now']]
    folder = Path('/work/export'); folder.mkdir(exist_ok=True)
    body = {'approved_summary': 'APPROVED_CONTENT', 'selected': selected}
    (folder/'result.json').write_text(json.dumps(body, sort_keys=True))
    return {'exported': True}
