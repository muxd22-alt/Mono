/* ═══════════════════════════════════════════════════════════════
   Mono Signal OS — Clean & Modular Frontend Architecture
   ═══════════════════════════════════════════════════════════════ */

(function () {
    "use strict";

    // ── Configuration Module ──
    const CONFIG = window.MONO_CONFIG || {};
    const DEFAULT_REPO = CONFIG.defaultRepo || "muxd22-alt/Signal-OS";
    const PILLAR_META = CONFIG.pillars || {
        financial: { name: "Financial & Market Intelligence", emoji: "🔵", color: "#3B82F6" },
        ai: { name: "AI / Research / AGI", emoji: "🟣", color: "#A855F7" },
        saudi: { name: "Saudi Economy / Urban / Labour", emoji: "🟢", color: "#22C55E" },
        products: { name: "Products & Platforms", emoji: "🟠", color: "#F97316" },
        mobile: { name: "Mobile & Infrastructure", emoji: "🔴", color: "#EF4444" },
        news: { name: "News & Dashboards", emoji: "🟡", color: "#EAB308" },
    };

    const LANG_COLORS = {
        JavaScript: "#f1e05a", TypeScript: "#3178c6", Python: "#3572A5",
        HTML: "#e34c26", CSS: "#563d7c", Rust: "#dea584", Go: "#00ADD8",
        Shell: "#89e051", Dart: "#00B4AB", "C#": "#178600", Astro: "#ff5a03",
        Batchfile: "#C1F12E",
    };

    // ── State Management Module ──
    class StateManager {
        constructor() {
            this.state = {
                repos: [],
                digest: null,
                kb: [],
                currentView: "today",
                currentPillar: "all",
                settings: this.loadSettings(),
            };
        }

        loadSettings() {
            try {
                const stored = localStorage.getItem("mono_settings");
                return stored ? JSON.parse(stored) : { repo: DEFAULT_REPO, dataMode: "local", theme: "dark" };
            } catch {
                return { repo: DEFAULT_REPO, dataMode: "local", theme: "dark" };
            }
        }

        saveSettings(newSettings) {
            this.state.settings = { ...this.state.settings, ...newSettings };
            try {
                localStorage.setItem("mono_settings", JSON.stringify(this.state.settings));
            } catch (e) {
                console.warn("Failed to persist settings to localStorage:", e);
            }
        }

        get repo() { return this.state.settings.repo || DEFAULT_REPO; }
    }

    const AppState = new StateManager();

    // ── Data Service Module ──
    class DataService {
        static async loadAllData() {
            UI.updateStatus("Syncing...", "loading");
            try {
                const [reposData, digestData, kbData] = await Promise.allSettled([
                    DataService.fetchJSON("data/repos.json"),
                    DataService.fetchJSON("data/digest.json"),
                    DataService.fetchKB("knowledge_base.jsonl"),
                ]);

                if (reposData.status === "fulfilled" && reposData.value) {
                    AppState.state.repos = reposData.value.repos || [];
                }
                if (digestData.status === "fulfilled" && digestData.value) {
                    AppState.state.digest = digestData.value;
                }
                if (kbData.status === "fulfilled" && kbData.value) {
                    AppState.state.kb = kbData.value;
                }

                RenderEngine.renderAll();
                UI.updateSyncInfo();
                UI.updateStatus("Synced", "ok");
            } catch (err) {
                console.error("Data loading error:", err);
                UI.updateStatus("Offline", "error");
                RenderEngine.renderAll();
            }
        }

        static async fetchJSON(url) {
            const resp = await fetch(url);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
            return resp.json();
        }

        static async fetchKB(url) {
            try {
                const resp = await fetch(url);
                if (!resp.ok) return [];
                const text = await resp.text();
                return text
                    .trim()
                    .split("\n")
                    .filter(Boolean)
                    .map(line => {
                        try { return JSON.parse(line); } catch { return null; }
                    })
                    .filter(Boolean);
            } catch {
                return [];
            }
        }
    }

    // ── Render Engine Module ──
    class RenderEngine {
        static renderAll() {
            RenderEngine.renderTodayView();
            RenderEngine.renderReposView();
            RenderEngine.renderKBView();
            RenderEngine.updateCounts();
        }

        static renderTodayView() {
            const kb = AppState.state.kb;
            const now = new Date();
            const cutoff24h = new Date(now - 24 * 60 * 60 * 1000).toISOString();

            const recent24h = kb.filter(e => (e.timestamp || "") >= cutoff24h);
            const interrupts = recent24h.filter(e => (e.urgency || 0) >= 9);
            const watch = recent24h.filter(e => {
                const u = e.urgency || 0;
                return u >= 5 && u < 9;
            });

            UI.setText("stat-total", kb.length);
            UI.setText("stat-interrupts", interrupts.length);
            UI.setText("stat-watch", watch.length);

            const activeRepos = AppState.state.repos.filter(r => (r.pushed_at || "") >= cutoff24h);
            UI.setText("stat-repos-active", activeRepos.length);

            // Interrupt List
            const interruptSection = document.getElementById("interrupt-section");
            const interruptList = document.getElementById("interrupt-list");
            if (interrupts.length > 0 && interruptSection && interruptList) {
                interruptSection.style.display = "block";
                interruptList.innerHTML = interrupts.map(RenderEngine.renderEntryCard).join("");
            } else if (interruptSection) {
                interruptSection.style.display = "none";
            }

            // Watch List
            const watchSection = document.getElementById("watch-section");
            const watchList = document.getElementById("watch-list");
            if (watch.length > 0 && watchSection && watchList) {
                watchSection.style.display = "block";
                watchList.innerHTML = watch.map(RenderEngine.renderEntryCard).join("");
            } else if (watchSection) {
                watchSection.style.display = "none";
            }

            // Active Repos Chips
            const chipsEl = document.getElementById("active-repos-chips");
            if (chipsEl) {
                if (activeRepos.length > 0) {
                    chipsEl.innerHTML = activeRepos.map(r => {
                        const pillar = PILLAR_META[r.pillar] || {};
                        return `<a href="${r.url}" target="_blank" class="repo-chip">
                            <span>${pillar.emoji || "◉"}</span>
                            <span>${Utils.escapeHtml(r.name)}</span>
                        </a>`;
                    }).join("");
                } else {
                    const cutoff7d = new Date(now - 7 * 24 * 60 * 60 * 1000).toISOString();
                    const weekRepos = AppState.state.repos.filter(r => (r.pushed_at || "") >= cutoff7d).slice(0, 15);
                    if (weekRepos.length > 0) {
                        chipsEl.innerHTML = `<p style="font-size:0.75rem;color:var(--text-muted);margin-bottom:0.5rem;">No repos pushed today — showing last 7 days:</p>` +
                            weekRepos.map(r => {
                                const pillar = PILLAR_META[r.pillar] || {};
                                return `<a href="${r.url}" target="_blank" class="repo-chip">
                                    <span>${pillar.emoji || "◉"}</span>
                                    <span>${Utils.escapeHtml(r.name)}</span>
                                </a>`;
                            }).join("");
                    } else {
                        chipsEl.innerHTML = `<p style="font-size:0.8rem;color:var(--text-muted);">Waiting for repo data...</p>`;
                    }
                }
            }

            // Recent Entries
            const recentList = document.getElementById("recent-list");
            const emptyToday = document.getElementById("empty-today");
            const sorted = [...kb].sort((a, b) => (b.timestamp || "").localeCompare(a.timestamp || ""));
            const recent = sorted.slice(0, 20);

            if (recent.length > 0 && recentList && emptyToday) {
                recentList.innerHTML = recent.map(RenderEngine.renderEntryCard).join("");
                emptyToday.style.display = "none";
            } else if (emptyToday) {
                if (recentList) recentList.innerHTML = "";
                emptyToday.style.display = "block";
            }
        }

        static renderEntryCard(entry) {
            const urgency = entry.urgency || 0;
            let cardClass = "entry-card";
            let scoreClass = "score-low";

            if (urgency >= 9) {
                cardClass += " entry-interrupt";
                scoreClass = "score-high";
            } else if (urgency >= 5) {
                cardClass += " entry-watch";
                scoreClass = "score-medium";
            }

            const pillarKey = entry.pillar || "Unknown";
            const pillar = PILLAR_META[pillarKey] || { emoji: "⚪", name: pillarKey, color: "#666" };

            return `
            <div class="${cardClass}">
                <div class="entry-score">
                    <div class="entry-score-value ${scoreClass}">${urgency}</div>
                    <div class="entry-score-label">urgency</div>
                </div>
                <div class="entry-body">
                    <div class="entry-header">
                        <span class="entry-id">#${entry.id || "?"}</span>
                        <span class="entry-pillar-badge" style="background:${pillar.color}22;color:${pillar.color}">
                            ${pillar.emoji} ${pillar.name}
                        </span>
                    </div>
                    <div class="entry-summary">${Utils.escapeHtml(entry.summary || entry.content || "")}</div>
                    ${entry.reason ? `<div class="entry-reason">${Utils.escapeHtml(entry.reason)}</div>` : ""}
                    <div class="entry-meta">
                        <div class="entry-meta-scores">
                            <span class="entry-meta-score">R:${entry.relevance || 0}</span>
                            <span class="entry-meta-score">N:${entry.novelty || 0}</span>
                            <span class="entry-meta-score">U:${urgency}</span>
                        </div>
                        <span>${Utils.formatTimeAgo(entry.timestamp)}</span>
                        ${entry.issue_number ? `<a href="https://github.com/${AppState.repo}/issues/${entry.issue_number}" target="_blank" style="color:var(--color-accent);text-decoration:none;">#${entry.issue_number}</a>` : ""}
                    </div>
                </div>
            </div>`;
        }

        static renderReposView() {
            const grid = document.getElementById("repo-grid");
            const empty = document.getElementById("empty-repos");
            const filtered = RenderEngine.filterRepos();

            if (!grid || !empty) return;

            if (filtered.length === 0) {
                grid.innerHTML = "";
                empty.style.display = "block";
                return;
            }

            empty.style.display = "none";
            grid.innerHTML = filtered.map(RenderEngine.renderRepoCard).join("");
        }

        static filterRepos() {
            let repos = AppState.state.repos;
            if (AppState.state.currentPillar !== "all") {
                repos = repos.filter(r => r.pillar === AppState.state.currentPillar);
            }

            const query = (document.getElementById("search-input")?.value || "").toLowerCase();
            if (query) {
                repos = repos.filter(r =>
                    r.name.toLowerCase().includes(query) ||
                    (r.description || "").toLowerCase().includes(query) ||
                    (r.pillar_name || "").toLowerCase().includes(query) ||
                    (r.language || "").toLowerCase().includes(query)
                );
            }

            return repos;
        }

        static renderRepoCard(repo) {
            const pillar = PILLAR_META[repo.pillar] || {};
            const langColor = LANG_COLORS[repo.language] || "#666";

            let issuesHtml = "";
            if (repo.recent_issues && repo.recent_issues.length > 0) {
                issuesHtml = `<div class="repo-issues-inline">` +
                    repo.recent_issues.slice(0, 2).map(i =>
                        `<a href="${i.url}" target="_blank" class="repo-issue-chip">
                            <span class="repo-issue-num">#${i.number}</span>
                            <span class="truncate">${Utils.escapeHtml(i.title)}</span>
                        </a>`
                    ).join("") +
                    `</div>`;
            }

            return `
            <div class="repo-card" style="--repo-pillar-color: ${pillar.color || '#666'}">
                <div class="repo-card-header">
                    <div>
                        <div class="repo-name">
                            <a href="${repo.url}" target="_blank">${Utils.escapeHtml(repo.name)}</a>
                        </div>
                        <div class="repo-account">@${repo.account}</div>
                    </div>
                    ${repo.private ? `<span class="repo-private-badge">Private</span>` : ""}
                </div>
                ${repo.description ? `<div class="repo-desc">${Utils.escapeHtml(repo.description)}</div>` : ""}
                <div class="repo-stats">
                    <span class="repo-stat">
                        <span class="repo-lang-dot" style="background:${langColor}"></span>
                        ${repo.language || "Unknown"}
                    </span>
                    ${repo.stars > 0 ? `<span class="repo-stat">⭐ ${repo.stars}</span>` : ""}
                    ${repo.open_issues > 0 ? `<span class="repo-stat">🔹 ${repo.open_issues} issues</span>` : ""}
                    ${repo.fork ? `<span class="repo-stat">🔱 Fork</span>` : ""}
                </div>
                <div class="repo-pushed">Pushed ${Utils.formatTimeAgo(repo.pushed_at)}</div>
                ${issuesHtml}
            </div>`;
        }

        static renderKBView() {
            const list = document.getElementById("kb-list");
            const empty = document.getElementById("empty-kb");
            const sortBy = document.getElementById("kb-sort")?.value || "newest";
            const pillarFilter = document.getElementById("kb-pillar-filter")?.value || "all";

            if (!list || !empty) return;

            let entries = [...AppState.state.kb];

            if (pillarFilter !== "all") {
                entries = entries.filter(e => e.pillar === pillarFilter);
            }

            const query = (document.getElementById("search-input")?.value || "").toLowerCase();
            if (query) {
                entries = entries.filter(e =>
                    (e.summary || "").toLowerCase().includes(query) ||
                    (e.content || "").toLowerCase().includes(query) ||
                    (e.reason || "").toLowerCase().includes(query) ||
                    (e.pillar || "").toLowerCase().includes(query)
                );
            }

            switch (sortBy) {
                case "urgency":
                    entries.sort((a, b) => (b.urgency || 0) - (a.urgency || 0));
                    break;
                case "relevance":
                    entries.sort((a, b) => (b.relevance || 0) - (a.relevance || 0));
                    break;
                case "novelty":
                    entries.sort((a, b) => (b.novelty || 0) - (a.novelty || 0));
                    break;
                default:
                    entries.sort((a, b) => (b.timestamp || "").localeCompare(a.timestamp || ""));
            }

            if (entries.length === 0) {
                list.innerHTML = "";
                empty.style.display = "block";
                return;
            }

            empty.style.display = "none";
            list.innerHTML = entries.map(RenderEngine.renderEntryCard).join("");
        }

        static updateCounts() {
            const now = new Date();
            const cutoff24h = new Date(now - 24 * 60 * 60 * 1000).toISOString();
            const recent = AppState.state.kb.filter(e => (e.timestamp || "") >= cutoff24h);

            UI.setText("today-count", recent.length);
            UI.setText("repos-count", AppState.state.repos.length);
            UI.setText("kb-count", AppState.state.kb.length);

            const pillarCounts = {};
            AppState.state.repos.forEach(r => {
                const p = r.pillar || "unknown";
                pillarCounts[p] = (pillarCounts[p] || 0) + 1;
            });

            document.querySelectorAll("[data-pillar-count]").forEach(el => {
                const pk = el.dataset.pillarCount;
                el.textContent = pillarCounts[pk] || 0;
            });
        }
    }

    // ── UI Controller Module ──
    class UI {
        static init() {
            UI.setupNavigation();
            UI.setupSearch();
            UI.setupSettings();
            UI.setupCapture();
            UI.setupPillarTabs();
            UI.setupKBControls();
            UI.setTodayDate();

            DataService.loadAllData().then(() => {
                setTimeout(() => {
                    const loadingScreen = document.getElementById("loading-screen");
                    const app = document.getElementById("app");
                    if (loadingScreen && app) {
                        loadingScreen.classList.add("fade-out");
                        app.classList.remove("hidden");
                        setTimeout(() => {
                            app.classList.add("visible");
                            loadingScreen.style.display = "none";
                        }, 400);
                    }
                }, 1000);
            });
        }

        static setupNavigation() {
            document.querySelectorAll(".nav-item[data-view]").forEach(item => {
                item.addEventListener("click", () => {
                    UI.switchView(item.dataset.view);
                });
            });

            document.querySelectorAll(".pillar-filter").forEach(btn => {
                btn.addEventListener("click", () => {
                    AppState.state.currentPillar = btn.dataset.pillar;
                    document.querySelectorAll(".pillar-filter").forEach(b => b.classList.remove("active"));
                    btn.classList.add("active");
                    UI.switchView("repos");
                    document.querySelectorAll(".pillar-tab").forEach(t => {
                        t.classList.toggle("active", t.dataset.tab === AppState.state.currentPillar);
                    });
                    RenderEngine.renderReposView();
                });
            });
        }

        static switchView(viewName) {
            AppState.state.currentView = viewName;
            document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
            document.getElementById(`view-${viewName}`)?.classList.add("active");
            document.querySelectorAll(".nav-item[data-view]").forEach(n => {
                n.classList.toggle("active", n.dataset.view === viewName);
            });
        }

        static setupPillarTabs() {
            document.getElementById("pillar-tabs")?.addEventListener("click", e => {
                const tab = e.target.closest(".pillar-tab");
                if (!tab) return;
                AppState.state.currentPillar = tab.dataset.tab;
                document.querySelectorAll(".pillar-tab").forEach(t => t.classList.remove("active"));
                tab.classList.add("active");
                RenderEngine.renderReposView();
            });
        }

        static setupKBControls() {
            document.getElementById("kb-sort")?.addEventListener("change", RenderEngine.renderKBView);
            document.getElementById("kb-pillar-filter")?.addEventListener("change", RenderEngine.renderKBView);
        }

        static setupSearch() {
            const input = document.getElementById("search-input");
            let debounceTimer;

            input?.addEventListener("input", () => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    RenderEngine.renderReposView();
                    RenderEngine.renderKBView();
                }, 200);
            });

            document.addEventListener("keydown", e => {
                if ((e.metaKey || e.ctrlKey) && e.key === "k") {
                    e.preventDefault();
                    input?.focus();
                }
                if (e.key === "Escape") {
                    input?.blur();
                    if (input) input.value = "";
                    RenderEngine.renderReposView();
                    RenderEngine.renderKBView();
                }
            });
        }

        static setupSettings() {
            const modal = document.getElementById("settings-modal");
            const openBtn = document.getElementById("btn-settings");
            const closeBtn = document.getElementById("btn-close-settings");
            const saveBtn = document.getElementById("btn-save-settings");

            openBtn?.addEventListener("click", () => {
                UI.setValue("setting-repo", AppState.repo);
                UI.setValue("setting-data-mode", AppState.state.settings.dataMode || "local");
                UI.setValue("setting-theme", AppState.state.settings.theme || "dark");
                if (modal) modal.style.display = "flex";
            });

            closeBtn?.addEventListener("click", () => {
                if (modal) modal.style.display = "none";
            });

            modal?.addEventListener("click", e => {
                if (e.target === modal) modal.style.display = "none";
            });

            saveBtn?.addEventListener("click", () => {
                AppState.saveSettings({
                    repo: UI.getValue("setting-repo") || DEFAULT_REPO,
                    dataMode: UI.getValue("setting-data-mode") || "local",
                    theme: UI.getValue("setting-theme") || "dark",
                });
                if (modal) modal.style.display = "none";
            });

            document.getElementById("btn-refresh")?.addEventListener("click", DataService.loadAllData);
        }

        static setupCapture() {
            document.getElementById("btn-capture")?.addEventListener("click", () => {
                const title = UI.getValue("capture-title").trim();
                const body = UI.getValue("capture-body").trim();

                if (!title) {
                    alert("Please enter a signal title");
                    return;
                }

                const repo = AppState.repo;
                const encodedTitle = encodeURIComponent(title);
                const encodedBody = encodeURIComponent(body || "");
                const issueUrl = `https://github.com/${repo}/issues/new?title=${encodedTitle}&body=${encodedBody}`;

                window.open(issueUrl, "_blank");

                UI.setValue("capture-title", "");
                UI.setValue("capture-body", "");
            });
        }

        static setTodayDate() {
            const el = document.getElementById("today-date");
            if (el) {
                el.textContent = new Date().toLocaleDateString("en-US", {
                    weekday: "long",
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                });
            }
        }

        static updateSyncInfo() {
            UI.setText("sync-info", `Last sync: ${new Date().toLocaleTimeString()}`);
        }

        static updateStatus(text, type) {
            UI.setText("status-text", text);
            const dot = document.querySelector(".status-dot");
            if (dot) {
                dot.style.background =
                    type === "ok" ? "var(--color-normal)" :
                    type === "error" ? "var(--color-interrupt)" :
                    "var(--color-watch)";
            }
        }

        static setText(id, text) {
            const el = document.getElementById(id);
            if (el) el.textContent = text;
        }

        static getValue(id) {
            const el = document.getElementById(id);
            return el ? el.value : "";
        }

        static setValue(id, val) {
            const el = document.getElementById(id);
            if (el) el.value = val;
        }
    }

    // ── Utilities Module ──
    class Utils {
        static formatTimeAgo(isoString) {
            if (!isoString) return "—";
            const date = new Date(isoString);
            const now = new Date();
            const diffMs = now - date;
            const diffMin = Math.floor(diffMs / 60000);
            const diffHr = Math.floor(diffMs / 3600000);
            const diffDay = Math.floor(diffMs / 86400000);

            if (diffMin < 1) return "just now";
            if (diffMin < 60) return `${diffMin}m ago`;
            if (diffHr < 24) return `${diffHr}h ago`;
            if (diffDay < 7) return `${diffDay}d ago`;
            if (diffDay < 30) return `${Math.floor(diffDay / 7)}w ago`;
            return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
        }

        static escapeHtml(str) {
            if (!str) return "";
            return str
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }
    }

    // Initialization
    document.addEventListener("DOMContentLoaded", UI.init);
})();
