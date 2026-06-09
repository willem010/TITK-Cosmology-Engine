## 2. DE GEREVISEERDE NODE & HET CONSOLIDATIEPRINCIPE

### 2.1 Publieke Toestand ($\sigma_{pub}$) versus Interne Structuur ($\sigma_{int}$)
Binnen de architectuur van TITK is een node geen monolithisch, dimensieloos punt, maar een lokaal informatiesysteem met een strikte, wetmatige scheiding in toegankelijkheid en computationele rechten:

* **$\sigma_{int}$ (Interne Structuur):** De private, computationele micro-toestand van de node. Binnen deze afgeschermde zone worden parallelle feedbacklussen, interne synchronisaties en micro-transities berekend zonder directe invloed van buitenaf.
* **$\sigma_{pub}$ (Publieke Toestand):** De geaggregeerde grensvoorwaarde van de node. Alleen deze toestand is extern zichtbaar, leesbaar en beschikbaar voor aangrenzende nodes ten behoeve van de eerstvolgende causale hop ($T_{obs}$).

---

### 2.2 Het Consolidatieprincipe (State-Compressie via Projectie)
Een fundamenteel axioma binnen TITK is dat informatie binnen het universum niet verdwijnt of wordt vernietigd, maar *consolideert* zodra haar causale bijdrage volledig is geabsorbeerd en verwerkt in de actuele toestand van het systeem.

#### Het Mechanisme
De kosmische matrix bewaart fundamenteel niet de geschiedenis van elke individuele microscopische interactie; er is geen sprake van een oneindige, alsmaar uitdijende *event log*. Zodra een complexe reeks microscopische causale updates (zoals miljarden interne botsingen of micro-transities binnen $\sigma_{int}$) heeft geleid tot een stabiel macroscopisch aggregaat (bijvoorbeeld een stabiel macro-drukprofiel of een evenwichtstoestand), mag de historische micro-informatie consolideren naar een lagere resolutie.

#### De Ontwerpregel
De matrix streeft inherent naar een minimale representatie die exact dezelfde causale toekomst oplevert:

$$\text{Minimale Representatie} \implies \text{Invariante Causale Toekomst}$$

Dit compressiemechanisme fungeert als een natuurlijke, wetmatige rem op een geheugenexplosie binnen de matrix. Het verklaart waarom macroscopische systemen stabiel kunnen opereren zonder te bezwijken onder de computationele last van hun onderliggende kwantumruis.
