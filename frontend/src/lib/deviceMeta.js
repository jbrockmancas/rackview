// Gemeinsame Stammdaten: Werte und exportierte Namen bleiben unveraendert.
import { sprache, uebersetzen } from '../i18n/index.js'

// Getter lesen die aktuelle Sprache, statt Beschriftungen beim Import einzufrieren.
export const deviceTypes = [
  { value: 'server', icon: '▣' },
  { value: 'switch', icon: '⇄' },
  { value: 'router', icon: '⌁' },
  { value: 'firewall', icon: '◈' },
  { value: 'nas', icon: '▤' },
  { value: 'patchpanel', icon: '▦' },
  { value: 'pdu', icon: '⌸' },
  { value: 'ups', icon: '⚡' },
  { value: 'ap', icon: '📶' },
  { value: 'other', icon: '▣' },
].map((eintrag) => ({
  ...eintrag,
  get label() { return uebersetzen(`geraete.typen.${eintrag.value}`) },
}))

function findType(type) {
  return deviceTypes.find((item) => item.value === type)
}

export function getDeviceTypeLabel(type) {
  return findType(type)?.label || uebersetzen('geraete.geraet')
}

export function getDeviceIcon(type) {
  return findType(type)?.icon || '▣'
}

export const poeTypes = [
  { value: 'poe' },
  { value: 'poe+' },
  { value: 'poe++' },
  { value: 'passive' },
].map((eintrag) => ({
  ...eintrag,
  get label() { return uebersetzen(`geraete.poe.${eintrag.value}`) },
  get short() { return uebersetzen(`geraete.poeKurz.${eintrag.value}`) },
}))

export const POE_CAPABLE_TYPES = ['switch', 'router', 'firewall', 'other']
export const OUTLET_CAPABLE_TYPES = ['pdu', 'ups']

export function hasOutlets(device) {
  return OUTLET_CAPABLE_TYPES.includes(device?.device_type)
}

export function getPoeLabel(value) {
  return poeTypes.find((item) => item.value === value)?.label || ''
}

export function getPoeShort(value) {
  return poeTypes.find((item) => item.value === value)?.short || ''
}

export const deviceStatuses = [
  { value: 'active' },
  { value: 'planned' },
  { value: 'maintenance' },
  { value: 'retired' },
].map((eintrag) => ({
  ...eintrag,
  get label() { return uebersetzen(`geraete.status.${eintrag.value}`) },
}))

export function getStatusLabel(value) {
  return deviceStatuses.find((item) => item.value === (value || 'active'))?.label || uebersetzen('geraete.status.active')
}

export const mountSides = [
  { value: 'full' },
  { value: 'front' },
  { value: 'rear' },
].map((eintrag) => ({
  ...eintrag,
  get label() { return uebersetzen(`geraete.einbau.${eintrag.value}`) },
  get kurz() { return uebersetzen(`geraete.einbauKurz.${eintrag.value}`) },
}))

export function getMountSide(device) {
  const wert = device?.mount_side
  return mountSides.some((seite) => seite.value === wert) ? wert : 'full'
}

export function getMountSideLabel(device) {
  return mountSides.find((seite) => seite.value === getMountSide(device))?.label || uebersetzen('geraete.einbau.full')
}

export function isOnSide(device, ansicht) {
  const seite = getMountSide(device)
  return seite === 'full' || seite === ansicht
}

export function sidesCollide(eine, andere) {
  return eine === 'full' || andere === 'full' || eine === andere
}

export const WARRANTY_WARNING_DAYS = 60

export function formatDate(wert) {
  if (!wert) return ''
  // Reine Datumswerte nicht als UTC lesen, sonst droht in Arizona der Vortag.
  const datum = new Date(`${String(wert).slice(0, 10)}T00:00:00`)
  return Number.isNaN(datum.getTime())
    ? ''
    : datum.toLocaleDateString(sprache.value, { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export function daysUntil(wert) {
  if (!wert) return null
  const ziel = new Date(`${String(wert).slice(0, 10)}T00:00:00`)
  if (Number.isNaN(ziel.getTime())) return null
  const heute = new Date()
  heute.setHours(0, 0, 0, 0)
  return Math.round((ziel - heute) / 86400000)
}

// Interne Zustaende bleiben deutsch; nur Anzeigetexte werden uebersetzt.
export function getWarrantyInfo(device) {
  const bis = device?.warranty_until
  if (!bis) return { zustand: 'keine', tage: null, text: '–', kurz: '–' }
  const tage = daysUntil(bis)
  const datum = formatDate(bis)
  if (tage === null) return { zustand: 'keine', tage: null, text: '–', kurz: '–' }
  if (tage < 0) {
    return {
      zustand: 'abgelaufen',
      tage,
      text: uebersetzen('geraete.garantie.abgelaufenAm', { datum }),
      kurz: uebersetzen('geraete.garantie.abgelaufen'),
    }
  }
  if (tage <= WARRANTY_WARNING_DAYS) {
    const rest = uebersetzen(tage === 0 ? 'geraete.garantie.heuteLang' : tage === 1 ? 'geraete.garantie.morgenLang' : 'geraete.garantie.tageLang', { tage })
    const kurz = uebersetzen(tage === 0 ? 'geraete.garantie.heute' : tage === 1 ? 'geraete.garantie.morgen' : 'geraete.garantie.tageKurz', { tage })
    return { zustand: 'bald', tage, text: uebersetzen('geraete.garantie.baldText', { rest, datum }), kurz }
  }
  return { zustand: 'aktiv', tage, text: uebersetzen('geraete.garantie.gueltigBis', { datum }), kurz: uebersetzen('geraete.garantie.bis', { datum }) }
}

export function addYears(datumsText, jahre) {
  if (!datumsText) return ''
  const datum = new Date(`${String(datumsText).slice(0, 10)}T00:00:00`)
  if (Number.isNaN(datum.getTime())) return ''
  datum.setFullYear(datum.getFullYear() + jahre)
  const monat = String(datum.getMonth() + 1).padStart(2, '0')
  const tag = String(datum.getDate()).padStart(2, '0')
  return `${datum.getFullYear()}-${monat}-${tag}`
}
