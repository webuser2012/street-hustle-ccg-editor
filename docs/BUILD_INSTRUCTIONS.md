# Street Hustle CCG — Card Editor App Build Instructions
**For a coding agent to build a complete card creation/editing application**

---

## 🎯 PROJECT GOAL
Build a **web-based card editor** for Street Hustle CCG that allows users to:
- **Drag & drop custom artwork** onto each card
- **Design colors** for text, borders, backgrounds per card type/rarity
- **Edit all text fields** (name, stats, abilities, flavor text)
- **Maintain visual identity** by card type (Dealer/Stash/Action/Borough) and rarity
- **Export print-ready cards** and JSON data for the game engine
- **Load/save projects** from the master database (116 cards v9.6)

---

## 📦 SOURCE ASSETS (All in `/home/homer/Desktop/streethustle/`)

### Core Data Files
| File | Purpose |
|------|---------|
| `CCG_v9.6_Package/STREETHUSTLE_MASTER_DB_v9.6.json` | **Single source of truth** — 116 cards with full schema |
| `CCG_v9.6_Package/STREETHUSTLE_DEALERS_DB_v9.6.json` | 26 Dealer cards |
| `CCG_v9.6_Package/STREETHUSTLE_STASH_DB_v9.6.json` | 29 Stash cards |
| `CCG_v9.6_Package/STREETHUSTLE_ACTIONS_DB_v9.6.json` | 35 Action cards |
| `CCG_v9.6_Package/STREETHUSTLE_BOROUGHS_DB_v9.6.json` | 26 Borough cards |
| `CCG_v9.6_Package/DESIGN_DOC_v9.6.md` | Complete game design document |
| `CCG_v9.6_Package/CARD_ART_PROMPTS_v9.6_COMPLETE.md` | 116 Leonardo.ai prompts |
| `CCG_v9.6_Package/cards_v5.1_original.html` | Print template reference (52 cards) |
| `CARD_ART_PROMPTS_LEONARDO.md` | 41 prompts with style guide |

### Visual Reference
| File | Purpose |
|------|---------|
| `webpages/cards.html` | **Current print template** — CSS variables, card structure, 5 sheets × 9 cards |
| `webpages/index.html` | Marketing site with design system (colors, fonts, noise, scanlines) |
| `deploy/index.html` | Alt marketing version |
| `deploy-ctc/index.html` | Coast-to-Coast marketing version |

---

## 🎨 DESIGN SYSTEM (Extract from existing files)

### CSS Variables (Root Tokens)
```css
:root {
  /* Core palette */
  --or: #ff6600;   /* Primary orange */
  --am: #ff9900;   /* Amber */
  --gd: #ffcc00;   /* Gold */
  --gr: #00cc44;   /* Green */
  --bl: #2299ff;   /* Blue */
  --pu: #bb44ff;   /* Purple */
  --re: #ff2200;   /* Red */
  
  /* Backgrounds */
  --bg: #0a0400;   /* Card bg */
  --bg2: #150800;  /* Band bg */
  --bg3: #160a00;  /* Section bg */
  
  /* Text */
  --tx: #ffd9a0;   /* Primary text */
  --tx2: #8a5030;  /* Secondary text */
  --tx3: #ffeedd;  /* Bright text */
  
  /* Borders */
  --bdr: #3a1800;  /* Border color */
  
  /* Rarity borders */
  --common: #666;
  --uncommon: #2299ff;
  --rare: #ff6600;
  --legendary: #ffcc00;
  
  /* Type colors (for badges/borders) */
  --dealer-color: #ff6600;
  --stash-color: #00cc44;
  --action-color: #2299ff;
  --borough-color: #bb44ff;
}
```

### Typography
| Element | Font | Usage |
|---------|------|-------|
| Display/Title | `Bebas Neue` | Card names, big numbers, headers |
| UI/Mono | `Space Mono` | Labels, stats, keywords, small caps |
| Body | `Barlow Condensed` | Ability text, flavor text |

### Card Dimensions
- **Print size**: 2.25" × 3.5" (63.5mm × 88.9mm)
- **Art aspect**: Portrait, fills ~60% of card height
- **Web preview**: Scale to ~300px × 467px for editor
- **Art generation**: 512×768 (Leonardo.ai) → upscale to 1024×1536 for print

