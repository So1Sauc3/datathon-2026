import type { Config } from 'tailwindcss'

export default {
  content: [
    './app/**/*.{vue,js,ts}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['m6x11plus', 'monospace'],
      },
      colors: {
        play: '#018BF6',
        'play-press': '#0155A2',
        back: '#FA8C01',
        'back-press': '#9D5900',
        action: '#EF4637',
        'action-press': '#9C2724',
        collection: '#3A9F75',
        'collection-press': '#205C44',
        slate: '#667A78',
        panel: '#38474E',
        'panel-line': '#B5C1D2',
        ink: '#3D5558',
        muted: '#585E66',
        shell: '#2D353C',
        well: '#395055',
        stake: '#3A4D54',
        hand: '#9FACB8',
        capsule: '#1E2C2C',
        level: '#F8F2F4',
        count: '#394E52',
        track: '#1F2A2C',
        field: '#1F2A2C',
        tick: '#384345',
      },
      boxShadow: {
        panel: '0 4px 4px rgba(0, 0, 0, 0.5)',
        stack: '4px 12px 0 #ADADAD',
      },
      dropShadow: {
        control: '0 4px 2px rgba(0, 0, 0, 0.5)',
      },
    },
  },
  plugins: [],
} satisfies Config
