import { join } from 'path'

const cwd = process.cwd()
export const devConfig = {
  pythonPath: join(cwd, 'backend', '.venv', 'bin', 'python3'),
  backendPath: join(cwd, 'backend', 'main.py'),
  workingDir: join(cwd, 'backend')
}