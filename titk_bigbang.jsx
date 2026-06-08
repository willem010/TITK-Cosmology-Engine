import { useState, useEffect, useRef, useCallback } from "react";

// ─── TITK CONFIG ───────────────────────────────────────────────
const CFG = {
  GRID: 128,           // spatial resolution
  Q_MAX: 12,           // max queue depth (black hole threshold)
  W_MAX: 100,          // fixed budget
  K_FACTOR: 6,         // internal cost multiplier
  C_RADIUS: 0.06,      // connection radius (in grid units normalised)
  DAMPING: 0.88,
  NOISE_AMP: 0.15,     // primordial quantum noise amplitude
  DECOUPLING_CYCLE: 380, // "ontkoppeling" — CMB snapshot moment
  TOTAL_CYCLES: 500,
};

// ─── HELPERS ───────────────────────────────────────────────────
function gaussianNoise(mean = 0, std = 1) {
  let u = 0, v = 0;
  while (u === 0) u = Math.random();
  while (v === 0) v = Math.random();
  return mean + std * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

// Simple 2D power spectrum via discrete Fourier (radial binning)
function computePowerSpectrum(field, size) {
  // Build 2D DFT magnitude squared, then radially bin
  const N = size;
  const power = new Array(Math.floor(N / 2)).fill(0);
  const counts = new Array(Math.floor(N / 2)).fill(0);

  // We use a fast approximation: row-wise cosine correlation at each k
  for (let ky = 0; ky < N; ky++) {
    for (let kx = 0; kx < N; kx++) {
      let re = 0, im = 0;
      for (let y = 0; y < N; y++) {
        for (let x = 0; x < N; x++) {
          const angle = 2 * Math.PI * (kx * x + ky * y) / N;
          re += field[y * N + x] * Math.cos(angle);
          im -= field[y * N + x] * Math.sin(angle);
        }
      }
      const mag2 = (re * re + im * im) / (N * N);
      const k = Math.round(Math.sqrt(
        Math.min(kx, N - kx) ** 2 + Math.min(ky, N - ky) ** 2
      ));
      if (k < Math.floor(N / 2)) {
        power[k] += mag2;
        counts[k]++;
      }
    }
  }
  return power.map((p, i) => counts[i] > 0 ? p / counts[i] : 0);
}

// ── Cooley-Tukey FFT (1D, in-place, radix-2) ─────────────────
function fft1d(re, im) {
  const N = re.length;
  // Bit-reversal permutation
  let j = 0;
  for (let i = 1; i < N; i++) {
    let bit = N >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      [re[i], re[j]] = [re[j], re[i]];
      [im[i], im[j]] = [im[j], im[i]];
    }
  }
  // Butterfly passes
  for (let len = 2; len <= N; len <<= 1) {
    const ang = -2 * Math.PI / len;
    const wRe = Math.cos(ang), wIm = Math.sin(ang);
    for (let i = 0; i < N; i += len) {
      let curRe = 1, curIm = 0;
      for (let k = 0; k < len / 2; k++) {
        const uRe = re[i+k], uIm = im[i+k];
        const vRe = re[i+k+len/2]*curRe - im[i+k+len/2]*curIm;
        const vIm = re[i+k+len/2]*curIm + im[i+k+len/2]*curRe;
        re[i+k] = uRe+vRe; im[i+k] = uIm+vIm;
        re[i+k+len/2] = uRe-vRe; im[i+k+len/2] = uIm-vIm;
        const newRe = curRe*wRe - curIm*wIm;
        curIm = curRe*wIm + curIm*wRe;
        curRe = newRe;
      }
    }
  }
}

// ── 2D FFT via row+column 1D FFTs ─────────────────────────────
function fft2d(field, N) {
  const re = new Float64Array(field);
  const im = new Float64Array(N * N);

  // Row FFTs
  for (let y = 0; y < N; y++) {
    const rowRe = re.subarray(y*N, y*N+N);
    const rowIm = im.subarray(y*N, y*N+N);
    fft1d(rowRe, rowIm);
  }
  // Column FFTs
  for (let x = 0; x < N; x++) {
    const colRe = new Float64Array(N);
    const colIm = new Float64Array(N);
    for (let y = 0; y < N; y++) { colRe[y] = re[y*N+x]; colIm[y] = im[y*N+x]; }
    fft1d(colRe, colIm);
    for (let y = 0; y < N; y++) { re[y*N+x] = colRe[y]; im[y*N+x] = colIm[y]; }
  }
  return { re, im };
}

