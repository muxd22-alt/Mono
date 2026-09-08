/* ═══════════════════════════════════════════════════════════════
   Mono Signal OS — Application Logic
   ═══════════════════════════════════════════════════════════════ */

(function () {
    "use strict";

    // ── Config ──
    const CONFIG = window.MONO_CONFIG || {};
    const DEFAULT_REPO = CONFIG.defaultRepo || "muxd22-alt/Signal-OS";
    const PILLAR_META = {
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

    // ── State ──
    let state = {
        repos: [],
        digest: null,
        kb: [],
        currentView: "today",
        currentPillar: "all",
        settings: loadSettings(),
    };

    function loadSettings() {
        try {
            const s = localStorage.getItem("mono_settings");
            return s ? JSON.parse(s) : { repo: DEFAULT_REPO, dataMode: "local", theme: "dark" };
        } catch {
            return { repo: DEFAULT_REPO, dataMode: "local", theme: "dark" };
        }
    }

    function saveSettings(s) {
        state.settings = s;
        localStorage.setItem("mono_settings", JSON.stringify(s));
    }

    // ── Initialization ──
    document.addEventListener("DOMContentLoaded", init);

    async function init() {
        setupNavigation();
        setupSearch();
        setupSettings();
        setupCapture();
        setupPillarTabs();
        setupKBControls();
        setTodayDate();

        await loadAllData();

        // Finish loading animation
        setTimeout(() => {
            const loadingScreen = document.getElementById("loading-screen");
            const app = document.getElementById("app");
            loadingScreen.classList.add("fade-out");
            app.classList.remove("hidden");
            setTimeout(() => {
                app.classList.add("visible");
                loadingScreen.style.display = "none";
            }, 400);
        }, 1800);
    }

    // ── Data Loading ──
    async function loadAllData() {
        try {
            const [reposData, digestData, kbData] = await Promise.allSettled([
                fetchJSON("data/repos.json"),
                fetchJSON("data/digest.json"),
                fetchKB("knowledge_base.jsonl"),
            ]);

            if (reposData.status === "fulfilled" && reposData.value) {
                state.repos = reposData.value.repos || [];
            }
            if (digestData.status === "fulfilled" && digestData.value) {
                state.digest = digestData.value;
            }
            if (kbData.status === "fulfilled" && kbData.value) {
                state.kb = kbData.value;
            }

            renderAll();
            updateSyncInfo();
            updateStatus("Synced", "ok");
        } catch (err) {
            console.error("Data load error:", err);
            updateStatus("Offline", "error");
            renderAll();
        }
    }

    async function fetchJSON(url) {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
        return resp.json();
    }

    async function fetchKB(url) {
        try {
            const resp = await fetch(url);
            if (!resp.ok) return [];
            const text = await resp.text();
            return text.trim().split("\n").filter(Boolean).map(line => JSON.parse(line));
        } catch {
            return [];
        }
    }

    // ── Rendering ──
    function renderAll() {
        renderTodayView();
        renderReposView();
        renderKBView();
        updateCounts();
    }

    function renderTodayView() {
        const digest = state.digest;
        const kb = state.kb;

        // Stats
        const totalEntries = kb.length;
        const now = new Date();
        const cutoff24h = new Date(now - 24 * 60 * 60 * 1000).toISOString();

        const recent24h = kb.filter(e => (e.timestamp || "") >= cutoff24h);
        const interrupts = recent24h.filter(e => (e.urgency || 0) >= 9);
        const watch = recent24h.filter(e => {
            const u = e.urgency || 0;
            return u >= 5 && u < 9;
        });

        document.getElementById("stat-total").textContent = totalEntries;
        document.getElementById("stat-interrupts").textContent = interrupts.length;
        document.getElementById("stat-watch").textContent = watch.length;

        // Active repos
        const activeRepos = state.repos.filter(r => (r.pushed_at || "") >= cutoff24h);
        document.getElementById("stat-repos-active").textContent = activeRepos.length;

        // Interrupt section
        const interruptSection = document.getElementById("interrupt-section");
        const interruptList = document.getElementById("interrupt-list");
        if (interrupts.length > 0) {
            interruptSection.style.display = "block";
            interruptList.innerHTML = interrupts.map(renderEntryCard).join("");
        } else {
            interruptSection.style.display = "none";
        }

        // Watch section
        const watchSection = document.getElementById("watch-section");
        const watchList = document.getElementById("watch-list");
        if (watch.length > 0) {
            watchSection.style.display = "block";
            watchList.innerHTML = watch.map(renderEntryCard).join("");
        } else {
            watchSection.style.display = "none";
        }

        // Active repo chips
        const chipsEl = document.getElementById("active-repos-chips");
        if (activeRepos.length > 0) {
            chipsEl.innerHTML = activeRepos.map(r => {
                const pillar = PILLAR_META[r.pillar] || {};
                return `<a href="${r.url}" target="_blank" class="repo-chip">
                    <span>${pillar.emoji || "◉"}</span>
                    <span>${r.name}</span>
                </a>`;
            }).join("");
        } else {
            // Show weekly active repos instead
            const cutoff7d = new Date(now - 7 * 24 * 60 * 60 * 1000).toISOString();
            const weekRepos = state.repos.filter(r => (r.pushed_at || "") >= cutoff7d).slice(0, 15);
            if (weekRepos.length > 0) {
                chipsEl.innerHTML = `<p style="font-size:0.75rem;color:var(--text-muted);margin-bottom:0.5rem;">No repos pushed today — showing last 7 days:</p>` +
                    weekRepos.map(r => {
                        const pillar = PILLAR_META[r.pillar] || {};
                        return `<a href="${r.url}" target="_blank" class="repo-chip">
                            <span>${pillar.emoji || "◉"}</span>
                            <span>${r.name}</span>
                        </a>`;
                    }).join("");
            } else {
                chipsEl.innerHTML = `<p style="font-size:0.8rem;color:var(--text-muted);">Waiting for repo data...</p>`;
            }
        }

        // Recent entries
        const recentList = document.getElementById("recent-list");
        const emptyToday = document.getElementById("empty-today");

        // Show all KB sorted by recency, but prioritize recent
        const sorted = [...kb].sort((a, b) => (b.timestamp || "").localeCompare(a.timestamp || ""));
        const recent = sorted.slice(0, 20);

        if (recent.length > 0) {
            recentList.innerHTML = recent.map(renderEntryCard).join("");
            emptyToday.style.display = "none";
        } else {
            recentList.innerHTML = "";
            emptyToday.style.display = "block";
        }
    }

    function renderEntryCard(entry) {
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

        const timeAgo = formatTimeAgo(entry.timestamp);

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
                <div class="entry-summary">${escapeHtml(entry.summary || entry.content || "")}</div>
                ${entry.reason ? `<div class="entry-reason">${escapeHtml(entry.reason)}</div>` : ""}
                <div class="entry-meta">
                    <div class="entry-meta-scores">
                        <span class="entry-meta-score">R:${entry.relevance || 0}</span>
                        <span class="entry-meta-score">N:${entry.novelty || 0}</span>
                        <span class="entry-meta-score">U:${urgency}</span>
                    </div>
                    <span>${timeAgo}</span>
                    ${entry.issue_number ? `<a href="https://github.com/${state.settings.repo}/issues/${entry.issue_number}" target="_blank" style="color:var(--color-accent);text-decoration:none;">#${entry.issue_number}</a>` : ""}
                </div>
            </div>
        </div>`;
    }

    function renderReposView() {
        const grid = document.getElementById("repo-grid");
        const empty = document.getElementById("empty-repos");
        const filtered = filterRepos();

        if (filtered.length === 0) {
            grid.innerHTML = "";
            empty.style.display = "block";
            return;
        }

        empty.style.display = "none";
        grid.innerHTML = filtered.map(renderRepoCard).join("");
    }

    function filterRepos() {
        let repos = state.repos;
        if (state.currentPillar !== "all") {
            repos = repos.filter(r => r.pillar === state.currentPillar);
        }

        // Search filter
        const q = (document.getElementById("search-input")?.value || "").toLowerCase();
        if (q) {
            repos = repos.filter(r =>
                r.name.toLowerCase().includes(q) ||
                (r.description || "").toLowerCase().includes(q) ||
                (r.pillar_name || "").toLowerCase().includes(q) ||
                (r.language || "").toLowerCase().includes(q)
            );
        }

        return repos;
    }

    function renderRepoCard(repo) {
        const pillar = PILLAR_META[repo.pillar] || {};
        const langColor = LANG_COLORS[repo.language] || "#666";
        const pushed = formatTimeAgo(repo.pushed_at);

        let issuesHtml = "";
        if (repo.recent_issues && repo.recent_issues.length > 0) {
            issuesHtml = `<div class="repo-issues-inline">` +
                repo.recent_issues.slice(0, 2).map(i =>
                    `<a href="${i.url}" target="_blank" class="repo-issue-chip">
                        <span class="repo-issue-num">#${i.number}</span>
                        <span class="truncate">${escapeHtml(i.title)}</span>
                    </a>`
                ).join("") +
                `</div>`;
        }

        return `
        <div class="repo-card" style="--repo-pillar-color: ${pillar.color || '#666'}">
            <div class="repo-card-header">
                <div>
                    <div class="repo-name">
                        <a href="${repo.url}" target="_blank">${escapeHtml(repo.name)}</a>
                    </div>
                    <div class="repo-account">@${repo.account}</div>
                </div>
                ${repo.private ? `<span class="repo-private-badge">Private</span>` : ""}
            </div>
            ${repo.description ? `<div class="repo-desc">${escapeHtml(repo.description)}</div>` : ""}
            <div class="repo-stats">
                <span class="repo-stat">
                    <span class="repo-lang-dot" style="background:${langColor}"></span>
                    ${repo.language || "Unknown"}
                </span>
                ${repo.stars > 0 ? `<span class="repo-stat">⭐ ${repo.stars}</span>` : ""}
                ${repo.open_issues > 0 ? `<span class="repo-stat">🔹 ${repo.open_issues} issues</span>` : ""}
                ${repo.fork ? `<span class="repo-stat">🔱 Fork</span>` : ""}
            </div>
            <div class="repo-pushed">Pushed ${pushed}</div>
            ${issuesHtml}
        </div>`;
    }

    function renderKBView() {
        const list = document.getElementById("kb-list");
        const empty = document.getElementById("empty-kb");
        const sortBy = document.getElementById("kb-sort")?.value || "newest";
        const pillarFilter = document.getElementById("kb-pillar-filter")?.value || "all";

        let entries = [...state.kb];

        // Filter by pillar
        if (pillarFilter !== "all") {
            entries = entries.filter(e => e.pillar === pillarFilter);
        }

        // Search filter
        const q = (document.getElementById("search-input")?.value || "").toLowerCase();
        if (q) {
            entries = entries.filter(e =>
                (e.summary || "").toLowerCase().includes(q) ||
                (e.content || "").toLowerCase().includes(q) ||
                (e.reason || "").toLowerCase().includes(q) ||
                (e.pillar || "").toLowerCase().includes(q)
            );
        }

        // Sort
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
            default: // newest
                entries.sort((a, b) => (b.timestamp || "").localeCompare(a.timestamp || ""));
        }

        if (entries.length === 0) {
            list.innerHTML = "";
            empty.style.display = "block";
            return;
        }

        empty.style.display = "none";
        list.innerHTML = entries.map(renderEntryCard).join("");
    }

    // ── Navigation ──
    function setupNavigation() {
        const navItems = document.querySelectorAll(".nav-item[data-view]");
        navItems.forEach(item => {
            item.addEventListener("click", () => {
                const view = item.dataset.view;
                switchView(view);
            });
        });

        // Pillar sidebar filters
        const pillarFilters = document.querySelectorAll(".pillar-filter");
        pillarFilters.forEach(btn => {
            btn.addEventListener("click", () => {
                state.currentPillar = btn.dataset.pillar;
                pillarFilters.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                switchView("repos");
                // Also update the pillar tabs
                document.querySelectorAll(".pillar-tab").forEach(t => {
                    t.classList.toggle("active", t.dataset.tab === state.currentPillar);
                });
                renderReposView();
            });
        });
    }

    function switchView(viewName) {
        state.currentView = viewName;

        document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
        document.getElementById(`view-${viewName}`)?.classList.add("active");

        document.querySelectorAll(".nav-item[data-view]").forEach(n => {
            n.classList.toggle("active", n.dataset.view === viewName);
        });
    }

    function setupPillarTabs() {
        document.getElementById("pillar-tabs")?.addEventListener("click", e => {
            const tab = e.target.closest(".pillar-tab");
            if (!tab) return;

            state.currentPillar = tab.dataset.tab;
            document.querySelectorAll(".pillar-tab").forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            renderReposView();
        });
    }

    function setupKBControls() {
        document.getElementById("kb-sort")?.addEventListener("change", renderKBView);
        document.getElementById("kb-pillar-filter")?.addEventListener("change", renderKBView);
    }

    // ── Search ──
    function setupSearch() {
        const input = document.getElementById("search-input");
        let debounceTimer;

        input?.addEventListener("input", () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                renderReposView();
                renderKBView();
            }, 200);
        });

        // Cmd+K / Ctrl+K shortcut
        document.addEventListener("keydown", e => {
            if ((e.metaKey || e.ctrlKey) && e.key === "k") {
                e.preventDefault();
                input?.focus();
            }
            if (e.key === "Escape") {
                input?.blur();
                if (input) input.value = "";
                renderReposView();
                renderKBView();
            }
        });
    }

    // ── Settings ──
    function setupSettings() {
        const modal = document.getElementById("settings-modal");
        const openBtn = document.getElementById("btn-settings");
        const closeBtn = document.getElementById("btn-close-settings");
        const saveBtn = document.getElementById("btn-save-settings");

        openBtn?.addEventListener("click", () => {
            document.getElementById("setting-repo").value = state.settings.repo || DEFAULT_REPO;
            document.getElementById("setting-data-mode").value = state.settings.dataMode || "local";
            document.getElementById("setting-theme").value = state.settings.theme || "dark";
            modal.style.display = "flex";
        });

        closeBtn?.addEventListener("click", () => {
            modal.style.display = "none";
        });

        modal?.addEventListener("click", e => {
            if (e.target === modal) modal.style.display = "none";
        });

        saveBtn?.addEventListener("click", () => {
            saveSettings({
                repo: document.getElementById("setting-repo").value || DEFAULT_REPO,
                dataMode: document.getElementById("setting-data-mode").value || "local",
                theme: document.getElementById("setting-theme").value || "dark",
            });
            modal.style.display = "none";
        });

        // Refresh button
        document.getElementById("btn-refresh")?.addEventListener("click", async () => {
            updateStatus("Syncing...", "loading");
            await loadAllData();
        });
    }

    // ── Capture ──
    function setupCapture() {
        const captureBtn = document.getElementById("btn-capture");
        captureBtn?.addEventListener("click", () => {
            const title = document.getElementById("capture-title")?.value?.trim();
            const body = document.getElementById("capture-body")?.value?.trim();

            if (!title) {
                alert("Please enter a signal title");
                return;
            }

            const repo = state.settings.repo || DEFAULT_REPO;
            const encodedTitle = encodeURIComponent(title);
            const encodedBody = encodeURIComponent(body || "");
            const issueUrl = `https://github.com/${repo}/issues/new?title=${encodedTitle}&body=${encodedBody}`;

            window.open(issueUrl, "_blank");

            // Clear inputs
            document.getElementById("capture-title").value = "";
            document.getElementById("capture-body").value = "";
        });
    }

    // ── Helpers ──
    function updateCounts() {
        const now = new Date();
        const cutoff24h = new Date(now - 24 * 60 * 60 * 1000).toISOString();
        const recent = state.kb.filter(e => (e.timestamp || "") >= cutoff24h);

        document.getElementById("today-count").textContent = recent.length;
        document.getElementById("repos-count").textContent = state.repos.length;
        document.getElementById("kb-count").textContent = state.kb.length;

        // Pillar counts for repos
        const pillarCounts = {};
        state.repos.forEach(r => {
            const p = r.pillar || "unknown";
            pillarCounts[p] = (pillarCounts[p] || 0) + 1;
        });

        document.querySelectorAll("[data-pillar-count]").forEach(el => {
            const pk = el.dataset.pillarCount;
            el.textContent = pillarCounts[pk] || 0;
        });
    }

    function setTodayDate() {
        const el = document.getElementById("today-date");
        if (el) {
            const now = new Date();
            el.textContent = now.toLocaleDateString("en-US", {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric",
            });
        }
    }

    function updateSyncInfo() {
        const el = document.getElementById("sync-info");
        if (el) {
            el.textContent = `Last sync: ${new Date().toLocaleTimeString()}`;
        }
    }

    function updateStatus(text, type) {
        const dot = document.querySelector(".status-dot");
        const label = document.querySelector(".status-text");
        if (label) label.textContent = text;

        if (dot) {
            dot.style.background =
                type === "ok" ? "var(--color-normal)" :
                type === "error" ? "var(--color-interrupt)" :
                "var(--color-watch)";
        }
    }

    function formatTimeAgo(isoString) {
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

    function escapeHtml(str) {
        if (!str) return "";
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }
})();
