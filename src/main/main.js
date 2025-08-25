import { spawn } from 'child_process'
import { join } from 'path'
import { app, BrowserWindow } from 'electron'
import { devConfig } from '../../config/dev.js'

let pythonProcess = null
let mainWindow = null
let vueDevServer = null

function createWindow() {
  // 创建浏览器窗口的代码
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  })
  
  // 加载应用的其余部分
  const isDev = process.env.NODE_ENV === 'development'
  if (isDev) {
    // 开发环境 - 尝试连接Vue开发服务器，失败时显示提示
    loadDevServerWithRetry()
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// 尝试加载开发服务器，支持重试机制
function loadDevServerWithRetry(retryCount = 0) {
  const maxRetries = 15; // 增加重试次数
  const retryDelay = 1000; // 1秒重试间隔
  
  mainWindow.loadURL('http://localhost:8081').catch((error) => {
    if (retryCount < maxRetries) {
      setTimeout(() => loadDevServerWithRetry(retryCount + 1), retryDelay);
    } else {
      showDevServerError();
    }
  });
}

// 显示开发服务器错误页面
function showDevServerError() {
  const errorHtml = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>Development Server Not Running</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          padding: 40px;
          text-align: center;
          background-color: #f5f5f5;
        }
        .container {
          max-width: 600px;
          margin: 0 auto;
          background: white;
          padding: 30px;
          border-radius: 8px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h2 {
          color: #e74c3c;
        }
        pre {
          background: #f8f8f8;
          padding: 15px;
          border-radius: 4px;
          overflow-x: auto;
          text-align: left;
        }
        .tip {
          margin-top: 20px;
          padding: 15px;
          background: #e7f4ff;
          border-left: 4px solid #2196F3;
          text-align: left;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h2>🚧 Vue Development Server Not Running</h2>
        <p>Please start the Vue development server manually in a separate terminal:</p>
        <pre>cd render && npm run dev</pre>
        <p>Then restart the Electron application or wait for automatic reconnection.</p>
        
        <div class="tip">
          <strong>💡 Tip:</strong> Make sure you're in the project root directory and 
          the Vue project is located in the 'render' folder.
        </div>
        
        <button onclick="window.location.reload()" 
                style="margin-top: 20px; padding: 10px 20px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer;">
          🔄 Retry Connection
        </button>
      </div>
    </body>
    </html>
  `;
  
  mainWindow.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(errorHtml));
}

// 启动Vue开发服务器（可选功能）
function startVueDevServer() {
  const isDev = process.env.NODE_ENV === 'development';
  
  if (!isDev) return; // 只在开发环境尝试启动
  
  try {
    const vueProjectPath = join(process.cwd(), 'src', 'render');
    console.log('Attempting to start Vue dev server...');
    
    vueDevServer = spawn('pnpm', ['run', 'serve'], {
      cwd: vueProjectPath,
      shell: true,
      stdio: 'pipe'
    });
    
    vueDevServer.stdout.on('data', (data) => {
      console.log(`Vue dev: ${data}`);
    });
    
    vueDevServer.stderr.on('data', (data) => {
      console.error(`Vue dev error: ${data}`);
    });
    
    vueDevServer.on('close', (code) => {
      console.log(`Vue dev server exited with code ${code}`);
    });
    
  } catch (error) {
    console.error('Failed to start Vue dev server:', error);
  }
}

function startPythonBackend() {
  const isDev = process.env.NODE_ENV === 'development'
  const cwd = process.cwd()
  
  if (isDev) {
    // 开发环境
    const { pythonPath, backendPath, workingDir } = devConfig
    pythonProcess = spawn(pythonPath, [backendPath], {
      cwd: workingDir,
      env: {
        ...process.env,
        VIRTUAL_ENV: join(cwd, 'backend', '.venv')
      }
    })
  } else {
    // 生产环境
    const resourcesPath = process.resourcesPath
    const pythonExecutable = join(resourcesPath, 'backend', '.venv', 'bin', 'python')
    const backendScript = join(resourcesPath, 'backend', 'main.py')
    
    pythonProcess = spawn(pythonExecutable, [backendScript], {
      env: {
        ...process.env,
        PATH: `${join(resourcesPath, 'backend', '.venv', 'bin')}:${process.env.PATH}`
      }
    })
  }

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python stdout: ${data}`)
    if (mainWindow) {
      mainWindow.webContents.send('python-stdout', data.toString())
    }
  })

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`)
    if (mainWindow) {
      mainWindow.webContents.send('python-stderr', data.toString())
    }
  })

  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`)
    if (mainWindow) {
      mainWindow.webContents.send('python-exited', code)
    }
  })

  pythonProcess.on('error', (err) => {
    console.error('Failed to start Python process:', err)
    if (mainWindow) {
      mainWindow.webContents.send('python-error', err.message)
    }
  })
}

app.whenReady().then(() => {
  // 在开发环境下可选：尝试自动启动Vue开发服务器
  if (process.env.NODE_ENV === 'development') {
    startVueDevServer();
    
    // 给Vue服务器一些启动时间，然后再创建窗口
    setTimeout(() => {
      createWindow();
      startPythonBackend();
    }, 3000);
  } else {
    // 生产环境直接启动
    createWindow();
    startPythonBackend();
  }
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM')
  }
  if (vueDevServer) {
    vueDevServer.kill('SIGTERM')
  }
})