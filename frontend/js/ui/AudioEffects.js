/**
 * AI Adaptive Traffic Signal Digital Twin - Procedural Web Audio Sound Effects
 */

export class AudioEffects {
  constructor() {
    this.enabled = false;
    this.ctx = null;
  }

  init() {
    if (!this.ctx && typeof window !== 'undefined') {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
  }

  toggle() {
    this.enabled = !this.enabled;
    if (this.enabled) {
      this.init();
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
      this.playBeep(880, 0.08, 'sine');
    }
    return this.enabled;
  }

  playBeep(freq = 440, duration = 0.08, type = 'sine', gainVal = 0.04) {
    if (!this.enabled || !this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      gain.gain.setValueAtTime(gainVal, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch (e) {
      // Audio autoplay or permissions handled gracefully
    }
  }

  playSignalChange() {
    this.playBeep(520, 0.06, 'triangle', 0.03);
  }

  playSignalSwitch() {
    this.playBeep(580, 0.05, 'sine', 0.025);
  }

  playAiDecision() {
    if (!this.enabled || !this.ctx) return;
    this.playBeep(660, 0.05, 'sine', 0.02);
    setTimeout(() => this.playBeep(990, 0.08, 'sine', 0.03), 60);
  }

  playEmergencySiren() {
    if (!this.enabled || !this.ctx) return;
    this.playBeep(850, 0.14, 'sawtooth', 0.045);
    setTimeout(() => this.playBeep(650, 0.14, 'sawtooth', 0.045), 140);
  }

  playAccidentAlarm() {
    if (!this.enabled || !this.ctx) return;
    this.playBeep(920, 0.1, 'square', 0.05);
    setTimeout(() => this.playBeep(440, 0.18, 'sawtooth', 0.06), 110);
  }
}

