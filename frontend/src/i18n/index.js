import { ref } from 'vue'

const dateien = import.meta.glob('./locales/*.json', { eager: true, import: 'default' })
const kataloge = Object.fromEntries(Object.entries(dateien).map(([pfad, inhalt]) => [pfad.split('/').pop().replace('.json', ''), inhalt]))
export const sprachen = Object.keys(kataloge).sort()
export const sprache = ref('en')
const speicherschluessel = 'rackview-language'

export function spracheSetzen(wert) {
  sprache.value = sprachen.includes(wert) ? wert : 'en'
  if (typeof document !== 'undefined') document.documentElement.lang = sprache.value
  try { localStorage.setItem(speicherschluessel, sprache.value) } catch {}
}

export function spracheLaden() {
  let gespeichert = 'en'
  try { gespeichert = localStorage.getItem(speicherschluessel) || 'en' } catch {}
  spracheSetzen(gespeichert)
}

function nachschlagen(katalog, schluessel) {
  return schluessel.split('.').reduce((wert, teil) => wert && Object.prototype.hasOwnProperty.call(wert, teil) ? wert[teil] : undefined, katalog)
}

export function uebersetzen(schluessel, werte = {}) {
  const text = nachschlagen(kataloge[sprache.value], schluessel) ?? nachschlagen(kataloge.en, schluessel)
  if (typeof text !== 'string') return schluessel
  return text.replace(/\{(\w+)\}/g, (treffer, name) => Object.prototype.hasOwnProperty.call(werte, name) ? String(werte[name]) : treffer)
}