### Sacred Geometry by Card Type
| Type | Geometry Pattern | Visual Treatment |
|------|------------------|------------------|
| **Dealer** | Metatron's Cube | Halo/aura behind figure |
| **Stash** | Flower of Life / Seed of Life | Energy field around product |
| **Action** | Sri Yantra / Merkaba | Star burst radiating from center |
| **Borough** | Hexagonal grid | Overlaid on cityscape |

### Rarity Neon Colors
| Rarity | Neon Colors |
|--------|-------------|
| Common | Green + Orange |
| Uncommon | Blue + Teal |
| Rare | Gold + Amber |
| Legendary | Purple + Crimson + White |

---

## 🃏 CARD DATA SCHEMA (from Master DB)

```json
{
  "id": "unique_id",
  "set": "SCE|CTC|EXP1|EXP2|EXP3",
  "type": "dealer|stash|action|borough",
  "name": "Card Name",
  "emoji": "🎴",
  "cost": 0,
  "rarity": "common|uncommon|rare|legendary",
  "faction": "FACTION_NAME|null",
  "text": "Rules text for display",
  "flavor": "Flavor text",
  "keywords": ["KEYWORD1", "KEYWORD2"],
  "art_prompt": "Leonardo.ai prompt",
  
  // Dealer-specific
  "hp": 10,
  "atk": 1,
  "def": 0,
  "ability": "Special ability text",
  
  // Stash-specific
  "drug": "weed|heroin|cocaine|...",
  "atkBonus": 1,
  "special": "heal2|double_attack|...",
  
  // Action-specific
  "effect": "One-shot effect description",
  
  // Borough-specific
  "heatGain": 1,
  "bonus": "Passive bonus description"
}
```

### Factions (6) with Colors
| Faction | Color | Icon | Theme |
|---------|-------|------|-------|
| STREET_CREW | #FF6600 | 👥 | Aggression, early game |
| UPTOWN_SYNDICATE | #FFCC00 | 👑 | Control, late game |
| BROOKLYN_CONNECT | #00CC44 | 🌿 | Ramp, Stash synergy |
| BRONX_RUNNERS | #2299FF | 🏃 | Speed, mobility |
| GHOST_NETWORK | #BB44FF | 👻 | Evasion, control |
| FEDERAL_TASKFORCE | #FF2200 | 🏛️ | Disruption, removal |

### Keywords (22 total)
`SUPPLY_CHAIN`, `HASTE`, `SHIELD`, `TRAVEL`, `CONNECTION`, `TURF_WAR`, `FEDERAL_HEAT`, `SYNDICATE`, `LAUNDER`, `PRESTIGE`, `CARTEL`, `BORDER`, `MULE`, `CRYPTO`, `ANONYMOUS`, `DEAD_DROP`, `CONTRABAND`, `GUARD`, `YARD`, `COMMISSARY`, plus custom ones like `STASH_BOOST`, `PLUG_HEAT`, `DRAIN_HEAT`, `ACTION_IMMUNE`, `COP_IMMUNE`, `UNLIMITED_STASH`, `BOSS_PER_STASH`, `KO_HEAT`, `SCOUT`, `MULE`, `STASH_MASTERY`, `DRAW_ON_STASH`, `CONNECTION`, `KINGPIN_ENTRY`, `LEGACY_RECRUIT`, `FACTION_HP_BOOST`, `HIVE_STASH_DISCOUNT`, `TOKEN_GENERATION`, `CORRUPTION`, `FEDERAL_DISCOUNT`, `ACTION_DRAW`, `COMMISSARY`, `CONTRABAND`, `YARD`, `KO_PENALTY`, `GRANT_HASTE`, `BURNOUT`, `GRANT_SHIELD`, `QUEENS_BONUS`, `HEAL_ON_ATTACH`, `STATEN_BONUS`, `DRAW_ON_ATTACH`, `BROOKLYN_BONUS`, `ANTI_FREEZE`, `STRIP_DEF`, `RANDOM_ATK_VARIABLE`, `BREAKTHROUGH`, `CHEAT_DEATH`, `FREEZE_ON_ATTACK`, `FREE`, `CHAOS_VARIABLE`, `BRONX_BONUS`, `CONFUSE_ON_ATTACK`, `DOUBLE_ATTACK`, `ON_ATTACH_DAMAGE`, `HEAL_ON_PLAY`, `RANDOM_ATK`, `PLUG_HEAT`, `DRAIN_HEAT`, `ACTION_IMMUNE`, `SUPPLY_CHAIN_EXEMPT`, `COP_IMMUNE`, `UNLIMITED_STASH`, `BOSS_PER_STASH`, `KO_HEAT`, `SCOUT`, `STASH_BOOST`, `BOROUGH_BONUS`, `HEAT_ON_ENTRY`, `TURF_WAR`, `ACTION_IMMUNE_TURF`, `CRYPTO`, `ANONYMOUS`, `DEAD_DROP`, `ENTRY_DESTROY_STASH`, `CARTEL`, `PRESTIGE`, `LAUNDER`, `SYNDICATE`, `FEDERAL_HEAT`, `CONNECTION`, `MULE`

