# TITK Cosmology Engine (v1.4)
> **Topologische Informatietheorie van de Kosmos**

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
│   └── 10_fractale_node_hierarchie.md
│
└── titk_sim.py        # Core Computation Engine (Python 3 / NumPy)
