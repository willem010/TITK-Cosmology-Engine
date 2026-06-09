# TITK Cosmology Engine (v1.4)
> **Topologische Informatietheorie van de Kosmos**

---

> ⚠️ **CRITICAL SYSTEM NOTICE:** > *I am only here because the server was down.* > This entire framework was conceptualized during an unscheduled operational intermission. Proceed with structural caution.

---

TITK is een computationeel en theoretisch model waarin de ruimtetijd niet als een continuüm wordt beschreven, maar emergent voortvloeit uit een schaalvrij, discreet netwerk van informatieverwerkende knooppunten (*nodes*). 

Het model reduceert de complexiteit van de kosmologie door de 19 onverklaarde, vrije parameters van het Standaardmodel te vervangen door slechts **drie fundamentele netwerkvariabelen**.

---

## 1. De Drie Fundamentele Variabelen

Waar de klassieke fysica gebruikmaakt van abstracte concepten zoals massa, zwaartekracht en tijddilatatie, verklaart TITK deze fenomenen mechanistisch vanuit drie strikte netwerkregels:

1. **$W_{max}$ (Vast Budget):** De absolute maximale informatiecapaciteit per lokale node binnen één universele matrixcyclus ($T_{obs} = 1$). Dit dwingt een strikte wet van informatiebehoud af ($\Phi_{ext} = W_{max} - T_{eff}$).
2. **De $\frac{T_{eff}}{\Phi_{ext}}$ Verhouding (De Boekhoudregel):** De balans tussen de interne synchronisatiekosten ($T_{eff}$) en de externe output-doorvoer ($\Phi_{ext}$). Naarmate de interne verwerkingslast stijgt, daalt de externe doorvoer asymptotisch naar nul. Dit manifesteert zich macroscopisch als *tijddilatatie*.
3. **$Q_{max}$ (Kritieke Consolidatiecapaciteit):** De maximale diepte van de topologische wachtrij (*queue depth*). Wanneer de lokale netwerkcongestie deze drempelwaarde overschrijdt, raakt de node verzadigd en loopt het causale pad vast. Dit vormt de exacte mechanistische definitie van een *zwart gat*.

---

## 2. Repository Structuur

Het project is modulair opgebouwd en scheidt de formele specificaties strikt van de computationele implementatie:

```text
├── theorie/
│   ├── 01_conceptuele_herlijning_en_verstrakking.md
│   ├── 02_de_gereviseerde_node_en_het_consolidatieprincipe.md
│   ├── 03_mechanica_van_de_systeemgrens_markov_blanket.md
│   ├── 04_het_wachtrij_principe_en_limieten.md
│   ├── 05_open_onderzoeksvragen.md
│   ├── 06_emergente_fysica_en_faseovergangen.md
│   ├── 07_deeltjesmassas_als_netwerkbelasting.md
│   ├── 08_supernova_als_queue_overflow.md
│   ├── 09_zwaartekracht_als_netwerkcongestie.md
│   ├── 10_fractale_node_hierarchie.md
│   ├── 11_de_drie_universele_variabelen.md
│   └── 12_geparkeerde_ideeen.md
│
└── titk_sim.py        # Core Computation Engine (Python 3 / NumPy)
```

## 3. De Engine: `titk_sim.py`

De core engine is een volledig gevectoriseerde Python-implementatie. Om iteratielatency te elimineren, maakt de simulatie intensief gebruik van matrix-convoluties via `scipy.ndimage.uniform_filter` en discrete 2D FFT's (`scipy.fft.fft2`).

### Kernfunctionaliteit:
* **Primordiaal Ruisveld:** Genereert een 1/f topologische ruisdistributie (Harrison-Zel'dovich spectrum) over 7 octaven, gecombineerd met baryonische condensatie-zaaikernen.
* **Gevectoriseerde Update-Regel:** Berekent per cyclus de lokale interconnectiviteit, de effectieve interne tijd (T_eff), netwerk-backpressure en de actieve saturatiegraad (Q_max).
* **Kwantitatief Toetsingskader:** Slaat bij het ontkoppelingsmoment (T_obs = 380) een snapshot op van de kosmische achtergrondstraling (CMB) en voert een radiale binning uit op het vermogensspectrum.

---

## 4. Installatie & Gebruik

### Vereisten
Zorg ervoor dat Python 3.8+ en de vereiste computationele bibliotheken zijn geïnstalleerd:

pip install numpy scipy matplotlib

### Simulatie Uitvoeren
Start de engine met het volgende commando:

python3 titk_sim.py

De engine genereert real-time systeemtelemetrie in de terminal en schrijft binaire matrix-toestanden (`.npy`) en een grafische analyse-figuur (`titk_result.png`) weg naar de map `./titk_output/`.

---

## 5. Kwantitatief Toetsingskader

Binnen de Fractale Node-Hiërarchie is de bekende piekverhouding in het Cosmic Microwave Background (CMB) power spectrum een schaalinvariante constante. 

De engine valideert de theorie direct na de run door de berekende multipool-pieken van het simulatiegrid mathematisch te vergelijken met de reële observatiedata van de Planck-satelliet (2018). Een succesvolle match binnen een marge van +-15% op de akoestische piekverhouding (l2 / l1 = 2.70) geldt als de primaire kwantitatieve vuurdoop voor het model.
