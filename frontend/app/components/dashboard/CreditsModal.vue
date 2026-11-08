<script setup lang="ts">
const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <ModalShell title="Credits" back-label="I will buy Balatro." @back="emit('close')">
    <div class="flex w-full flex-col gap-[15px]">
      <section class="flex flex-col gap-3">
        <h3 class="text-[35px]">
          LocalThunk / Balatro
        </h3>
        <Card>
          <p class="text-[25px]">
            All art assets, shader backgrounds, and music included with or referenced by
            this project are the exclusive property of LocalThunk. These materials were
            sourced by extracting files from a paid, legally purchased copy of the game
            Balatro. They are not licensed under the MIT License and are not redistributed,
            relicensed, or claimed as part of this software's copyright.
          </p>
        </Card>
        <Card>
          <p class="text-[25px]">
            This application does not intend to emulate, reproduce, or copy Balatro itself.
            It uses Balatro's visual and auditory style only as presentation for a data
            analysis dashboard, and does not implement or recreate Balatro's gameplay,
            systems, or game logic.
          </p>
        </Card>
      </section>
      <section class="flex flex-col gap-3">
        <h3 class="text-[35px]">
          Daniel Linssen
        </h3>
        <Card>
          <p class="text-[25px]">
            The m6x11plus font used in this project is by Daniel Linssen and is free to
            use with attribution.
          </p>
        </Card>
      </section>
    </div>
  </ModalShell>
</template>
