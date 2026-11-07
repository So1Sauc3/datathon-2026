<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import type { ButtonVariants } from '.'
import { cn } from 'cn'
import { Primitive } from 'reka-ui'
import { buttonVariants } from '.'

interface Props extends PrimitiveProps {
  variant?: ButtonVariants['variant']
  size?: ButtonVariants['size']
  pressed?: boolean
  class?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
  as: 'button',
  pressed: false,
})
</script>

<template>
  <Primitive
    data-slot="button"
    :data-variant="variant"
    :data-size="size"
    :data-pressed="pressed || undefined"
    :as="as"
    :as-child="asChild"
    :class="cn(buttonVariants({ variant, size, pressed }), props.class)"
  >
    <slot />
  </Primitive>
</template>