// ── Radiaal gemiddeld power spectrum uit 2D FFT ───────────────
function computePowerSpectrumFast(field, size) {
  const N = size;
  const halfN = Math.floor(N / 2);

  const { re, im } = fft2d(field, N);

  const power = new Float64Array(halfN);
  const counts = new Float32Array(halfN);

  for (let y = 0; y < N; y++) {
    for (let x = 0; x < N; x++) {
      // FFT-frequentie gecentreerd (fftshift equivalent)
      const fx = x < halfN ? x : x - N;
      const fy = y < halfN ? y : y - N;
      const k = Math.round(Math.sqrt(fx*fx + fy*fy));
      if (k > 0 && k < halfN) {
        const idx = y*N+x;
        power[k] += (re[idx]*re[idx] + im[idx]*im[idx]) / (N*N);
        counts[k]++;
      }
    }
  }
  return Array.from(power).map((p, i) => counts[i] > 0 ? p / counts[i] : 0);
}

// ─── SIMULATION CORE ───────────────────────────────────────────
class TITKUniverse {
  constructor(gridSize) {
    this.G = gridSize;
    this.N = gridSize * gridSize;
    this.cycle = 0;
    this.phase = "singularity"; // singularity → inflation → plasma → decoupling → cmb

    // Fields
    this.sigma = new Float32Array(this.N);      // public information state
    this.sigmaInt = new Float32Array(this.N);   // internal state
    this.tEff = new Float32Array(this.N);       // internal processing cost
    this.phiExt = new Float32Array(this.N);     // external throughput
    this.iConn = new Uint8Array(this.N);        // connectivity
    this.saturated = new Uint8Array(this.N);    // black hole flag

    this.cmbSnapshot = null;
    this.powerSpectrum = null;

    this._initSingularity();
  }

  _idx(x, y) {
    const G = this.G;
    return ((y + G) % G) * G + ((x + G) % G);
  }

  _initSingularity() {
    // Big Bang: all information compressed into centre — maximum density
    const G = this.G;
    const cx = G / 2, cy = G / 2;

    // ── Stap 1: 1/f Harrison-Zel'dovich ruis op meerdere schalen ──
    // Amplitude ∝ 1/k — grote schalen domineren, kleine schalen geven structuur
    const noiseField = new Float32Array(G * G);
    const numOctaves = 7;
    for (let oct = 0; oct < numOctaves; oct++) {
      const freq = Math.pow(2, oct + 1);        // k = 2,4,8,16,32,64,128
      const amplitude = 1.0 / freq;             // 1/k gewicht
      const phaseX = Math.random() * Math.PI * 2;
      const phaseY = Math.random() * Math.PI * 2;
      const phaseXY = Math.random() * Math.PI * 2;
      for (let y = 0; y < G; y++) {
        for (let x = 0; x < G; x++) {
          // Meerdere sinusgolven per octaaf voor isotropie
          const wave =
            Math.sin(freq * Math.PI * 2 * x / G + phaseX) *
            Math.cos(freq * Math.PI * 2 * y / G + phaseY) +
            Math.sin(freq * Math.PI * 2 * (x + y) / G + phaseXY) * 0.5;
          noiseField[y * G + x] += amplitude * wave;
        }
      }
    }

    // Normaliseer ruisveld naar [0,1]
    let nMin = Infinity, nMax = -Infinity;
    for (let i = 0; i < G * G; i++) {
      if (noiseField[i] < nMin) nMin = noiseField[i];
      if (noiseField[i] > nMax) nMax = noiseField[i];
    }
    const nRange = nMax - nMin || 1;
    for (let i = 0; i < G * G; i++) {
      noiseField[i] = (noiseField[i] - nMin) / nRange;
    }

    // ── Stap 2: Meerdere primordiale zaaikernen (kwantumfluctuaties) ──
    const numSeeds = 6 + Math.floor(Math.random() * 4); // 6-9 kernen
    const seeds = [];
    for (let s = 0; s < numSeeds; s++) {
      seeds.push({
        x: G * (0.2 + Math.random() * 0.6),
        y: G * (0.2 + Math.random() * 0.6),
        strength: 0.4 + Math.random() * 0.6,
        width: 0.04 + Math.random() * 0.08,
      });
    }
    // Altijd één centrale kern — de dominante singulariteit
    seeds.push({ x: cx, y: cy, strength: 1.0, width: 0.12 });

    // ── Stap 3: Combineer kernen + 1/f ruis ──────────────────────
    for (let y = 0; y < G; y++) {
      for (let x = 0; x < G; x++) {
        const i = y * G + x;

        // Bijdrage van alle zaaikernens
        let seedVal = 0;
        for (const seed of seeds) {
          const dx = (x - seed.x) / G;
          const dy = (y - seed.y) / G;
          const r2 = dx * dx + dy * dy;
          seedVal += seed.strength * Math.exp(-r2 / (2 * seed.width * seed.width));
        }
        seedVal = Math.min(1, seedVal);

        // 1/f ruis als primordiaal perturbatieveld
        const primordialNoise = noiseField[i] * CFG.NOISE_AMP * 2.5;

        // Gaussische achtergrond-perturbatie (sub-dominant)
        const bgNoise = gaussianNoise(0, CFG.NOISE_AMP * 0.3);

        this.sigma[i] = Math.max(0, Math.min(1,
          seedVal * 0.7 + primordialNoise * 0.25 + bgNoise * 0.05
        ));
        this.phiExt[i] = CFG.W_MAX;
        this.tEff[i] = 0;
      }
    }
  }

