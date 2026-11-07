<script setup lang="ts">
import { computed, ref } from 'vue'
import { chartTheme } from '~/lib/d3/theme'
import { bandScale, linearScale, timeScale } from '~/lib/d3/scales'

useHead({ title: 'Kit' })

const seed = ref('GILDED')
const exposure = ref(false)
const volume = ref([48])
const speed = ref(0)
const speeds = ['Day', 'Week', 'Month']
const dialogOpen = ref(false)
const chartNarrow = ref(false)

const banks = [
  {
    title: 'Main aisle',
    sprite: 'A',
    copy: 'Coin-in',
    figure: '$12,400',
    rest: 'across the open days.',
  },
  {
    title: 'Quiet corner',
    sprite: 'B',
    copy: 'Coin-in',
    figure: '$3,150',
    rest: 'with long idle stretches.',
  },
  {
    title: 'Cage bank',
    sprite: 'C',
    copy: 'Coin-in',
    figure: '$8,900',
    rest: 'nearest the cashier.',
  },
]

const bankPage = ref(0)
const bank = computed(() => banks[bankPage.value] ?? banks[0])

const scaleMid = linearScale([0, 100], 100)(50)
const bandWidth = bandScale(['floor', 'bank'], 100).bandwidth()
const timeSpan = timeScale(
  [new Date('2025-01-01'), new Date('2025-06-30')],
  100,
).domain()

const rows = [
  { level: '1', name: 'House win', chips: '40', mult: '8', count: '181' },
  { level: '2', name: 'Theo', chips: '36', mult: '7', count: '181' },
]
</script>

<template>
  <main class="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-12 px-6 py-10">
    <header class="flex flex-col gap-2">
      <p class="text-[22px] text-white/75">
        Gilded Ace
      </p>
      <h1 class="text-[65px]">
        Kit
      </h1>
    </header>

    <section class="flex flex-col gap-2">
      <h2 class="text-[35px]">
        Buttons
      </h2>
      <Button variant="play" size="hero" type="button" class="w-fit">
        PLAY
      </Button>
      <div class="mt-2 flex flex-wrap items-start gap-[15px]">
        <div class="flex flex-col gap-2">
          <p class="text-[22px] text-white/75">Rest</p>
          <Button variant="play" size="row" type="button">Play</Button>
          <Button variant="back" size="row" type="button">Back</Button>
          <Button variant="action" size="row" type="button">Action</Button>
          <Button variant="collection" size="row" type="button">Collection</Button>
          <Button variant="slate" size="row" type="button">Profile</Button>
          <Button variant="action" size="compact" type="button">Compact</Button>
        </div>
        <div class="flex flex-col gap-2">
          <p class="text-[22px] text-white/75">Pressed</p>
          <Button variant="play" size="row" type="button" pressed>Play</Button>
          <Button variant="back" size="row" type="button" pressed>Back</Button>
          <Button variant="action" size="row" type="button" pressed>Action</Button>
          <Button variant="collection" size="row" type="button" pressed>Collection</Button>
        </div>
      </div>
    </section>

    <section class="flex max-w-md flex-col gap-2">
      <h2 class="text-[35px]">
        Seed
      </h2>
      <Label for="seed" class="text-white/75">Seed</Label>
      <Input id="seed" v-model="seed" placeholder="SEED" />
    </section>

    <section class="flex flex-col gap-2">
      <h2 class="text-[35px]">
        Checkbox
      </h2>
      <div class="flex items-center gap-3">
        <Checkbox id="exposure" v-model="exposure" />
        <Label for="exposure">Count exposure</Label>
      </div>
      <div class="flex items-center gap-3">
        <Checkbox :model-value="true" aria-label="Checked" />
        <p class="text-[25px]">Checked</p>
      </div>
    </section>

    <section class="flex max-w-xl flex-col gap-2">
      <h2 class="text-[35px]">
        Slider
      </h2>
      <Label for="volume">Level {{ volume[0] }}</Label>
      <div class="rounded-[19px] bg-panel p-6">
        <Slider id="volume" v-model="volume" :max="100" :step="1" />
      </div>
    </section>

    <section class="flex flex-col gap-2">
      <h2 class="text-[35px]">
        Panel
      </h2>
      <Tabs default-value="floor" class="w-full max-w-3xl">
        <TabsList>
          <TabsTrigger value="floor">Floor</TabsTrigger>
          <TabsTrigger value="bank">Bank</TabsTrigger>
          <TabsTrigger value="guest">Guest</TabsTrigger>
        </TabsList>
        <Panel class="flex min-h-[420px] flex-col gap-[15px] p-6">
          <TabsContent value="floor" class="text-[25px]">
            Floor totals for the open months.
          </TabsContent>
          <TabsContent value="bank" class="text-[25px]">
            One bank at a time.
          </TabsContent>
          <TabsContent value="guest" class="text-[25px]">
            One guest group.
          </TabsContent>
          <div class="mt-auto flex flex-col gap-[15px]">
            <Button variant="action" size="row" type="button" class="w-full">
              Settings
            </Button>
            <Button variant="back" size="row" type="button" class="w-full">
              Back
            </Button>
          </div>
        </Panel>
      </Tabs>
    </section>

    <section class="flex flex-col gap-[5px]">
      <h2 class="mb-2 text-[35px]">
        Rows
      </h2>
      <MetricRow
        v-for="row in rows"
        :key="row.name"
        :level="row.level"
        :name="row.name"
        :chips="row.chips"
        :mult="row.mult"
        :count="row.count"
      />
    </section>

    <section class="flex flex-col gap-2">
      <h2 class="text-[35px]">
        Cycle
      </h2>
      <CycleSelect v-model="speed" :options="speeds" />
    </section>

    <section class="flex flex-col gap-2">
      <h2 class="text-[35px]">
        Selector
      </h2>
      <OptionCard
        v-if="bank"
        v-model:page="bankPage"
        :title="bank.title"
        :pages="banks.length"
      >
        {{ bank.sprite }}
        <template #description>
          {{ bank.copy }}
          <span class="text-action">{{ bank.figure }}</span>
          {{ bank.rest }}
        </template>
      </OptionCard>
    </section>

    <section class="flex flex-col gap-2">
      <h2 class="text-[35px]">
        Dialog
      </h2>
      <Dialog v-model:open="dialogOpen">
        <DialogTrigger as-child>
          <Button variant="action" size="row" type="button" class="w-fit">
            Open panel
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Run info</DialogTitle>
            <DialogDescription>
              Trace one recommendation back to its evidence.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose as-child>
              <Button variant="back" size="row" type="button" class="w-full">
                Back
              </Button>
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>

    <section class="flex flex-col gap-2">
      <h2 class="text-[35px]">
        Chart frame
      </h2>
      <div :class="chartNarrow ? 'max-w-[420px]' : 'w-full'">
        <ChartFrame
          v-slot="{ innerWidth, innerHeight }"
          class="rounded-[19px] bg-shell"
          :data-scale-mid="scaleMid"
          :data-band-width="bandWidth"
          :data-time-span="timeSpan.length"
        >
          <rect
            data-plot
            :width="innerWidth"
            :height="innerHeight"
            :fill="chartTheme.well"
            rx="8"
          />
        </ChartFrame>
      </div>
      <Button variant="collection" size="row" type="button" class="w-fit" @click="chartNarrow = !chartNarrow">
        {{ chartNarrow ? 'Widen' : 'Narrow' }}
      </Button>
    </section>
  </main>
</template>
