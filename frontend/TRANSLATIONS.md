# Translation foundation

Status: foundation only. Existing screens, backend messages, exports, dates and plural forms have not yet been migrated or verified.

English is the default and fallback. The selector stores the preference in localStorage under rackview-language and updates the HTML lang attribute. Storage failures are tolerated.

Existing identifiers and stored values must not be renamed. Only application-provided display text should be translated; never translate user-entered content.

## Adding a language

Copy src/i18n/locales/en.json to a new locale JSON file, for example fr.json, and translate its values. Locale files are discovered at build time; rebuild the frontend. Add an optional native-language label to bezeichnungen in Sprachwahl.vue; otherwise the locale code is displayed. Do not change translation keys.

## Migrating text

In templates use {{ $t('bereich.schluessel') }}. In script setup import uebersetzen from the i18n module. Keep reactive derived text inside computed functions so it updates when the language changes. Use German translation keys for new entries. Translate complete sentences and pass interpolation values as the second argument, e.g. uebersetzen('geraete.anzahl', { anzahl: liste.length }). This foundation supports named interpolation but not plural rules; add plural support before migrating count-dependent sentences.

## Remaining work and verification

Migrate App.vue, components, shared display helpers, backend validation and exports. Add automated key-parity checks, plural handling and locale-aware formatting. Run the frontend production build, Docker build and browser tests in both languages. Verify persistence, keyboard navigation and selector placement on mobile and in dialogs. No build or runtime tests were executed for this foundation in the assistant environment.
