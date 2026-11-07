const API_URL = window.APP_CONFIG.API_BASE_URL;

const state = {
    token: localStorage.getItem("token"),
    user: null,
    tickets: [],
    selectedTicket: null,
    skip: 0,
    limit: 10
};

const $ = id => document.getElementById(id);

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

function showMessage(id, message, success = false) {
    const element = $(id);
    element.textContent = message;
    element.className = success ? "message success" : "message";
}

async function api(path, options = {}) {
    const headers = { ...(options.headers || {}) };

    if (state.token) {
        headers.Authorization = `Bearer ${state.token}`;
    }

    if (options.body) {
        headers["Content-Type"] = "application/json";
    }

    const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers
    });

    const text = await response.text();
    let data;

    try {
        data = text ? JSON.parse(text) : null;
    } catch {
        data = text;
    }

    if (!response.ok) {
        throw new Error(
            data?.detail || `Request failed: ${response.status}`
        );
    }

    return data;
}

// Authentication tabs
document.querySelectorAll(".auth-tab").forEach(button => {
    button.addEventListener("click", () => {
        document.querySelectorAll(".auth-tab").forEach(tab =>
            tab.classList.remove("active")
        );

        button.classList.add("active");

        const login = button.dataset.tab === "login";

        $("loginForm").classList.toggle("hidden", !login);
        $("registerForm").classList.toggle("hidden", login);

        showMessage("authMessage", "");
    });
});

