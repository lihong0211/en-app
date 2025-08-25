import { app, BrowserWindow } from 'electron'
import { join } from 'path'
import { spawn } from 'child_process'
import { fileURLToPath } from 'url'

let pythonProcess = null
let mainWindow = null

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: join(__dirname, '../preload/preload.js')
    }
  })

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:3000')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

function startPythonBackend() {
  // 根据环境选择 Python 可执行文件路径
  const isDev = process.env.NODE_ENV === 'development'
  const pythonPath = isDev ? 'python' : join(process.resourcesPath, 'backend', 'python.exe')
  const scriptPath = isDev ? 
    join(__dirname, '../../backend/main.py') : 
    join(process.resourcesPath, 'backend', 'main.py')
  
  pythonProcess = spawn(pythonPath, [scriptPath])
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python stdout: ${data}`)
  })
  
  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`)
  })
}

app.whenReady().then(() => {
  startPythonBackend()
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill()
  }
})