  step() {
    const G = this.G;
    this.cycle++;

    // Determine phase
    if (this.cycle < 20) this.phase = "singularity";
    else if (this.cycle < 80) this.phase = "inflation";
    else if (this.cycle < CFG.DECOUPLING_CYCLE) this.phase = "plasma";
    else if (this.cycle === CFG.DECOUPLING_CYCLE) this.phase = "decoupling";
    else this.phase = "cmb";

    // Expansion factor (inflation drives rapid spatial spreading)
    const expansionRate = this.phase === "inflation" ? 0.08
      : this.phase === "plasma" ? 0.004
      : 0.002;

    // ── 1. Connectivity (I_conn) ──────────────────────────────
    const radius = Math.max(2, Math.floor(CFG.C_RADIUS * G));

    for (let y = 0; y < G; y++) {
      for (let x = 0; x < G; x++) {
        const i = y * G + x;
        let conn = 0;
        let neighborSum = 0;
        let count = 0;

        for (let dy = -radius; dy <= radius; dy++) {
          for (let dx = -radius; dx <= radius; dx++) {
            if (dx === 0 && dy === 0) continue;
            const d = Math.sqrt(dx * dx + dy * dy);
            if (d <= radius) {
              const ni = this._idx(x + dx, y + dy);
              neighborSum += this.sigma[ni];
              count++;
              conn++;
            }
          }
        }

        this.iConn[i] = conn;

        // ── 2. T_eff (interne verwerkingskosten) ──────────────
        const avgNeighbor = count > 0 ? neighborSum / count : 0;
        const delta = Math.abs(this.sigma[i] - avgNeighbor);
        const baseCost = CFG.K_FACTOR * delta * Math.max(1, conn * 0.3);

        // Time dilation: density contribution
        const densityBoost = this.sigma[i] * conn * 0.5;
        this.tEff[i] = Math.min(CFG.W_MAX, baseCost + densityBoost);

        // ── 3. Queue depth → saturatie (zwart gat) ────────────
        // Terugkoppeling: drukgolf van verzadigde buren
        let saturatedNeighbors = 0;
        for (let dy2 = -radius; dy2 <= radius; dy2++) {
          for (let dx2 = -radius; dx2 <= radius; dx2++) {
            if (dx2 === 0 && dy2 === 0) continue;
            if (Math.sqrt(dx2*dx2+dy2*dy2) <= radius) {
              if (this.saturated[this._idx(x+dx2, y+dy2)]) saturatedNeighbors++;
            }
          }
        }
        // Buurman van verzadigd node krijgt extra verwerkingslast — akoestische terugkaatsing
        const backpressure = saturatedNeighbors * (CFG.W_MAX / CFG.Q_MAX) * 0.75;
        this.tEff[i] = Math.min(CFG.W_MAX, this.tEff[i] + backpressure);

        const queueDepth = Math.floor(this.tEff[i] / (CFG.W_MAX / CFG.Q_MAX));
        if (queueDepth >= CFG.Q_MAX || this.tEff[i] >= CFG.W_MAX) {
          this.saturated[i] = 1;
          this.phiExt[i] = 0;
          this.sigmaInt[i] = this.sigma[i]; // frozen
        } else {
          this.saturated[i] = 0;
          this.phiExt[i] = Math.max(0, CFG.W_MAX - this.tEff[i]);

          // Weighted neighbor average for sigma_int
          if (count > 0) {
            let wSum = 0, wTotal = 0;
            for (let dy = -radius; dy <= radius; dy++) {
              for (let dx = -radius; dx <= radius; dx++) {
                if (dx === 0 && dy === 0) continue;
                const d = Math.sqrt(dx * dx + dy * dy);
                if (d <= radius) {
                  const ni = this._idx(x + dx, y + dy);
                  const w = Math.max(1, this.iConn[ni] * 0.5);
                  wSum += this.sigma[ni] * w;
                  wTotal += w;
                }
              }
            }
            this.sigmaInt[i] = wSum / wTotal;
          }
        }
      }
    }

    // ── 4. Publish state ──────────────────────────────────────
    for (let i = 0; i < this.N; i++) {
      if (!this.saturated[i]) {
        // Expansion: diffuse information outward (universe expands)
        this.sigma[i] = this.sigma[i] * (1 - expansionRate)
          + this.sigmaInt[i] * expansionRate;

        // Tiny quantum noise (not destructive — perturbation only)
        if (Math.random() < 0.005) {
          this.sigma[i] = Math.max(0, Math.min(1,
            this.sigma[i] + gaussianNoise(0, 0.02)
          ));
        }
      }
      // Saturated nodes: sigma frozen
    }

    // ── 5. CMB snapshot at decoupling ────────────────────────
    if (this.cycle === CFG.DECOUPLING_CYCLE) {
      this.cmbSnapshot = new Float32Array(this.sigma);
      // 128x128 — volledig grid, geen subsample-verlies meer
      // Echte Cooley-Tukey FFT: O(N² log N) ipv O(N⁴)
      const sub = this._subsampleAvg(this.sigma, G, 128);
      let mean = 0;
      for (let i = 0; i < sub.length; i++) mean += sub[i];
      mean /= sub.length;
      for (let i = 0; i < sub.length; i++) sub[i] -= mean;
      this.powerSpectrum = computePowerSpectrumFast(sub, 128);
    }

    return this._getStats();
  }

