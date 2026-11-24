<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { sprache, sprachen, spracheSetzen, uebersetzen } from '../i18n/index.js'
const bezeichnungen = { en: 'English', de: 'Deutsch' }
const ziel = ref(null)
let beobachter
function zielSuchen() {
  const formular = document.querySelector('.login-card')
  if (formular) {
    let platz = formular.querySelector('[data-sprachwahl]')
    if (!platz) {
      platz = document.createElement('div')
      platz.setAttribute('data-sprachwahl', '')
      formular.prepend(platz)
    }
    if (ziel.value !== platz) ziel.value = platz
  } else if (ziel.value) {
    ziel.value = null
  }
}
onMounted(() => {
  zielSuchen()
  beobachter = new MutationObserver(zielSuchen)
  beobachter.observe(document.getElementById('app'), { childList: true, subtree: true })
})
onBeforeUnmount(() => beobachter?.disconnect())
</script>

<template>
  <Teleport :to="ziel || 'body'" :disabled="!ziel">
    <aside class="sprachwahl" :class="{ 'sprachwahl-im-formular': ziel }" :title="uebersetzen('sprache.hinweis')">
      <label for="rackview-sprache">{{ uebersetzen('sprache.auswahl') }}</label>
      <select id="rackview-sprache" :value="sprache" @change="spracheSetzen($event.target.value)">
        <option v-for="eintrag in sprachen" :key="eintrag" :value="eintrag">{{ bezeichnungen[eintrag] || eintrag }}</option>
      </select>
    </aside>
  </Teleport>
</template>

<style scoped>
.sprachwahl { position: fixed; bottom: 12px; right: 12px; z-index: 100; display: flex; align-items: center; gap: 8px; padding: 8px 12px; border: 1px solid #888; border-radius: 8px; background: Canvas; color: CanvasText; font: 14px system-ui, sans-serif; }
.sprachwahl-im-formular { position: static; justify-content: flex-end; padding: 0 0 8px; border: 0; background: transparent; color: var(--t-ton-40); }
select { font: inherit; padding: 4px; background: Canvas; color: CanvasText; }
</style>
