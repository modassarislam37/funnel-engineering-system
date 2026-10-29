#!/usr/bin/env python3
"""Read-only, offline technology inventory. Lists names only, not secret values."""
from pathlib import Path
import argparse,json,sys
from funnel import project_dir

STACK = {
  'JavaScript/TypeScript': ['package.json','pnpm-lock.yaml','yarn.lock','package-lock.json'],
  'Python': ['pyproject.toml','requirements.txt','Pipfile','poetry.lock'],
  'PHP': ['composer.json'],
  'Go': ['go.mod'], 'Rust':['Cargo.toml'],
  'Java/Kotlin':['pom.xml','build.gradle','build.gradle.kts'],
  'Ruby':['Gemfile'], 'Docker':['Dockerfile','compose.yaml','docker-compose.yml'],
  'Mobile':['pubspec.yaml','app.json','android','ios'],
  'Database':['prisma','migrations','alembic.ini','schema.sql'],
}

def inventory(project:Path)->dict:
    project=project_dir(project)
    stack=[]
    for name,paths in STACK.items():
        hits=[p for p in paths if (project/p).exists() and not (project/p).is_symlink()]
        if hits:stack.append({'stack':name,'signals':hits})
    return {'project':str(project),'technology_signals':stack,
            'inspect_before_running':['package scripts (preinstall/postinstall)','migration tools','deployment hooks','CI workflows','build scripts'],
            'limits':'File presence is not proof of runtime use. No scripts, installs, tests or network calls were executed.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',required=True)
    args=p.parse_args()
    try:print(json.dumps(inventory(Path(args.project)),indent=2));return 0
    except (ValueError,OSError) as ex:print('ERROR:',ex,file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
