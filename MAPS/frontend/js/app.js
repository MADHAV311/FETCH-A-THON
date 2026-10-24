/**
 * TrafficFlow-MAPS: Frontend Application Coordinator
 * Coordinates 60 FPS Canvas rendering, 25 Hz state polling,
 * navigation mode switching (Map View vs Dedicated ASI:One Chat View),
 * and location-aware traffic intelligence querying.
 */

import { ApiClient } from './api/ApiClient.js';
import { MapRenderer } from './rendering/MapRenderer.js';

class MapsApp {
  constructor() {
    this.api = new ApiClient();
    this.canvas = document.getElementById('map-canvas');
    this.renderer = new MapRenderer(this.canvas);

    this.latestState = null;
    this.soundEnabled = true;
    this.audioCtx = null;
    this.chimePlayed = false;
    this.activeView = 'navigation'; // 'navigation' or 'chat'

    this.cacheElements();
    this.bindEvents();
    this.startStatePolling();
    this.startRenderLoop();
  }

  cacheElements() {
    // Mode Switcher Tabs
    this.tabNavView = document.getElementById('tab-nav-view');
    this.tabChatView = document.getElementById('tab-chat-view');
    this.viewNav = document.getElementById('view-navigation');
    this.viewChat = document.getElementById('view-chat');
    this.btnExpandChat = document.getElementById('btn-expand-chat');

    // Controls
    this.btnPlayPause = document.getElementById('btn-play-pause');
    this.playIcon = document.getElementById('play-icon');
    this.playText = document.getElementById('play-text');
    this.btnReset = document.getElementById('btn-reset');
    this.selectSpeed = document.getElementById('select-speed');
    this.btnSoundToggle = document.getElementById('btn-sound-toggle');
    this.soundIcon = document.getElementById('sound-icon');

    // Turn Card
    this.turnCard = document.getElementById('turn-card');
    this.turnIcon = document.getElementById('turn-icon');
    this.turnDistance = document.getElementById('turn-distance');
    this.turnInstruction = document.getElementById('turn-instruction');
    this.etaTime = document.getElementById('eta-time');
    this.etaDist = document.getElementById('eta-dist');

    // Alert Banner
    this.proactiveBanner = document.getElementById('proactive-banner');
    this.btnAccept = document.getElementById('btn-accept-reroute');
    this.btnReject = document.getElementById('btn-reject-reroute');

    // Speed HUD
    this.hudSpeed = document.getElementById('hud-speed');
    this.hudStatus = document.getElementById('hud-status');
    this.hudRouteName = document.getElementById('hud-route-name');

    // Economic Stats
    this.statDelaySaved = document.getElementById('stat-delay-saved');
    this.statFuelSaved = document.getElementById('stat-fuel-saved');
    this.statTripSavings = document.getElementById('stat-trip-savings');
    this.statAnnualLakhs = document.getElementById('stat-annual-lakhs');

    // Side Chat Drawer
    this.chatFormSide = document.getElementById('chat-form-side');
    this.chatInputSide = document.getElementById('chat-input-side');
    this.chatMessagesSide = document.getElementById('chat-messages-side');
    this.promptPills = document.querySelectorAll('.prompt-pill');

    // Dedicated Full Chat View Elements
    this.chatFormFull = document.getElementById('chat-form-full');
    this.chatInputFull = document.getElementById('chat-input-full');
    this.chatMessagesFull = document.getElementById('chat-messages-full');
    this.locChips = document.querySelectorAll('.loc-chip');
    this.actionBtns = document.querySelectorAll('.action-btn');
  }

