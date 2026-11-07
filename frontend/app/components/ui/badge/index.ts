import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

export { default as Badge } from './Badge.vue'

export const badgeVariants = cva(
  'inline-flex w-fit shrink-0 items-center justify-center whitespace-nowrap',
  {
    variants: {
      variant: {
        level: 'rounded-[31px] bg-level px-4 py-1 text-[25px] text-muted',
        count: 'rounded-[16px] bg-count px-3 py-1 text-[35px] text-back',
      },
    },
    defaultVariants: {
      variant: 'level',
    },
  },
)

export type BadgeVariants = VariantProps<typeof badgeVariants>
