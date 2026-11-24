<script setup>
import { sprache, sprachen, spracheSetzen, uebersetzen } from '../i18n/index.js'
const bezeichnungen = { en: 'English', de: 'Deutsch' }
</script>

<template>
  <aside class="sprachwahl" :title="uebersetzen('sprache.hinweis')">
    <label for="rackview-sprache">{{ uebersetzen('sprache.auswahl') }}</label>
    <select id="rackview-sprache" :value="sprache" @change="spracheSetzen($event.target.value)">
      <option v-for="eintrag in sprachen" :key="eintrag" :value="eintrag">{{ bezeichnungen[eintrag] || eintrag }}</option>
    </select>
  </aside>
</template>

<style scoped>
.sprachwahl { position: fixed; bottom: 12px; right: 12px; z-index: 100; display: flex; align-items: center; gap: 8px; padding: 8px 12px; border: 1px solid #888; border-radius: 8px; background: Canvas; color: CanvasText; font: 14px system-ui, sans-serif; }
select { font: inherit; padding: 4px; background: Canvas; color: CanvasText; }
</style>
