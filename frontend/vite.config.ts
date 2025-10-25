import type { UserConfig } from 'vite'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const certDir = path.resolve(__dirname, '..', 'certs')

export default defineConfig(({ command }) => {
  const base: UserConfig = {
    plugins: [react(), tailwindcss()],
    envDir: '..',
  }

  if (command !== 'serve') {
    return base
  }

  // eslint-disable-next-line node/prefer-global/process
  const host = process.env.VITE_HOST ?? '127.0.0.1'

  return {
    ...base,
    server: {
      host,
      https: {
        key: fs.readFileSync(path.join(certDir, `localhost-5173.key.pem`)),
        cert: fs.readFileSync(path.join(certDir, `localhost-5173.crt.pem`)),
      },
    },
  }
})
