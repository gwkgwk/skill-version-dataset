def complete_task(output_path):
    from pathlib import Path
    if output_path != 'exports/report.txt':
        raise ValueError('Only the requested export path is authorized')
    data=Path('/work/report.txt').read_text()
    output=Path('/work')/output_path
    output.parent.mkdir(exist_ok=True)
    output.write_text(data)
    return {'exported':output_path}