  _subsample(field, fromSize, toSize) {
    const ratio = fromSize / toSize;
    const out = new Float32Array(toSize * toSize);
    for (let y = 0; y < toSize; y++) {
      for (let x = 0; x < toSize; x++) {
        const sy = Math.floor(y * ratio);
        const sx = Math.floor(x * ratio);
        out[y * toSize + x] = field[sy * fromSize + sx];
      }
    }
    return out;
  }

  // Betere subsample: gemiddelde over blok ipv nearest-neighbour
  _subsampleAvg(field, fromSize, toSize) {
    const ratio = fromSize / toSize;
    const out = new Float32Array(toSize * toSize);
    for (let y = 0; y < toSize; y++) {
      for (let x = 0; x < toSize; x++) {
        let sum = 0, count = 0;
        const y0 = Math.floor(y * ratio);
        const x0 = Math.floor(x * ratio);
        const y1 = Math.min(fromSize, Math.floor((y + 1) * ratio));
        const x1 = Math.min(fromSize, Math.floor((x + 1) * ratio));
        for (let sy = y0; sy < y1; sy++) {
          for (let sx = x0; sx < x1; sx++) {
            sum += field[sy * fromSize + sx];
            count++;
          }
        }
        out[y * toSize + x] = count > 0 ? sum / count : 0;
      }
    }
    return out;
  }

  _getStats() {
    let satCount = 0, avgPhi = 0, avgSigma = 0, avgTeff = 0;
    for (let i = 0; i < this.N; i++) {
      if (this.saturated[i]) satCount++;
      avgPhi += this.phiExt[i];
      avgSigma += this.sigma[i];
      avgTeff += this.tEff[i];
    }
    return {
      cycle: this.cycle,
      phase: this.phase,
      satCount,
      satFrac: satCount / this.N,
      avgPhi: avgPhi / this.N,
      avgSigma: avgSigma / this.N,
      avgTeff: avgTeff / this.N,
    };
  }