  bindEvents() {
    // Mode View Navigation Switching
    this.tabNavView.addEventListener('click', () => this.switchView('navigation'));
    this.tabChatView.addEventListener('click', () => this.switchView('chat'));
    if (this.btnExpandChat) {
      this.btnExpandChat.addEventListener('click', () => this.switchView('chat'));
    }

    // Play/Pause
    this.btnPlayPause.addEventListener('click', async () => {
      if (!this.latestState) return;
      const willPlay = !this.latestState.isPlaying;
      await this.api.sendControl(willPlay ? 'play' : 'pause');
      this.playIcon.textContent = willPlay ? '⏸️' : '▶️';
      this.playText.textContent = willPlay ? 'Pause' : 'Play';
    });

    // Reset
    this.btnReset.addEventListener('click', async () => {
      await this.api.sendControl('reset');
      this.chimePlayed = false;
      this.proactiveBanner.style.display = 'none';
      this.broadcastChat('agent', 'Journey reset. Vehicle restarted at Koramangala 4th Block.');
    });

    // Speed
    this.selectSpeed.addEventListener('change', async (e) => {
      await this.api.sendControl('speed', { speed: parseFloat(e.target.value) });
    });

    // Sound Toggle
    this.btnSoundToggle.addEventListener('click', () => {
      this.soundEnabled = !this.soundEnabled;
      this.soundIcon.textContent = this.soundEnabled ? '🔊' : '🔇';
      this.btnSoundToggle.textContent = `${this.soundIcon.textContent} Sound: ${this.soundEnabled ? 'ON' : 'OFF'}`;
    });

    // Proactive Alert Actions
    this.btnAccept.addEventListener('click', async () => {
      const res = await this.api.acceptReroute();
      this.proactiveBanner.style.display = 'none';
      this.broadcastChat('user', 'Accepted proactive reroute!');
      this.broadcastChat('agent', 'Reroute confirmed: Taking 8th Cross Green Wave Bypass. Saving 6.2 mins & 0.42L fuel!');
    });

    this.btnReject.addEventListener('click', async () => {
      const res = await this.api.rejectReroute();
      this.proactiveBanner.style.display = 'none';
      this.broadcastChat('user', 'Staying on default route.');
      this.broadcastChat('agent', 'Acknowledged. Vehicle approaching Central Junction red signal queue.');
    });

    // Side Chat Drawer Form
    this.chatFormSide.addEventListener('submit', async (e) => {
      e.preventDefault();
      const msg = this.chatInputSide.value.trim();
      if (!msg) return;
      this.chatInputSide.value = '';
      await this.handleUserQuery(msg);
    });

    // Full Chat View Form
    this.chatFormFull.addEventListener('submit', async (e) => {
      e.preventDefault();
      const msg = this.chatInputFull.value.trim();
      if (!msg) return;
      this.chatInputFull.value = '';
      await this.handleUserQuery(msg);
    });

    // Side quick prompt pills
    this.promptPills.forEach(pill => {
      pill.addEventListener('click', async () => {
        const query = pill.getAttribute('data-query');
        await this.handleUserQuery(query);
      });
    });

    // Location Hotspots Chips in Full Chat
    this.locChips.forEach(chip => {
      chip.addEventListener('click', async () => {
        const query = chip.getAttribute('data-query');
        await this.handleUserQuery(query);
      });
    });

    // Action buttons in Full Chat
    this.actionBtns.forEach(btn => {
      btn.addEventListener('click', async () => {
        const query = btn.getAttribute('data-query');
        await this.handleUserQuery(query);
      });
    });
  }

  switchView(viewName) {
    this.activeView = viewName;
    if (viewName === 'navigation') {
      this.tabNavView.classList.add('active-tab');
      this.tabChatView.classList.remove('active-tab');
      this.viewNav.style.display = 'block';
      this.viewChat.style.display = 'none';
      this.renderer.resize();
    } else {
      this.tabNavView.classList.remove('active-tab');
      this.tabChatView.classList.add('active-tab');
      this.viewNav.style.display = 'none';
      this.viewChat.style.display = 'flex';
      this.chatMessagesFull.scrollTop = this.chatMessagesFull.scrollHeight;
    }
  }

  async handleUserQuery(queryText) {
    this.broadcastChat('user', queryText);

    try {
      const res = await this.api.sendChat(queryText);
      this.broadcastChat('agent', res.agentReply);
    } catch (err) {
      this.broadcastChat('agent', '⚠️ Network error communicating with Fetch.ai Agentverse Almanac.');
    }
  }

  broadcastChat(sender, text) {
    const formatted = this.formatMarkdown(text);

    // 1. Append to side drawer chat
    if (this.chatMessagesSide) {
      const sideBubble = document.createElement('div');
      sideBubble.className = `chat-bubble ${sender}-bubble`;
      sideBubble.innerHTML = `<strong>${sender === 'user' ? 'You' : 'ASI:One Copilot'}:</strong> <p>${formatted}</p>`;
      this.chatMessagesSide.appendChild(sideBubble);
      this.chatMessagesSide.scrollTop = this.chatMessagesSide.scrollHeight;
    }

    // 2. Append to full chat stream
    if (this.chatMessagesFull) {
      const fullBubble = document.createElement('div');
      fullBubble.className = `chat-bubble ${sender}-bubble full-bubble`;
      const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      fullBubble.innerHTML = `
        <div class="bubble-header">
          <span class="bubble-author">${sender === 'user' ? '👤 Driver (Commuter KA-01-MJ-8821)' : '🤖 ASI:One Autonomous Agent (@trafficflow-maps)'}</span>
          <span class="bubble-time">${timeStr}</span>
        </div>
        <div class="bubble-content">
          ${formatted}
        </div>
      `;
      this.chatMessagesFull.appendChild(fullBubble);
      this.chatMessagesFull.scrollTop = this.chatMessagesFull.scrollHeight;
    }
  }