// Login
$("loginForm").addEventListener("submit", async event => {
    event.preventDefault();

    const form = new FormData(event.currentTarget);

    const body = new URLSearchParams({
        username: form.get("username"),
        password: form.get("password")
    });

    try {
        showMessage("authMessage", "Logging in...");

        const response = await fetch(`${API_URL}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Login failed");
        }

        state.token = data.access_token;
        localStorage.setItem("token", state.token);

        await loadProfile();
        showDashboard();

    } catch (error) {
        showMessage("authMessage", error.message);
    }
});

// Registration
$("registerForm").addEventListener("submit", async event => {
    event.preventDefault();

    const form = new FormData(event.currentTarget);

    try {
        showMessage("authMessage", "Creating account...");

        const result = await api("/register", {
            method: "POST",
            body: JSON.stringify({
                username: form.get("username"),
                password: form.get("password")
            })
        });

        showMessage(
            "authMessage",
            result.message || "Account created. Please log in.",
            true
        );

        document.querySelector('[data-tab="login"]').click();

        $("loginForm").elements.username.value =
            form.get("username");

    } catch (error) {
        showMessage("authMessage", error.message);
    }
});

// Get authenticated user details
async function loadProfile() {
    state.user = await api("/users/me");
    $("userInfo").textContent =
        `${state.user.username} · ${state.user.role}`;
}

// Show dashboard
function showDashboard() {
    $("authView").classList.add("hidden");
    $("dashboard").classList.remove("hidden");
    $("logoutBtn").classList.remove("hidden");

    const role = state.user.role;

    $("pageTitle").textContent =
        role === "admin" ? "Admin workspace" :
        role === "agent" ? "Assigned tickets" :
        "Your tickets";

    $("pageDescription").textContent =
        role === "admin" ? "Manage customer requests and agent assignments." :
        role === "agent" ? "Review and respond to your assigned tickets." :
        "Create requests and follow their progress.";

    $("newTicketBtn").classList.toggle(
        "hidden",
        role !== "customer"
    );

    loadTickets();
}

// Logout
$("logoutBtn").addEventListener("click", () => {
    localStorage.removeItem("token");
    state.token = null;
    state.user = null;
    state.selectedTicket = null;

    $("dashboard").classList.add("hidden");
    $("authView").classList.remove("hidden");
    $("logoutBtn").classList.add("hidden");
    $("userInfo").textContent = "";
});

// Create ticket dialog
$("newTicketBtn").addEventListener("click", () => {
    $("ticketDialog").showModal();
});

$("closeDialog").addEventListener("click", () => {
    $("ticketDialog").close();
});

$("cancelDialog").addEventListener("click", () => {
    $("ticketDialog").close();
});

// Create ticket
$("ticketForm").addEventListener("submit", async event => {
    event.preventDefault();

    const form = new FormData(event.currentTarget);

    try {
        await api("/tickets", {
            method: "POST",
            body: JSON.stringify({
                title: form.get("title"),
                description: form.get("description"),
                priority: form.get("priority")
            })
        });

        $("ticketDialog").close();
        event.currentTarget.reset();

        showMessage("appMessage", "Ticket created successfully.", true);
        await loadTickets();

    } catch (error) {
        showMessage("appMessage", error.message);
    }
});

// Search and filters
["searchInput", "statusFilter", "priorityFilter", "pageSize"]
    .forEach(id => {
        $(id).addEventListener("input", () => {
            if (id === "pageSize") {
                state.limit = Number($("pageSize").value);
            }

            state.skip = 0;
            loadTickets();
        });

        if (id !== "searchInput") {
            $(id).addEventListener("change", () => {
                state.skip = 0;
                loadTickets();
            });
        }
    });

// Pagination
$("previousPage").addEventListener("click", () => {
    state.skip = Math.max(0, state.skip - state.limit);
    loadTickets();
});

$("nextPage").addEventListener("click", () => {
    if (state.tickets.length === state.limit) {
        state.skip += state.limit;
        loadTickets();
    }
});

// Get tickets
async function loadTickets() {
    try {
        const params = new URLSearchParams({
            skip: state.skip,
            limit: state.limit
        });

        if ($("searchInput").value.trim()) {
            params.set("search", $("searchInput").value.trim());
        }

        if ($("statusFilter").value) {
            params.set("status", $("statusFilter").value);
        }

        if ($("priorityFilter").value) {
            params.set("priority", $("priorityFilter").value);
        }

        state.tickets = await api(`/tickets?${params}`);

        $("totalCount").textContent = state.tickets.length;
        $("openCount").textContent =
            state.tickets.filter(t => t.status === "open").length;
        $("progressCount").textContent =
            state.tickets.filter(t => t.status === "in_progress").length;
        $("resolvedCount").textContent =
            state.tickets.filter(t => t.status === "resolved").length;

        $("resultCount").textContent =
            `${state.tickets.length} result(s)`;

        $("pageLabel").textContent =
            `Page ${Math.floor(state.skip / state.limit) + 1}`;

        $("previousPage").disabled = state.skip === 0;
        $("nextPage").disabled = state.tickets.length < state.limit;

        renderTickets();

    } catch (error) {
        showMessage("appMessage", error.message);
    }
}

// Render ticket list
function renderTickets() {
    if (!state.tickets.length) {
        $("ticketList").innerHTML =
            '<p class="empty-state">No tickets found.</p>';
        return;
    }

    $("ticketList").innerHTML = state.tickets.map(ticket => `
        <article class="ticket-item ${
            state.selectedTicket?.id === ticket.id ? "selected" : ""
        }" data-id="${ticket.id}">

            <div class="ticket-top">
                <span class="ticket-title">
                    #${ticket.id} · ${escapeHTML(ticket.title)}
                </span>

                <span class="pill status-${escapeHTML(ticket.status)}">
                    ${escapeHTML(ticket.status.replace("_", " "))}
                </span>
            </div>

            <div class="ticket-meta">
                <span class="pill priority-${escapeHTML(ticket.priority)}">
                    ${escapeHTML(ticket.priority)}
                </span>
                <span>${escapeHTML(ticket.created_at || "Date unavailable")}</span>
                ${ticket.assigned_to
                    ? `<span>Agent #${ticket.assigned_to}</span>`
                    : ""}
            </div>
        </article>
    `).join("");

    document.querySelectorAll(".ticket-item").forEach(item => {
        item.addEventListener("click", () => {
            openTicket(Number(item.dataset.id));
        });
    });
}

// Open ticket details
async function openTicket(id) {
    try {
        const ticket = await api(`/tickets/${id}`);
        state.selectedTicket = ticket;

        renderTickets();

        const role = state.user.role;
        const canUpdate = role === "admin" || role === "agent";

        $("ticketDetails").innerHTML = `
            <div class="detail-top">
                <div>
                    <p class="eyebrow">TICKET #${ticket.id}</p>
                    <h2>${escapeHTML(ticket.title)}</h2>
                </div>

                <span class="pill status-${escapeHTML(ticket.status)}">
                    ${escapeHTML(ticket.status.replace("_", " "))}
                </span>
            </div>

            <div class="detail-meta">
                <span class="pill priority-${escapeHTML(ticket.priority)}">
                    ${escapeHTML(ticket.priority)} priority
                </span>
            </div>

            <p class="detail-description">
                ${escapeHTML(ticket.description)}
            </p>

            ${canUpdate ? `
                <div class="detail-controls">
                    <select id="statusUpdate">
                        <option value="open">Open</option>
                        <option value="in_progress">In progress</option>
                        <option value="resolved">Resolved</option>
                        <option value="closed">Closed</option>
                    </select>
                    <button id="saveStatus" class="button button-primary">
                        Update status
                    </button>
                </div>
            ` : ""}

            ${role === "admin" ? `
                <form id="assignForm" class="assign-form">
                    <input id="agentId" type="number" min="1"
                        placeholder="Agent user ID" required>
                    <button class="button button-light">Assign</button>
                </form>
            ` : ""}

            <h3 class="section-label">Conversation</h3>

            <div id="commentList" class="comment-list">
                <p class="empty-state">Loading comments...</p>
            </div>

            <form id="commentForm" class="comment-form">
                <textarea name="content" maxlength="4000"
                    placeholder="Write a reply..." required></textarea>
                <button class="button button-primary">Send comment</button>
            </form>
        `;

        if (canUpdate) {
            $("statusUpdate").value = ticket.status;

            $("saveStatus").addEventListener("click", async () => {
                try {
                    await api(`/tickets/${id}`, {
                        method: "PUT",
                        body: JSON.stringify({
                            status: $("statusUpdate").value
                        })
                    });

                    await loadTickets();
                    await openTicket(id);

                } catch (error) {
                    showMessage("appMessage", error.message);
                }
            });
        }

        if (role === "admin") {
            $("assignForm").addEventListener("submit", async event => {
                event.preventDefault();

                try {
                    const agentId = $("agentId").value;

                    await api(
                        `/tickets/${id}/assign?agent_id=${agentId}`,
                        { method: "PUT" }
                    );

                    await loadTickets();
                    await openTicket(id);

                } catch (error) {
                    showMessage("appMessage", error.message);
                }
            });
        }

        $("commentForm").addEventListener("submit", async event => {
            event.preventDefault();

            const content =
                new FormData(event.currentTarget).get("content");

            try {
                await api(`/tickets/${id}/comments`, {
                    method: "POST",
                    body: JSON.stringify({ content })
                });

                event.currentTarget.reset();
                await loadComments(id);

            } catch (error) {
                showMessage("appMessage", error.message);
            }
        });

        await loadComments(id);

    } catch (error) {
        showMessage("appMessage", error.message);
    }
}

// Get comments
async function loadComments(ticketId) {
    try {
        const comments =
            await api(`/tickets/${ticketId}/comments`);

        $("commentList").innerHTML = comments.length
            ? comments.map(comment => `
                <article class="comment">
                    <div class="comment-head">
                        <span class="comment-author">
                            User #${comment.user_id}
                        </span>
                        <span>${escapeHTML(comment.created_at)}</span>
                    </div>
                    <div class="comment-body">
                        ${escapeHTML(comment.content)}
                    </div>
                </article>
            `).join("")
            : '<p class="empty-state">No comments yet.</p>';

    } catch (error) {
        $("commentList").textContent = error.message;
    }
}

// Restore session
async function startApp() {
    if (!state.token) return;

    try {
        await loadProfile();
        showDashboard();
    } catch {
        localStorage.removeItem("token");
        state.token = null;
    }
}

startApp();