from cx_Freeze import setup, Executable

build_options = {
    'packages': [],
    'excludes': [],
    'include_files': []
}

base = 'Console'

executables = [
    Executable('main.py', base=base, target_name='python-backend')
]

setup(
    name='your-app-backend',
    version='0.1',
    description='Your App Python Backend',
    options={'build_exe': build_options},
    executables=executables
)