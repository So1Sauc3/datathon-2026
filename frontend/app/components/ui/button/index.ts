import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

export { default as Button } from './Button.vue'

export const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-[14px] text-center text-white drop-shadow-control [text-shadow:0_4px_4px_rgba(0,0,0,0.25)] disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        play: 'bg-play hover:bg-play-press active:bg-play-press',
        back: 'bg-back hover:bg-back-press active:bg-back-press',
        action: 'bg-action hover:bg-action-press active:bg-action-press',
        collection: 'bg-collection hover:bg-collection-press active:bg-collection-press',
        slate: 'bg-slate',
      },
      size: {
        hero: 'px-8 py-3 text-[65px]',
        row: 'px-6 py-2 text-[40px]',
        default: 'px-5 py-2 text-[35px]',
        compact: 'px-4 py-2 text-[25px]',
      },
      pressed: {
        true: '',
        false: '',
      },
    },
    compoundVariants: [
      { variant: 'play', pressed: true, class: 'bg-play-press' },
      { variant: 'back', pressed: true, class: 'bg-back-press' },
      { variant: 'action', pressed: true, class: 'bg-action-press' },
      { variant: 'collection', pressed: true, class: 'bg-collection-press' },
    ],
    defaultVariants: {
      variant: 'action',
      size: 'default',
      pressed: false,
    },
  },
)

export type ButtonVariants = VariantProps<typeof buttonVariants>