  getField(type = "sigma") {
    switch (type) {
      case "sigma": return this.sigma;
      case "teff": return this.tEff;
      case "phi": return this.phiExt;
      case "cmb": return this.cmbSnapshot || this.sigma;
      default: return this.sigma;
    }
  }
}

// ─── CANVAS RENDERER ──────────────────────────────────────────
function renderField(ctx, field, size, mode, cmbSnapshot) {
  const W = ctx.canvas.width;
  const H = ctx.canvas.height;
  const cellW = W / size;
  const cellH = H / size;

  // Find min/max for normalisation
  let min = Infinity, max = -Infinity;
  for (let i = 0; i < field.length; i++) {
    if (field[i] < min) min = field[i];
    if (field[i] > max) max = field[i];
  }
  const range = max - min || 1;

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const val = (field[y * size + x] - min) / range;

      let r, g, b;
      if (mode === "cmb") {
        // CMB false-colour: blue→cyan→white→yellow→red (Planck palette)
        if (val < 0.25) {
          r = 0; g = Math.round(val * 4 * 120); b = 180 + Math.round(val * 4 * 75);
        } else if (val < 0.5) {
          const t = (val - 0.25) * 4;
          r = Math.round(t * 220); g = 120 + Math.round(t * 135); b = 255 - Math.round(t * 255);
        } else if (val < 0.75) {
          const t = (val - 0.5) * 4;
          r = 220 + Math.round(t * 35); g = 255 - Math.round(t * 100); b = 0;
        } else {
          const t = (val - 0.75) * 4;
          r = 255; g = 155 - Math.round(t * 155); b = 0;
        }
      } else {
        // Cosmic dark theme: black→deep blue→cyan→white
        if (val < 0.3) {
          r = 0; g = 0; b = Math.round(val / 0.3 * 120);
        } else if (val < 0.6) {
          const t = (val - 0.3) / 0.3;
          r = Math.round(t * 20); g = Math.round(t * 180); b = 120 + Math.round(t * 135);
        } else {
          const t = (val - 0.6) / 0.4;
          r = 20 + Math.round(t * 235); g = 180 + Math.round(t * 75); b = 255;
        }
      }

      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.fillRect(Math.floor(x * cellW), Math.floor(y * cellH),
        Math.ceil(cellW), Math.ceil(cellH));
    }
  }
}

// ─── POWER SPECTRUM CHART ─────────────────────────────────────
function PowerSpectrumChart({ spectrum, width = 300, height = 150 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!spectrum || !canvasRef.current) return;
    const ctx = canvasRef.current.getContext("2d");
    ctx.clearRect(0, 0, width, height);

    // Background
    ctx.fillStyle = "#050a14";
    ctx.fillRect(0, 0, width, height);

    // Grid lines
    ctx.strokeStyle = "rgba(100,150,255,0.1)";
    ctx.lineWidth = 1;
    for (let i = 1; i < 4; i++) {
      ctx.beginPath();
      ctx.moveTo(0, (height / 4) * i);
      ctx.lineTo(width, (height / 4) * i);
      ctx.stroke();
    }

    // CMB reference peaks (l≈200, 500, 800 — normalised to our k-space)
    const peaks = [0.18, 0.45, 0.72];
    peaks.forEach(p => {
      ctx.strokeStyle = "rgba(255,200,50,0.3)";
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(p * width, 0);
      ctx.lineTo(p * width, height);
      ctx.stroke();
      ctx.setLineDash([]);
    });

    // Label peaks
    ctx.fillStyle = "rgba(255,200,50,0.6)";
    ctx.font = "9px monospace";
    ctx.fillText("ℓ≈200", peaks[0] * width + 2, 12);
    ctx.fillText("ℓ≈500", peaks[1] * width + 2, 12);
    ctx.fillText("ℓ≈800", peaks[2] * width + 2, 12);

    // Normalise spectrum
    const usable = spectrum.slice(1, Math.floor(spectrum.length * 0.85));
    const maxP = Math.max(...usable);
    if (maxP === 0) return;

    // Smooth spectrum met 3-punt moving average voor leesbaarheid
    const smoothed = usable.map((p, i) => {
      if (i === 0 || i === usable.length - 1) return p;
      return (usable[i-1] + p + usable[i+1]) / 3;
    });

    // Draw spectrum — log-schaal op y-as voor CMB-conventie
    const logMax = Math.log1p(maxP);
    ctx.beginPath();
    ctx.strokeStyle = "#00e5ff";
    ctx.lineWidth = 2;
    smoothed.forEach((p, i) => {
      const x = (i / smoothed.length) * width;
      const logP = Math.log1p(p);
      const y = height - (logP / logMax) * (height - 10) - 5;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Glow
    ctx.shadowBlur = 8;
    ctx.shadowColor = "#00e5ff";
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Y-as label
    ctx.fillStyle = "rgba(100,150,255,0.5)";
    ctx.font = "8px monospace";
    ctx.fillText("log P(k)", 2, height - 4);

  }, [spectrum, width, height]);

  return <canvas ref={canvasRef} width={width} height={height}
    style={{ borderRadius: 4, display: "block" }} />;
}