---

## 🛠️ APP REQUIREMENTS

### 1. **Project Dashboard / Card Library**
- Grid view of all 116 cards (filterable by type, rarity, set, faction)
- Thumbnail preview with art (or placeholder)
- Quick stats: name, type, rarity, cost, faction
- Search by name, ID, keyword
- Bulk operations (export, duplicate, delete)

### 2. **Card Editor (Main View)**
#### Left Panel: Card Canvas (Live Preview)
- **Exact visual replica** of print template (cards.html)
- Real-time updates as user edits
- Zoom controls (50%–200%)
- Toggle: Print view / Screen view / Art-only view

#### Right Panel: Property Editor (Tabbed)

**Tab 1: Basic Info**
- Card ID (auto-gen, editable)
- Set selector (SCE/CTC/EXP1/EXP2/EXP3)
- Type selector (Dealer/Stash/Action/Borough) → **changes layout**
- Rarity selector → **updates border color, neon palette**
- Faction selector (if applicable) → **updates type badge color**
- Cost (Heat) input
- Emoji picker

**Tab 2: Artwork**
- **Drag & drop zone** for card art (accept: PNG, JPG, WebP)
- Preview with aspect ratio lock (2.25:3.5 = 0.643)
- **Position/scale controls**: Pan, zoom, fit/cover toggle
- Opacity slider (for watermarking)
- **Art prompt display** (from DB) with "Regenerate" button → opens Leonardo.ai URL
- **Clear art** button → reverts to type-specific placeholder gradient
- *Optional*: AI upscale integration (Replicate/Stability API)

**Tab 3: Text Content** (dynamic per type)
- **Dealer**: Name, Subtitle, HP, ATK, DEF, Ability Text, Flavor Text
- **Stash**: Name, Subtitle (e.g., "+1 ATK · Attach to Dealer"), ATK Bonus, Ability Text, Flavor Text
- **Action**: Name, Cost Display (FREE/1/2/3), Effect Text, Flavor Text
- **Borough**: Name, Subtitle ("Borough · Free to play"), Heat/Turn, Ability Text, Flavor Text
- **All**: Set info (e.g., "v5.1 · SCE"), Collector number

**Tab 4: Colors & Styling** (Advanced)
- **Per-element color pickers** with live preview:
  - Card background (--bg)
  - Band background (--bg2)
  - Primary text (--tx)
  - Secondary text (--tx2)
  - Accent text (--tx3)
  - Border color (--bdr)
  - **Rarity border** (auto from rarity, but overrideable)
  - **Type badge color** (auto from type, but overrideable)
  - Stat colors (HP green, ATK orange, DEF blue, Boost green)
  - Ability tag backgrounds (per keyword/type)
- **Presets**: "Default", "High Contrast", "Colorblind Safe", "Printer Friendly"
- **Copy/Paste style** between cards
- **Reset to defaults** button

**Tab 5: Keywords & Mechanics**
- Multi-select keyword chips (filterable by set)
- Custom keyword input (for homebrew)
- Keyword tooltip on hover (from DESIGN_DOC)
- Validation: warns if `SUPPLY_CHAIN` missing on Dealer, etc.

**Tab 6: Export & Data**
- **Export JSON** (single card / selected / all) — matches master DB schema
- **Export HTML** (print sheet: 3×3 grid with cut marks)
- **Export PNG** (single card @ 300 DPI for print)
- **Export PDF** (full set, print-ready with bleed)
- **Import JSON** (merge/replace)
- **Save Project** (localStorage + file download .shccg format)

### 3. **Color Theme Designer** (Global)
- Master color palette editor (all CSS variables)
- **Type presets**: Dealer/Stash/Action/Borough base themes
- **Rarity presets**: Common/Uncommon/Rare/Legendary border glows
- **Faction presets**: 6 faction color schemes
- **Live preview** on sample cards
- **Export CSS variables** for use in game engine
- **Import/Export theme JSON**

