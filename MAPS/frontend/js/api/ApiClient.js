/**
 * TrafficFlow-MAPS: REST API Client
 */

export class ApiClient {
  constructor(baseUrl = "") {
    this.baseUrl = baseUrl;
  }

  async getState() {
    const res = await fetch(`${this.baseUrl}/api/nav/state`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }

  async acceptReroute() {
    const res = await fetch(`${this.baseUrl}/api/nav/reroute/accept`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    return await res.json();
  }

  async rejectReroute() {
    const res = await fetch(`${this.baseUrl}/api/nav/reroute/reject`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    return await res.json();
  }

  async sendControl(action, extra = {}) {
    const res = await fetch(`${this.baseUrl}/api/nav/control`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, ...extra })
    });
    return await res.json();
  }

  async sendChat(message) {
    const res = await fetch(`${this.baseUrl}/api/nav/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });
    return await res.json();
  }
}