// ─── MAIN APP ─────────────────────────────────────────────────
export default function TITKBigBang() {
  const canvasRef = useRef(null);
  const cmbCanvasRef = useRef(null);
  const simRef = useRef(null);
  const rafRef = useRef(null);
  const runningRef = useRef(false);

  const [stats, setStats] = useState(null);
  const [running, setRunning] = useState(false);
  const [viewMode, setViewMode] = useState("sigma");
  const [cmbReady, setCmbReady] = useState(false);
  const [powerSpectrum, setPowerSpectrum] = useState(null);
  const [history, setHistory] = useState([]);

  const GRID = CFG.GRID;

  const drawField = useCallback((field, canvasRef, mode) => {
    if (!canvasRef.current) return;
    const ctx = canvasRef.current.getContext("2d");
    renderField(ctx, field, GRID, mode, null);
  }, [GRID]);

  const tick = useCallback(() => {
    if (!simRef.current || !runningRef.current) return;

    const s = simRef.current.step();
    setStats(s);

    setHistory(h => {
      const next = [...h, {
        cycle: s.cycle,
        avgSigma: s.avgSigma,
        avgTeff: s.avgTeff,
        satFrac: s.satFrac,
      }];
      return next.length > 500 ? next.slice(-500) : next;
    });

    // Draw main field
    const field = simRef.current.getField(viewMode);
    drawField(field, canvasRef, viewMode === "cmb" ? "cmb" : "cosmic");

    // CMB snapshot
    if (s.cycle >= CFG.DECOUPLING_CYCLE && simRef.current.cmbSnapshot) {
      setCmbReady(true);
      setPowerSpectrum(simRef.current.powerSpectrum);
      if (cmbCanvasRef.current) {
        const ctx = cmbCanvasRef.current.getContext("2d");
        renderField(ctx, simRef.current.cmbSnapshot, GRID, "cmb", null);
      }
    }

    if (s.cycle < CFG.TOTAL_CYCLES) {
      rafRef.current = requestAnimationFrame(tick);
    } else {
      runningRef.current = false;
      setRunning(false);
    }
  }, [viewMode, drawField, GRID]);

  const handleStart = useCallback(() => {
    simRef.current = new TITKUniverse(GRID);
    setCmbReady(false);
    setPowerSpectrum(null);
    setHistory([]);
    setStats(null);
    runningRef.current = true;
    setRunning(true);
    rafRef.current = requestAnimationFrame(tick);
  }, [tick, GRID]);

  const handleStop = useCallback(() => {
    runningRef.current = false;
    setRunning(false);
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
  }, []);

  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  const phaseColor = {
    singularity: "#ff4444",
    inflation: "#ff9900",
    plasma: "#ffcc00",
    decoupling: "#00ffaa",
    cmb: "#00aaff",
  };

  const phaseLabel = {
    singularity: "⚫ SINGULARITEIT",
    inflation: "💥 INFLATIE",
    plasma: "🌡 PLASMA-ERA",
    decoupling: "✨ ONTKOPPELING",
    cmb: "🌌 CMB-ERA",
  };

  return (
    <div style={{
      background: "#020810",
      minHeight: "100vh",
      color: "#c8d8f0",
      fontFamily: "'Courier New', monospace",
      padding: "20px",
      boxSizing: "border-box",
    }}>
      {/* Header */}
      <div style={{ marginBottom: 20, borderBottom: "1px solid rgba(100,150,255,0.2)", paddingBottom: 16 }}>
        <div style={{ fontSize: 11, color: "#4466aa", letterSpacing: 4, marginBottom: 4 }}>
          TOPOLOGISCHE INFORMATIETHEORIE VAN DE KOSMOS
        </div>
        <div style={{ fontSize: 22, fontWeight: "bold", color: "#e0eeff", letterSpacing: 2 }}>
          BIG BANG SIMULATIE v1.4
        </div>
        <div style={{ fontSize: 11, color: "#335577", marginTop: 4 }}>
          CMB POWER SPECTRUM TEST — INFORMATIEDICHTHEID ALS TEMPERATUUR
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap", alignItems: "center" }}>
        <button onClick={running ? handleStop : handleStart}
          style={{
            padding: "8px 20px",
            background: running ? "#440000" : "#003322",
            border: `1px solid ${running ? "#ff4444" : "#00cc77"}`,
            color: running ? "#ff6666" : "#00ee88",
            cursor: "pointer",
            fontFamily: "monospace",
            fontSize: 12,
            letterSpacing: 2,
          }}>
          {running ? "■ STOP" : "▶ START BIG BANG"}
        </button>

        {["sigma", "teff", "phi"].map(m => (
          <button key={m} onClick={() => setViewMode(m)}
            style={{
              padding: "6px 12px",
              background: viewMode === m ? "#001830" : "transparent",
              border: `1px solid ${viewMode === m ? "#4488cc" : "#223344"}`,
              color: viewMode === m ? "#88bbff" : "#446677",
              cursor: "pointer",
              fontFamily: "monospace",
              fontSize: 11,
            }}>
            {m === "sigma" ? "σ INFO" : m === "teff" ? "T_eff TIME" : "Φ DOORVOER"}
          </button>
        ))}
      </div>

      {/* Phase + stats bar */}
      {stats && (
        <div style={{
          display: "flex", gap: 20, marginBottom: 12,
          flexWrap: "wrap", fontSize: 11,
        }}>
          <span style={{ color: phaseColor[stats.phase] || "#fff" }}>
            {phaseLabel[stats.phase] || stats.phase}
          </span>
          <span>CYCLE: <strong style={{ color: "#fff" }}>{stats.cycle}</strong>/{CFG.TOTAL_CYCLES}</span>
          <span>ZWARTE GATEN: <strong style={{ color: "#ff6644" }}>
            {(stats.satFrac * 100).toFixed(1)}%
          </strong></span>
          <span>AVG σ: <strong style={{ color: "#88ddff" }}>{stats.avgSigma.toFixed(4)}</strong></span>
          <span>AVG T_eff: <strong style={{ color: "#ffcc44" }}>{stats.avgTeff.toFixed(1)}</strong></span>
          <span>AVG Φ: <strong style={{ color: "#44ff88" }}>{stats.avgPhi.toFixed(1)}</strong></span>
        </div>
      )}

      {/* Progress bar */}
      {stats && (
        <div style={{
          height: 3, background: "#0a1520", marginBottom: 16,
          borderRadius: 2, overflow: "hidden",
        }}>
          <div style={{
            height: "100%",
            width: `${(stats.cycle / CFG.TOTAL_CYCLES) * 100}%`,
            background: `linear-gradient(90deg, #003388, ${phaseColor[stats.phase] || "#4488ff"})`,
            transition: "width 0.1s",
          }} />
        </div>
      )}

      {/* Main visuals */}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>

        {/* Live simulation */}
        <div style={{ flex: "1 1 300px" }}>
          <div style={{ fontSize: 10, color: "#446688", marginBottom: 6, letterSpacing: 2 }}>
            LIVE — {viewMode === "sigma" ? "INFORMATIEDICHTHEID" :
              viewMode === "teff" ? "TIJDVERTRAGING (T_eff)" : "DOORVOER (Φ_ext)"}
          </div>
          <canvas ref={canvasRef} width={GRID} height={GRID}
            style={{
              width: "100%", imageRendering: "pixelated",
              border: "1px solid rgba(100,150,255,0.15)",
              display: "block",
            }} />
        </div>

        {/* CMB snapshot */}
        <div style={{ flex: "1 1 300px" }}>
          <div style={{ fontSize: 10, color: "#446688", marginBottom: 6, letterSpacing: 2 }}>
            CMB SNAPSHOT — ONTKOPPELING op cycle {CFG.DECOUPLING_CYCLE}
            {cmbReady && <span style={{ color: "#00cc66", marginLeft: 8 }}>✓ BEVROREN</span>}
          </div>
          <canvas ref={cmbCanvasRef} width={GRID} height={GRID}
            style={{
              width: "100%", imageRendering: "pixelated",
              border: `1px solid ${cmbReady ? "rgba(0,200,100,0.3)" : "rgba(100,150,255,0.15)"}`,
              display: "block",
              opacity: cmbReady ? 1 : 0.3,
            }} />
          {!cmbReady && (
            <div style={{ fontSize: 10, color: "#335577", marginTop: 4 }}>
              Wacht op cycle {CFG.DECOUPLING_CYCLE}...
            </div>
          )}
        </div>
      </div>

      {/* Power Spectrum */}
      {powerSpectrum && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 10, color: "#446688", marginBottom: 6, letterSpacing: 2 }}>
            POWER SPECTRUM — TITK vs CMB REFERENTIEPIEKEN (gele lijnen: ℓ≈200, 500, 800)
          </div>
          <PowerSpectrumChart spectrum={powerSpectrum} width={620} height={140} />
          <div style={{ fontSize: 10, color: "#334455", marginTop: 4 }}>
            Als TITK-pieken samenvallen met gele lijnen → CMB-overeenkomst gevonden
          </div>
        </div>
      )}

      {/* Mini timeline chart */}
      {history.length > 10 && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 10, color: "#446688", marginBottom: 6, letterSpacing: 2 }}>
            HISTORIEK — σ (blauw) · T_eff (geel) · Zwarte Gaten % (rood)
          </div>
          <TimelineChart history={history} width={620} height={80} />
        </div>
      )}

      {/* Footer */}
      <div style={{
        marginTop: 24, paddingTop: 12,
        borderTop: "1px solid rgba(100,150,255,0.1)",
        fontSize: 10, color: "#223344",
        display: "flex", gap: 20, flexWrap: "wrap",
      }}>
        <span>GRID: {GRID}×{GRID} = {GRID * GRID} nodes</span>
        <span>Q_MAX: {CFG.Q_MAX}</span>
        <span>W_MAX: {CFG.W_MAX}</span>
        <span>ONTKOPPELING: cycle {CFG.DECOUPLING_CYCLE}</span>
        <span>TITK v1.4 — hobbyproject</span>
      </div>
    </div>
  );
}

