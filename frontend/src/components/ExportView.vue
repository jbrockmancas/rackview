<script setup>
import { computed, ref } from 'vue'
import { getDeviceTypeLabel, getMountSideLabel, getPoeLabel, getStatusLabel } from '../lib/deviceMeta.js'
import { sprache, uebersetzen } from '../i18n/index.js'
const props = defineProps({ devices: { type: Array, default: () => [] }, racks: { type: Array, default: () => [] }, locations: { type: Array, default: () => [] }, connections: { type: Array, default: () => [] }, api: { type: Function, required: true } })
const emit = defineEmits(['print-rack', 'imported'])
const jsonLaedt = ref(false)
const jsonFehler = ref('')
function datum() { return new Date().toISOString().slice(0, 10) }
function rackVon(device) { return props.racks.find((rack) => Number(rack.id) === Number(device?.rack_id)) || null }
function ortVon(device) { return props.locations.find((ort) => Number(ort.id) === Number(device?.location_id)) || null }
function wohin(device) { return device?.rack_id ? `1${rackVon(device)?.name || ''}` : `2${ortVon(device)?.name || ''}` }
function geraetVon(id) { return props.devices.find((device) => Number(device.id) === Number(id)) || null }
function csvZelle(wert) {
  let text = wert === null || wert === undefined ? '' : String(wert)
  if (/^[=+\-@\t\r]/.test(text)) text = `'${text}`
  return /[";\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
}
function csvDatei(kopf, zeilen) { return '\uFEFF' + [kopf, ...zeilen].map((zeile) => zeile.map(csvZelle).join(';')).join('\r\n') }
function herunterladen(inhalt, dateiname, typ) {
  const url = URL.createObjectURL(new Blob([inhalt], { type: typ }))
  const link = document.createElement('a')
  link.href = url
  link.download = dateiname
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
function geraeteCsv() {
  const kopf = ['inventar.racks', 'details.standort', 'export.heVon', 'export.heBis', 'export.hoehe', 'details.einbauseite', 'export.name', 'details.typ', 'inventar.status', 'details.hersteller', 'details.modell', 'details.seriennummer', 'details.ip', 'details.mac', 'details.vlan', 'details.switchPort', 'details.uplinkPort', 'details.ports', 'export.poePorts', 'export.poeStandard', 'details.beschreibung', 'details.notizen'].map((key) => uebersetzen(key))
  kopf[0] = 'Rack'
  const zeilen = [...props.devices].sort((a, b) => wohin(a).localeCompare(wohin(b), sprache.value) || Number(b.start_unit) - Number(a.start_unit) || String(a.name || '').localeCompare(String(b.name || ''), sprache.value)).map((device) => {
    const rack = rackVon(device)
    const start = Number(device.start_unit) || ''
    const hoehe = Number(device.height_units) || 1
    return [rack?.name, rack ? rack.location : ortVon(device)?.name, start, start ? start + hoehe - 1 : '', hoehe, getMountSideLabel(device), device.name, getDeviceTypeLabel(device.device_type), getStatusLabel(device.status), device.manufacturer, device.model, device.serial_number, device.ip_address, device.mac_address, device.vlan, device.switch_port, device.uplink_port, device.network_ports, device.poe_ports, device.poe_type ? getPoeLabel(device.poe_type) : '', device.description, device.notes]
  })
  herunterladen(csvDatei(kopf, zeilen), `rackview-geraete-${datum()}.csv`, 'text/csv;charset=utf-8')
}
const STATUS = computed(() => Object.fromEntries(['active', 'planned', 'faulty', 'disconnected'].map((wert) => [wert, uebersetzen(`verbindungen.status.${wert}`)])))
function verbindungenCsv() {
  const kopf = ['export.quellgeraet', 'export.quellport', 'export.zielgeraet', 'export.zielport', 'export.verbindungstyp', 'inventar.status', 'details.notizen'].map((key) => uebersetzen(key))
  const zeilen = props.connections.map((verbindung) => {
    const quelle = geraetVon(verbindung.source_device_id) || verbindung.source_device
    const ziel = geraetVon(verbindung.target_device_id) || verbindung.target_device
    return [quelle?.name, verbindung.source_port?.name, ziel?.name, verbindung.target_port?.name, !verbindung.connection_type || verbindung.connection_type === 'direct' ? uebersetzen('verbindungen.direkt') : verbindung.connection_type, STATUS.value[verbindung.status || 'active'] || verbindung.status, verbindung.notes]
  })
  herunterladen(csvDatei(kopf, zeilen), `rackview-verbindungen-${datum()}.csv`, 'text/csv;charset=utf-8')
}
async function jsonSicherung() {
  jsonLaedt.value = true
  jsonFehler.value = ''
  try {
    const antwort = await fetch('/api/export', { headers: { Accept: 'application/json' } })
    if (!antwort.ok) throw new Error(uebersetzen('export.http', { status: antwort.status }))
    const daten = await antwort.json()
    herunterladen(JSON.stringify(daten, null, 2), `rackview-sicherung-${datum()}.json`, 'application/json')
  } catch (error) { jsonFehler.value = uebersetzen('export.sicherungFehler', { fehler: error.message }) }
  finally { jsonLaedt.value = false }
}
const anzahlPorts = computed(() => props.devices.reduce((summe, device) => summe + (Number(device.network_ports) || 0), 0))
const MODI = computed(() => [
  { wert: 'ergaenzen', label: uebersetzen('export.ergaenzen'), hinweis: uebersetzen('export.ergaenzenText') },
  { wert: 'ersetzen', label: uebersetzen('export.ersetzen'), hinweis: uebersetzen('export.ersetzenText') },
])
const dateiFeld = ref(null)
const dateiName = ref('')
const dokument = ref(null)
const modus = ref('ergaenzen')
const vorschau = ref(null)
const importLaeuft = ref(false)
const importFehler = ref('')
const verstanden = ref(false)
const bereit = computed(() => Boolean(vorschau.value) && !importLaeuft.value && (modus.value !== 'ersetzen' || verstanden.value))
const hatInhalt = computed(() => Boolean(vorschau.value) && (vorschau.value.neu.racks > 0 || (vorschau.value.neu.standorte || 0) > 0))
async function dateiGewaehlt(ereignis) {
  const datei = ereignis.target.files?.[0]
  zuruecksetzen({ feldLeeren: false })
  if (!datei) return
  dateiName.value = datei.name
  try {
    const daten = JSON.parse(await datei.text())
    if (daten?.format !== 'rackview-export') throw new Error(uebersetzen('export.falschesFormat'))
    dokument.value = daten
    await vorschauHolen()
  } catch (fehler) { importFehler.value = uebersetzen('export.dateiFehler', { fehler: fehler.message }) }
}
async function vorschauHolen() {
  if (!dokument.value) return
  importLaeuft.value = true
  importFehler.value = ''
  try { vorschau.value = await props.api('/import/preview', { method: 'POST', body: JSON.stringify({ modus: modus.value, daten: dokument.value }) }) }
  catch (fehler) { vorschau.value = null; importFehler.value = fehler.message }
  finally { importLaeuft.value = false }
}
async function modusWechseln(wert) {
  if (modus.value === wert) return
  modus.value = wert
  verstanden.value = false
  await vorschauHolen()
}
async function importieren() {
  if (!bereit.value) return
  importLaeuft.value = true
  importFehler.value = ''
  try {
    const antwort = await props.api('/import', { method: 'POST', body: JSON.stringify({ modus: modus.value, daten: dokument.value }) })
    zuruecksetzen()
    emit('imported', antwort.angelegt)
  } catch (fehler) { importFehler.value = fehler.message }
  finally { importLaeuft.value = false }
}
function wort(anzahl, einzahl, mehrzahl) { return uebersetzen(`export.${Number(anzahl) === 1 ? einzahl : mehrzahl}`) }
function zuruecksetzen({ feldLeeren = true } = {}) {
  dokument.value = null
  vorschau.value = null
  dateiName.value = ''
  importFehler.value = ''
  verstanden.value = false
  if (feldLeeren && dateiFeld.value) dateiFeld.value.value = ''
}
</script>

<template>
  <section class="panel view-panel">
    <div class="export-grid">
      <article class="export-card"><div class="export-icon">▤</div><h3>{{ uebersetzen('export.geraeteliste') }}</h3><p>{{ uebersetzen('export.geraeteText') }}</p><span class="export-meta">{{ devices.length }} {{ wort(devices.length, 'geraet', 'geraete') }} · CSV</span><button type="button" class="export-button" :disabled="!devices.length" @click="geraeteCsv">{{ uebersetzen('export.csv') }}</button></article>
      <article class="export-card"><div class="export-icon">⇄</div><h3>{{ uebersetzen('verbindungen.gesamt') }}</h3><p>{{ uebersetzen('export.verbindungenText') }}</p><span class="export-meta">{{ connections.length }} {{ wort(connections.length, 'verbindung', 'verbindungen') }} · CSV</span><button type="button" class="export-button" :disabled="!connections.length" @click="verbindungenCsv">{{ uebersetzen('export.csv') }}</button></article>
      <article class="export-card"><div class="export-icon">⎘</div><h3>{{ uebersetzen('export.sicherung') }}</h3><p>{{ uebersetzen('export.sicherungText') }}</p><span class="export-meta">{{ racks.length }} {{ wort(racks.length, 'rack', 'racks') }}<template v-if="locations.length"> · {{ locations.length }} {{ wort(locations.length, 'standort', 'standorte') }}</template> · {{ devices.length }} {{ wort(devices.length, 'geraet', 'geraete') }} · {{ anzahlPorts }} {{ wort(anzahlPorts, 'port', 'ports') }} · JSON</span><button type="button" class="export-button" :disabled="jsonLaedt" @click="jsonSicherung">{{ uebersetzen(jsonLaedt ? 'export.erstellen' : 'export.json') }}</button><p v-if="jsonFehler" class="export-error">{{ jsonFehler }}</p></article>
    </div>
    <div class="export-import">
      <h3>{{ uebersetzen('export.wiederherstellen') }}</h3><p>{{ uebersetzen('export.importText') }}</p>
      <div class="import-modi" role="group" :aria-label="uebersetzen('export.importArt')"><button v-for="art in MODI" :key="art.wert" type="button" :class="{ aktiv: modus === art.wert }" :aria-pressed="modus === art.wert" @click="modusWechseln(art.wert)"><strong>{{ art.label }}</strong><small>{{ art.hinweis }}</small></button></div>
      <div class="import-datei"><button type="button" class="export-button secondary" @click="dateiFeld?.click()">{{ uebersetzen('export.datei') }}</button><input ref="dateiFeld" type="file" accept="application/json,.json" class="import-feld" @change="dateiGewaehlt" /><span v-if="dateiName">{{ dateiName }}</span></div>
      <div v-if="importFehler" class="export-error">{{ importFehler }}</div><p v-else-if="importLaeuft && !vorschau" class="export-empty">{{ uebersetzen('export.pruefen') }}</p>
      <div v-if="vorschau" class="import-vorschau">
        <p class="import-zahlen">
          <span><strong>{{ vorschau.neu.racks }}</strong> {{ wort(vorschau.neu.racks, 'rack', 'racks') }}</span>
          <span v-if="vorschau.neu.standorte"><strong>{{ vorschau.neu.standorte }}</strong> {{ wort(vorschau.neu.standorte, 'standort', 'standorte') }}</span>
          <span><strong>{{ vorschau.neu.geraete }}</strong> {{ wort(vorschau.neu.geraete, 'geraet', 'geraete') }}</span>
          <span><strong>{{ vorschau.neu.ports }}</strong> {{ wort(vorschau.neu.ports, 'port', 'ports') }}</span>
          <span v-if="vorschau.neu.steckplaetze"><strong>{{ vorschau.neu.steckplaetze }}</strong> {{ wort(vorschau.neu.steckplaetze, 'steckplatz', 'steckplaetze') }}</span>
          <span><strong>{{ vorschau.neu.verbindungen }}</strong> {{ wort(vorschau.neu.verbindungen, 'verbindung', 'verbindungen') }}</span>
        </p>
        <ul v-if="vorschau.racks.length" class="import-racks"><li v-for="(rack, nr) in vorschau.racks" :key="nr"><span><strong>{{ rack.name }}</strong><small>{{ rack.location || uebersetzen('export.ohneStandort') }} · {{ uebersetzen('details.hoeheWert', { hoehe: rack.height_units }) }}</small></span><small>{{ rack.geraete }} {{ wort(rack.geraete, 'geraet', 'geraete') }} · {{ rack.ports }} {{ wort(rack.ports, 'port', 'ports') }}<template v-if="rack.steckplaetze"> · {{ rack.steckplaetze }} {{ wort(rack.steckplaetze, 'steckplatz', 'steckplaetze') }}</template></small></li></ul>
        <ul v-if="vorschau.standorte && vorschau.standorte.length" class="import-racks"><li v-for="(ort, nr) in vorschau.standorte" :key="`o${nr}`"><span><strong>{{ ort.name }}</strong><small>{{ ort.description || uebersetzen('details.standort') }}</small></span><small>{{ ort.geraete }} {{ wort(ort.geraete, 'geraet', 'geraete') }} · {{ ort.ports }} {{ wort(ort.ports, 'port', 'ports') }}<template v-if="ort.steckplaetze"> · {{ ort.steckplaetze }} {{ wort(ort.steckplaetze, 'steckplatz', 'steckplaetze') }}</template></small></li></ul>
        <p v-if="!hatInhalt" class="export-empty">{{ uebersetzen('export.keinInhalt') }}</p>
        <div v-if="vorschau.entfaellt" class="import-warnung"><strong>{{ uebersetzen('export.warnung') }}</strong><span>{{ uebersetzen('export.entfaellt', { racks: `${vorschau.entfaellt.racks} ${wort(vorschau.entfaellt.racks, 'rack', 'racks')}`, standorte: vorschau.entfaellt.standorte ? `${vorschau.entfaellt.standorte} ${wort(vorschau.entfaellt.standorte, 'standort', 'standorte')}, ` : '', geraete: `${vorschau.entfaellt.geraete} ${wort(vorschau.entfaellt.geraete, 'geraet', 'geraete')}`, verbindungen: `${vorschau.entfaellt.verbindungen} ${wort(vorschau.entfaellt.verbindungen, 'verbindung', 'verbindungen')}` }) }}</span><label><input v-model="verstanden" type="checkbox" />{{ uebersetzen('export.bestaetigen') }}</label></div>
        <details v-if="vorschau.hinweise.length" class="import-hinweise"><summary>{{ uebersetzen(vorschau.hinweise.length === 1 ? 'export.hinweis' : 'export.hinweise', { anzahl: vorschau.hinweise.length }) }}</summary><ul><li v-for="(hinweis, nr) in vorschau.hinweise" :key="nr">{{ hinweis }}</li></ul></details>
        <div class="import-aktionen"><button type="button" class="export-button" :disabled="!bereit || !hatInhalt" @click="importieren">{{ uebersetzen(importLaeuft ? 'export.importLaeuft' : modus === 'ersetzen' ? 'export.ersetzenImport' : 'export.importieren') }}</button><button type="button" class="export-button secondary" :disabled="importLaeuft" @click="zuruecksetzen()">{{ uebersetzen('export.abbrechen') }}</button></div>
      </div>
    </div>
    <div class="export-racks"><h3>{{ uebersetzen('export.pdf') }}</h3><p>{{ uebersetzen('export.pdfText') }}</p><ul v-if="racks.length"><li v-for="rack in racks" :key="rack.id"><span><strong>{{ rack.name }}</strong><small>{{ rack.location || uebersetzen('export.ohneStandort') }} · {{ (rack.devices || []).length }} {{ wort((rack.devices || []).length, 'geraet', 'geraete') }}</small></span><button type="button" class="export-button secondary" @click="emit('print-rack', rack)">{{ uebersetzen('etiketten.drucken') }}</button></li></ul><p v-else class="export-empty">{{ uebersetzen('export.keineRacks') }}</p></div>
    <p class="export-note">{{ uebersetzen('export.backupHinweis') }}</p>
  </section>
</template>

<style scoped>
.view-panel { display: flex; flex-direction: column; gap: 22px; padding: 22px 24px 26px; }
.export-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
.export-card { display: flex; flex-direction: column; gap: 8px; padding: 18px; border: 1px solid var(--f-ton-93-4); border-radius: 14px; background: var(--f-grau-100); }
.export-icon { display: grid; place-items: center; width: 38px; height: 38px; border-radius: 10px; background: var(--f-ton-96); color: var(--t-blau-53); font-size: 17px; }
.export-card h3, .export-racks h3 { margin: 4px 0 0; color: var(--t-ton-11); font-size: 15px; font-weight: 800; }
.export-card p, .export-racks > p { flex: 1; margin: 0; color: var(--t-ton-47-3); font-size: 12px; line-height: 1.55; }
.export-meta { color: var(--t-ton-61-2); font-size: 11px; font-weight: 600; }
.export-button { align-self: flex-start; margin-top: 4px; padding: 10px 14px; border: 0; border-radius: 10px; color: var(--t-grau-100); background: linear-gradient(135deg, var(--f-blau-61), var(--f-blau-53)); font: inherit; font-size: 12px; font-weight: 750; cursor: pointer; }
.export-button:disabled { opacity: 0.5; cursor: default; }
.export-button.secondary { margin-top: 0; border: 1px solid var(--f-ton-91-2); color: var(--t-ton-40); background: var(--f-grau-100); }
.export-button.secondary:hover { border-color: var(--f-blau-86-2); color: var(--t-blau-53); }
.export-error { color: var(--t-rot-42) !important; }
.export-racks { display: flex; flex-direction: column; gap: 8px; }
.export-racks ul { display: flex; flex-direction: column; gap: 6px; margin: 6px 0 0; padding: 0; list-style: none; }
.export-racks li { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 14px; border: 1px solid var(--f-ton-95); border-radius: 10px; }
.export-racks li span { display: flex; flex-direction: column; gap: 2px; }
.export-racks li strong { color: var(--t-ton-11); font-size: 13px; }
.export-racks li small { color: var(--t-ton-61-2); font-size: 11px; }
.export-empty, .export-note { margin: 0; color: var(--t-ton-61-2); font-size: 12px; }
.export-import { display: flex; flex-direction: column; gap: 12px; padding: 18px; border: 1px solid var(--f-ton-93-4); border-radius: 14px; background: var(--f-grau-100); }
.export-import > p { margin: 0; color: var(--t-ton-61-2); font-size: 12px; }
.import-modi { display: flex; flex-wrap: wrap; gap: 10px; }
.import-modi button { display: flex; flex-direction: column; gap: 2px; min-width: 210px; padding: 10px 14px; border: 1px solid var(--f-ton-91-2); border-radius: 12px; background: var(--f-grau-100); text-align: left; cursor: pointer; }
.import-modi button:hover { border-color: var(--f-blau-86-2); }
.import-modi button.aktiv { border-color: var(--f-blau-53); background: var(--f-ton-96); }
.import-modi strong { color: var(--t-ton-11); font-size: 13px !important; font-weight: 750; }
.import-modi small { color: var(--t-ton-61-2); font-size: 11.5px !important; }
.import-datei { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.import-datei .export-button { margin-top: 0; }
.import-datei span { color: var(--t-ton-40); font-size: 12px; }
.import-feld { display: none; }
.import-vorschau { display: flex; flex-direction: column; gap: 12px; padding-top: 12px; border-top: 1px solid var(--f-ton-95); }
.import-zahlen { display: flex; flex-wrap: wrap; gap: 18px; margin: 0; }
.import-zahlen span { color: var(--t-ton-61-2); font-size: 12px; }
.import-zahlen strong { margin-right: 4px; color: var(--t-ton-11); font-size: 15px; font-weight: 800; }
.import-racks { display: flex; flex-direction: column; gap: 6px; margin: 0; padding: 0; list-style: none; }
.import-racks li { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 8px 12px; border: 1px solid var(--f-ton-95); border-radius: 10px; }
.import-racks li span { display: flex; flex-direction: column; gap: 2px; }
.import-racks li strong { color: var(--t-ton-11); font-size: 13px; }
.import-racks li small { color: var(--t-ton-61-2); font-size: 11px; }
.import-warnung { display: flex; flex-direction: column; gap: 8px; padding: 12px 14px; border: 1px solid var(--f-rot-89); border-radius: 12px; background: var(--f-rot-51-3); }
.import-warnung strong { color: var(--t-rot-35); font-size: 13px; font-weight: 800; }
.import-warnung span { color: var(--t-rot-40); font-size: 12px; }
.import-warnung label { display: flex; align-items: center; gap: 8px; color: var(--t-rot-35); font-size: 12px; font-weight: 700; cursor: pointer; }
.import-hinweise summary { color: var(--t-ton-40); font-size: 12px; font-weight: 700; cursor: pointer; }
.import-hinweise ul { display: flex; flex-direction: column; gap: 4px; margin: 8px 0 0; padding-left: 18px; }
.import-hinweise li { color: var(--t-ton-61-2); font-size: 12px; }
.import-aktionen { display: flex; flex-wrap: wrap; gap: 10px; }
.import-aktionen .export-button { margin-top: 0; }
</style>