  formatMarkdown(str) {
    if (!str) return '';
    return str
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
  }

  playNavChime() {
    if (!this.soundEnabled) return;
    try {
      if (!this.audioCtx) {
        this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      const now = this.audioCtx.currentTime;

      const osc1 = this.audioCtx.createOscillator();
      const gain1 = this.audioCtx.createGain();
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(587.33, now); // D5
      gain1.gain.setValueAtTime(0.15, now);
      gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
      osc1.connect(gain1);
      gain1.connect(this.audioCtx.destination);
      osc1.start(now);
      osc1.stop(now + 0.35);

      const osc2 = this.audioCtx.createOscillator();
      const gain2 = this.audioCtx.createGain();
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(880.00, now + 0.12); // A5
      gain2.gain.setValueAtTime(0.18, now + 0.12);
      gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.55);
      osc2.connect(gain2);
      gain2.connect(this.audioCtx.destination);
      osc2.start(now + 0.12);
      osc2.stop(now + 0.55);
    } catch (e) {
      // Audio policy
    }
  }

  startStatePolling() {
    const poll = async () => {
      try {
        this.latestState = await this.api.getState();
        this.updateUI(this.latestState);
      } catch (e) {
        // server busy or starting
      }
      setTimeout(poll, 40); // 25 Hz
    };
    poll();
  }

  updateUI(state) {
    if (!state) return;

    // 1. Check Alert Banner Trigger
    const nav = state.navigation;
    if (nav.alertTriggered && nav.rerouteDecision === 'PENDING') {
      if (this.proactiveBanner.style.display !== 'block') {
        this.proactiveBanner.style.display = 'block';
        if (!this.chimePlayed) {
          this.playNavChime();
          this.chimePlayed = true;
        }
      }
    } else {
      this.proactiveBanner.style.display = 'none';
    }

    // 2. Speedometer & Status HUD
    this.hudSpeed.textContent = Math.round(state.vehicle.speedKmh);
    const isBypass = nav.activeRouteId === 'PROACTIVE_BYPASS';
    this.hudRouteName.textContent = isBypass ? '8th Cross Bypass' : 'Direct Arterial';

    if (state.vehicle.hasReachedDestination) {
      this.hudStatus.textContent = 'ARRIVED';
      this.hudStatus.className = 'hud-val green-text';
    } else if (state.vehicle.speedKmh < 4.0) {
      this.hudStatus.textContent = 'QUEUED / IDLING';
      this.hudStatus.className = 'hud-val red-text';
    } else {
      this.hudStatus.textContent = isBypass ? 'GREEN WAVE' : 'CRUISING';
      this.hudStatus.className = 'hud-val green-text';
    }

    // 3. Turn Card
    if (isBypass) {
      this.turnIcon.textContent = '↪️';
      this.turnDistance.textContent = 'Smooth Corridor';
      this.turnInstruction.textContent = 'Cruising along 8th Cross Ring Bypass';
      this.etaTime.textContent = '8.6 min';
      this.etaDist.textContent = '4.8 km';
    } else if (nav.rerouteDecision === 'REJECTED' || (state.vehicle.x > 360 && !isBypass)) {
      this.turnIcon.textContent = '⚠️';
      this.turnDistance.textContent = 'Standstill in 80m';
      this.turnInstruction.textContent = 'Approaching 34-car Central Junction queue';
      this.etaTime.textContent = '15.2 min';
      this.etaDist.textContent = '4.2 km';
    } else {
      this.turnIcon.textContent = '⬆️';
      this.turnDistance.textContent = 'In 150 meters';
      this.turnInstruction.textContent = '8th Cross Bypass Diversion ahead';
      this.etaTime.textContent = '15 min';
      this.etaDist.textContent = '4.2 km';
    }

    // 4. MoRTH Economic Stats
    const sav = state.advisory ? state.advisory.savings : null;
    if (sav) {
      this.statDelaySaved.textContent = `${sav.delaySavedMinutes} min`;
      this.statFuelSaved.textContent = `${sav.fuelSavedLiters} L`;
      this.statTripSavings.textContent = `₹${sav.totalTripSavingsInr}`;
      this.statAnnualLakhs.textContent = `₹${sav.annualizedCorridor.annualSavingsLakhs} L`;
    }
  }

  startRenderLoop() {
    const loop = () => {
      if (this.activeView === 'navigation') {
        this.renderer.render(this.latestState);
      }
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }
}

window.addEventListener('DOMContentLoaded', () => {
  window.mapsApp = new MapsApp();
});