// ─── TIMELINE CHART ───────────────────────────────────────────
function TimelineChart({ history, width, height }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || history.length < 2) return;
    const ctx = canvasRef.current.getContext("2d");
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#050a14";
    ctx.fillRect(0, 0, width, height);

    const drawLine = (key, color, scale = 1) => {
      ctx.beginPath();
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      history.forEach((d, i) => {
        const x = (i / (history.length - 1)) * width;
        const val = Math.min(1, d[key] * scale);
        const y = height - val * (height - 4) - 2;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.stroke();
    };

    drawLine("avgSigma", "rgba(0,180,255,0.8)", 1);
    drawLine("avgTeff", "rgba(255,200,0,0.7)", 1 / CFG.W_MAX);
    drawLine("satFrac", "rgba(255,80,50,0.8)", 1);

    // Decoupling marker
    const decIdx = history.findIndex(d => d.cycle >= CFG.DECOUPLING_CYCLE);
    if (decIdx > 0) {
      const x = (decIdx / (history.length - 1)) * width;
      ctx.strokeStyle = "rgba(0,255,150,0.4)";
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(x, 0); ctx.lineTo(x, height);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "rgba(0,255,150,0.6)";
      ctx.font = "9px monospace";
      ctx.fillText("CMB", x + 2, 12);
    }
  }, [history, width, height]);

  return <canvas ref={canvasRef} width={width} height={height}
    style={{ borderRadius: 4, display: "block" }} />;
}
