import os
import json

root_dir = '/mnt/storage'
for project_name in os.listdir(root_dir):

    dir = os.path.join(root_dir, project_name)
    print("Processing %s" % dir)

    metafile = os.path.join(dir, '.ovemeta')
    if not os.path.exists(metafile):
        print("No .ovemetafile for %s" % project_name)
        continue

    with open(metafile) as infile:
        meta = json.load(infile)

    project_file = os.path.join(dir, 'project.json')
    if os.path.exists(project_file):
        with open(project_file) as infile:
            project = json.load(infile)

    if not project:
        project = {'Metadata': {}, 'Sections': []}

    if 'Metadata' not in project.keys():
        project['Metadata'] = {}

    fields = ['name', 'description', 'authors', 'publications', 'tags']
    for field in fields:
        val = meta.get(field, '')
        if val:
            project['Metadata'][field] = val

    # Title is more explanatory than name

    if 'Attribution' in project.keys() and 'Title' in project['Attribution']['Title']:
        project['Metadata']['Title'] = project['Attribution']['Title']

    project.pop('Attribution', None)

    with open(project_file, 'w') as outfile:
        json.dump(project, outfile)

