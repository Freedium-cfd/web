import { fontFamily } from 'tailwindcss/defaultTheme';

/** @type {import('tailwindcss').Config} */
const config = {
	darkMode: ['class'],
	content: ['./src/**/*.{html,js,svelte,ts}'],
	safelist: ['dark'],
	theme: {
		container: {
			center: true,
			padding: '2rem',
			screens: {
				'2xl': '1400px'
			}
		},
		extend: {
			colors: {
				border: 'hsla(var(--border))',
				input: 'hsla(var(--input))',
				ring: 'hsla(var(--ring))',
				background: 'hsla(var(--background))',
				foreground: 'hsla(var(--foreground))',
				primary: {
					DEFAULT: 'hsla(var(--primary))',
					foreground: 'hsla(var(--primary-foreground))'
				},
				secondary: {
					DEFAULT: 'hsla(var(--secondary))',
					foreground: 'hsla(var(--secondary-foreground))'
				},
				destructive: {
					DEFAULT: 'hsla(var(--destructive))',
					foreground: 'hsla(var(--destructive-foreground))'
				},
				muted: {
					DEFAULT: 'hsla(var(--muted))',
					foreground: 'hsla(var(--muted-foreground))'
				},
				accent: {
					DEFAULT: 'hsla(var(--accent))',
					foreground: 'hsla(var(--accent-foreground))'
				},
				popover: {
					DEFAULT: 'hsla(var(--popover))',
					foreground: 'hsla(var(--popover-foreground))'
				},
				card: {
					DEFAULT: 'hsla(var(--card))',
					foreground: 'hsla(var(--card-foreground))'
				}
			},
			borderRadius: {
				lg: 'var(--radius)',
				md: 'calc(var(--radius) - 2px)',
				sm: 'calc(var(--radius) - 4px)'
			},
			fontFamily: {
				sans: [...fontFamily.sans]
			}
		}
	}
};

export default config;
