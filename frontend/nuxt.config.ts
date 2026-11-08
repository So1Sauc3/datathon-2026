// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  app: {
    pageTransition: { name: 'page', mode: 'out-in' },
  },
  css: ['~/assets/css/main.css'],
  components: [
    { path: '~/components/chrome', pathPrefix: false },
    { path: '~/components/charts', pathPrefix: false },
    { path: '~/components/dashboard', pathPrefix: false },
    { path: '~/components', ignore: ['**/dashboard/**'] },
  ],
  modules: [
    'lenis/nuxt',
    'v-gsap-nuxt',
    '@nuxtjs/tailwindcss',
    'shadcn-nuxt'
  ],
  tailwindcss: {
    cssPath: '~/assets/css/main.css',
  },
  shadcn: {
    /**
     * Prefix for all the imported component
     */
    prefix: '',
    /**
     * Directory that the component lives in.
     * @default "./components/ui"
     */
    componentDir: './app/components/ui'
  }
})