### 4. **Batch Operations**
- **Apply theme to all cards** of a type/rarity/set
- **Bulk art assignment** (folder drop → auto-match by card ID)
- **Bulk text find/replace** (e.g., update all "Heat" → "Energy")
- **Generate missing placeholders** for cards without art
- **Validate deck** (check required fields, keyword consistency)

---

## 🖥️ TECH STACK RECOMMENDATIONS

### Core Framework
- **React 18** + **TypeScript** + **Vite** (fast, modern)
- **Tailwind CSS** (maps perfectly to CSS variables) or raw CSS with CSS Variables
- **Zustand** or **Jotai** for state (lightweight)
- **React DnD** or **@dnd-kit** for drag-drop art

### Key Libraries
| Need | Library |
|------|---------|
| Drag-drop file upload | `react-dropzone` |
| Image crop/zoom/pan | `react-image-crop` or `cropperjs` |
| Color picker | `react-colorful` (tiny, no deps) |
| PDF generation | `@react-pdf/renderer` or `pdf-lib` + `html2canvas` |
| PNG export | `html2canvas-pro` or `dom-to-image-more` |
| File download | `file-saver` |
| Local storage persistence | `idb` (IndexedDB wrapper) |
| Keyboard shortcuts | `hotkeys-js` |
| Icons | `lucide-react` |
| Tooltips | `floating-ui` + custom |
| Virtualized list | `@tanstack/react-virtual` (for 116+ cards) |

### Project Structure
```
street-hustle-card-editor/
├── public/
│   ├── fonts/           # Bebas Neue, Barlow Condensed, Space Mono (WOFF2)
│   └── placeholders/    # Type-specific SVG placeholders
├── src/
│   ├── components/
│   │   ├── CardCanvas/          # Live preview (exact CSS from cards.html)
│   │   ├── CardEditor/          # Right panel tabs
│   │   ├── CardLibrary/         # Grid view, filters, search
│   │   ├── ThemeDesigner/       # Global color system
│   │   ├── ArtUploader/         # Drag-drop, crop, position
│   │   ├── PropertyTabs/        # Tabbed property panels
│   │   └── ExportDialog/        # Multi-format export
│   ├── hooks/
│   │   ├── useCardData.ts       # Load/save master DB
│   │   ├── useProject.ts        # Project state (IndexedDB)
│   │   ├── useTheme.ts          # CSS variable management
│   │   └── useExport.ts         # Export pipelines
│   ├── data/
│   │   ├── masterDB.json        # Imported at build or runtime
│   │   ├── cardSchema.ts        # Zod validation schemas
│   │   ├── keywords.ts          # Keyword definitions + tooltips
│   │   ├── factions.ts          # Faction data
│   │   └── rarity.ts            # Rarity configs
│   ├── utils/
│   │   ├── cardRenderer.ts      # HTML→Canvas/PDF rendering
│   │   ├── colorUtils.ts        # Contrast, palette generation
│   │   ├── fileUtils.ts         # Import/export helpers
│   │   └── idGenerator.ts       # Unique ID generation
│   ├── styles/
│   │   ├── cards.css            # Exact card styles from cards.html
│   │   ├── editor.css           # Editor UI styles
│   │   └── variables.css        # CSS variable definitions
│   └── types/
│       └── card.ts              # TypeScript interfaces
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

---

## 🔑 CRITICAL IMPLEMENTATION DETAILS

### Card Canvas Component (Pixel-Perfect)
**Must replicate `cards.html` CSS exactly.** Key structural classes:
```html
<div class="card {rarity} {type}">
  <div class="card-top">
    <span class="card-type {type}">{TYPE}</span>
    <div class="card-cost">{HEAT_PIPS}</div>
  </div>
  <div class="card-art">
    <img src="{art}" />  <!-- or .card-art-placeholder -->
  </div>
  <div class="card-name-band">
    <div class="card-name">{NAME}</div>
    <div class="card-subtitle">{SUBTITLE}</div>
  </div>
  <div class="card-stats">
    <!-- Dealer: HP/ATK/DEF | Stash: BOOST | Action: COST | Borough: HEAT/TURN -->
  </div>
  <div class="card-body">
    <span class="ability-tag {type}">{KEYWORD}</span>
    <div class="ability-text">{ABILITY}</div>
    <div class="flavor-text">{FLAVOR}</div>
  </div>
  <div class="card-footer">
    <span class="rarity-label">{RARITY}</span>
    <span class="set-info">{SET_INFO}</span>
  </div>
