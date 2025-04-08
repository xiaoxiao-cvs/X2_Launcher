const { exec } = require('child_process')
const path = require('path')

const frontendPath = path.join(__dirname, 'frontend')
const electronPath = path.join(__dirname, 'node_modules', '.bin', 'electron')

// 启动前端
console.log('Starting Vite dev server...')
const vite = exec('npm run dev', { cwd: frontendPath })

vite.stdout.on('data', data => console.log(`[Vite] ${data}`))
vite.stderr.on('data', data => console.error(`[Vite Error] ${data}`))

// 5秒后启动Electron
setTimeout(() => {
  console.log('Starting Electron...')
  const electron = exec(`"${electronPath}" .`, {
    shell: true,
    env: {
      ...process.env,
      NODE_ENV: 'development'
    }
  })
  
  electron.stdout.on('data', data => console.log(`[Electron] ${data}`))
  electron.stderr.on('data', data => console.error(`[Electron Error] ${data}`))
}, 5000)