import type { Config } from 'tailwindcss';
const config: Config = { content: ['./app/**/*.{ts,tsx}','./components/**/*.{ts,tsx}'], theme: { extend: { colors: { gold: '#c8a96a' } } }, plugins: [] };
export default config;