</div>
```

### Heat Pips Rendering
```tsx
function HeatPips({ cost, color = 'var(--or)' }) {
  return (
    <div className="card-cost">
      {Array.from({ length: cost }, (_, i) => (
        <span key={i} className="heat-pip" style={{ background: color }} />
      ))}
      {cost === 0 && <span style={{ fontSize: '8px', color: 'var(--gr)' }}>FREE</span>}
    </div>
  );
}
```

### Type-Specific Placeholder Gradients (from cards.html)
```css
.card.dealer .card-art-placeholder    { background: linear-gradient(160deg, #1a0500 0%, #0a0300 100%); }
.card.stash .card-art-placeholder     { background: linear-gradient(160deg, #001a08 0%, #000a03 100%); }
.card.action .card-art-placeholder    { background: linear-gradient(160deg, #00091a 0%, #000308 100%); }
.card.borough .card-art-placeholder   { background: linear-gradient(160deg, #0d001a 0%, #040008 100%); }
```

### Legendary Special Styling
```css
.card.legendary {
  box-shadow: 0 0 12px rgba(255,204,0,0.4);
}
.card.legendary .card-name { color: var(--legendary); }
.card.legendary .card-stats { background: #0d0800; }
.card.legendary .stat-val { color: var(--legendary); }
```

### Print Sheet Layout (3×3 grid)
```css
.sheet {
  width: 8.5in;
  display: grid;
  grid-template-columns: repeat(3, 2.25in);
  grid-template-rows: repeat(3, 3.5in);
  gap: 0.125in;
  padding: 0.35in;
  page-break-after: always;
}
@media print {
  .sheet { margin: 0; box-shadow: none; }
  body { background: white; }
}
```

---

## 🎯 USER WORKFLOWS

### Workflow 1: Create New Card from Scratch
1. Click "New Card" → choose Type (Dealer/Stash/Action/Borough)
2. Auto-generates ID: `{type}_{set}_{slugified-name}`
3. Fills defaults from type template
4. User edits all fields, drops art, picks colors
5. Saves → appears in library

### Workflow 2: Edit Existing Card (from Master DB)
1. Load master DB (auto on startup)
2. Click card in library → opens in editor
3. All fields populated, art shows placeholder if no image
4. User modifies → "Save" updates project (not master DB)
6. "Export to Master DB" → writes JSON file

### Workflow 3: Bulk Art Import
1. User has folder of 116 PNGs named `{set}_{id}_{name}.png`
2. Drop folder → app matches by ID, assigns to cards
3. Review unmatched, manual assign if needed
4. Batch export print sheets

### Workflow 4: Theme Customization
1. Open Theme Designer
2. Adjust master palette → all cards update live
3. Save theme → exports `theme.css` + `theme.json`
4. Apply to game engine (web game, print template)

### Workflow 5: Print Production
1. Select cards (or "All")
2. Choose "Export Print Sheets (PDF)"
3. App generates 13 pages (3×3) with cut marks, bleed
4. Download PDF → send to printer

---

## 📋 ACCEPTANCE CRITERIA

### Must Have (MVP)
- [ ] Load master DB JSON, display all 116 cards in library
- [ ] Card canvas matches `cards.html` visually (pixel-perfect)
- [ ] Drag-drop art onto card, auto-fit/crop, persists in project
- [ ] Edit all text fields per card type with live preview
- [ ] Rarity selector updates border color + neon palette
- [ ] Type selector changes layout (stats, placeholders)
- [ ] Export single card JSON (matches master schema)
- [ ] Export print sheet HTML (3×3 grid, cut marks)
- [ ] Save/load project to localStorage + .shccg file
- [ ] Theme designer edits CSS variables, exports CSS/JSON
- [ ] Keyboard shortcuts: Save (Cmd+S), Undo (Cmd+Z), Next/Prev card

### Should Have
- [ ] Batch art import (folder drop → auto-match)
- [ ] Export PNG @ 300 DPI (print quality)
- [ ] Export multi-page PDF (print-ready with bleed)
- [ ] Color presets (colorblind, high contrast, printer)
- [ ] Keyword validation warnings
- [ ] Copy/paste style between cards
- [ ] Search/filter library (type, rarity, set, faction, keyword)
- [ ] Art prompt display + "Open in Leonardo.ai" link

### Nice to Have
- [ ] AI upscale integration (Replicate API)
- [ ] Version history per card
- [ ] Collaboration (share project URL with encoded state)
- [ ] Deck builder mode (filter legal cards, count copies)
- [ ] Simulator preview (test card in game engine)
- [ ] Plugin system for custom card types

---

## 🚀 GETTING STARTED COMMANDS

```bash
# 1. Create project
npm create vite@latest street-hustle-card-editor -- --template react-ts
cd street-hustle-card-editor

# 2. Install deps
npm install zustand react-dropzone react-image-crop react-colorful \
  @react-pdf/renderer html2canvas-pro file-saver idb hotkeys-js \
  lucide-react @tanstack/react-virtual zod
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# 3. Copy fonts to public/fonts/ (Bebas Neue, Barlow Condensed, Space Mono WOFF2)
# 4. Copy cards.html CSS to src/styles/cards.css
# 5. Import master DB to src/data/masterDB.json

# 6. Run dev
npm run dev
```

---

## 📁 FILES TO REFERENCE DURING BUILD

| File | What to Extract |
|------|-----------------|
| `webpages/cards.html` | **Complete card CSS, HTML structure, print styles** |
| `webpages/index.html` | Design system (noise, scanlines, fonts, color usage) |
| `CCG_v9.6_Package/DESIGN_DOC_v9.6.md` | Game rules, keywords, factions, schema, agent tasks |
| `CCG_v9.6_Package/STREETHUSTLE_MASTER_DB_v9.6.json` | All 116 cards data, expansion framework |
| `CARD_ART_PROMPTS_LEONARDO.md` | Style guide, prompts, negative prompts, Leonardo settings |

---

## 💡 ARCHITECTURE NOTES FOR THE AGENT

1. **Separate concerns**: Card rendering (pure CSS/HTML) ≠ Editor UI state
2. **CSS Variables are king**: All theming flows through `:root` vars — editor just mutates them
3. **Card canvas = reusable component**: Use same component for preview, print sheet, export
4. **Project ≠ Master DB**: Project is user's working copy; Master DB is read-only reference
5. **Type-driven UI**: When `type` changes, swap the entire property panel layout
6. **Art is optional**: Placeholder gradients are part of the design — don't require images
7. **Print CSS is sacred**: Test `window.print()` output early and often
8. **Performance**: Virtualize library grid; debounce canvas re-renders (150ms)

---

## 🎨 VISUAL REFERENCE: CARD ANATOMY

```
┌─────────────────────────────────────┐  ← 2.25" wide
│ [TYPE BADGE]              [COST]    │  ← .card-top (bg2, 4px padding)
├─────────────────────────────────────┤
│                                     │
│           ARTWORK                   │  ← .card-art (flex:1, ~60% height)
│        (drag-drop zone)             │     Aspect: 2.25:3.5 = 0.643
│                                     │
├─────────────────────────────────────┤  ← .card-name-band (bg2)
│ CARD NAME                           │     .card-name (Bebas Neue, 15px)
│ Subtitle text                       │     .card-subtitle (Space Mono, 6px)
├─────────────────────────────────────┤  ← .card-stats (#0d0500 bg)
│  HP  │   ATK  │   DEF   │           │     3 columns (Dealer)
│  10  │   1    │   0     │           │     Stat val: Bebas Neue 14px
├─────────────────────────────────────┤  ← .card-body (bg)
│ [KEYWORD TAG]                       │     .ability-tag (type-colored)
│ Ability description text...         │     .ability-text (7.5px)
│ "Flavor text in italics..."         │     .flavor-text (6.5px, italic)
├─────────────────────────────────────┤  ← .card-footer (bg2)
│ [RARITY]                    [SET]   │     .rarity-label + .set-info
└─────────────────────────────────────┘  ← 3.5" tall
```

---

## 🔗 INTEGRATION POINTS

### For Web Game (`StreetHustle_CCG_v9.6.html`)
- Export `cards.json` → load at runtime
- Export `theme.css` → inject for consistent look
- Export `art-manifest.json` → `{ cardId: "path/to/art.png" }`

### For Print-on-Demand (DriveThruCards, TheGameCrafter)
- Export PDF with 1/8" bleed
- CMYK color profile (convert from RGB)
- 300 DPI minimum
- Card backs included (separate file)

### For Art Pipeline
- Export `prompts.csv` → `{id, name, prompt, negative, settings}`
- Import generated art via batch matcher
- Track generation status per card

---

*End of Build Instructions — Street Hustle CCG Card Editor v1.0*
*Generated from live project assets August 2026*