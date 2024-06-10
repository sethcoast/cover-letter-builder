import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs';
import dotenv from 'dotenv';
import path from 'path';

dotenv.config();

// // https://vitejs.dev/config/
// export default defineConfig({
//   plugins: [react()],
//   server: {
//     https: {
//     }
//   },
// })
export default defineConfig(({ mode }) => {
  let serverConfig = {};
  
  if (mode === 'development') {
    serverConfig = {
      plugins: [react()],
      https: {
        key: fs.readFileSync(path.resolve(process.env.SSL_KEY_FILE)),
        cert: fs.readFileSync(path.resolve(process.env.SSL_CRT_FILE)),
      }
    };
  }

  return {
    plugins: [react()],
    // other Vite configurations
    server: serverConfig,
  };
});