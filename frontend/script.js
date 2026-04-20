// script.js - Shared JavaScript utilities and API helpers

// ─────────────────────────────────────────────
// Configuration
// ─────────────────────────────────────────────
const API_BASE = "http://localhost:8000";  // Change to your server URL in production

// ─────────────────────────────────────────────
// Auth Helpers (using localStorage)
// ─────────────────────────────────────────────
const Auth = {
  save(userData) {
    localStorage.setItem("user", JSON.stringify(userData));
  },
  get() {
    try { return JSON.parse(localStorage.getItem("user")); }
    catch { return null; }
  },
  clear() { localStorage.removeItem("user"); },
  isLoggedIn() { return !!this.get(); },
  isAdmin() { return this.get()?.role === "admin"; },
  isStudent() { return this.get()?.role === "student"; }
};

// ─────────────────────────────────────────────
// API Helper - wraps fetch with error handling
// ─────────────────────────────────────────────
async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const user = Auth.get();

  const defaultHeaders = { "Content-Type": "application/json" };
  if (user?.token) defaultHeaders["Authorization"] = `Bearer ${user.token}`;

  // Don't set Content-Type for FormData (browser handles it)
  if (options.body instanceof FormData) {
    delete defaultHeaders["Content-Type"];
  }

  try {
    const res = await fetch(url, {
      ...options,
      headers: { ...defaultHeaders, ...(options.headers || {}) }
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || data.message || `HTTP ${res.status}`);
    }
    return { success: true, data };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

// ─────────────────────────────────────────────
// UI Helpers
// ─────────────────────────────────────────────

/** Show an alert message inside a container element */
function showAlert(containerId, message, type = "error") {
  const icons = { success: "✅", error: "❌", warning: "⚠️", info: "ℹ️" };
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `
    <div class="alert alert-${type}">
      <span>${icons[type] || "ℹ️"}</span>
      <span>${message}</span>
    </div>
  `;
  el.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/** Clear an alert container */
function clearAlert(containerId) {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = "";
}

/** Set button loading state */
function setButtonLoading(btn, loading, originalText) {
  if (loading) {
    btn.disabled = true;
    btn.dataset.original = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span> Please wait...`;
  } else {
    btn.disabled = false;
    btn.innerHTML = originalText || btn.dataset.original || "Submit";
  }
}

/** Format a date string nicely */
function formatDate(dateStr) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("en-IN", {
    year: "numeric", month: "long", day: "numeric",
    hour: "2-digit", minute: "2-digit"
  });
}

/** Get status badge HTML */
function getStatusBadge(status) {
  const badges = {
    "Pending": `<span class="badge badge-pending">⏳ Pending</span>`,
    "Approved": `<span class="badge badge-approved">✅ Approved</span>`,
    "Rejected": `<span class="badge badge-rejected">❌ Rejected</span>`
  };
  return badges[status] || `<span class="badge">${status}</span>`;
}

// ─────────────────────────────────────────────
// Form Validation
// ─────────────────────────────────────────────
const Validate = {
  email(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  },
  phone(value) {
    return /^[6-9]\d{9}$/.test(value.replace(/\s/g, ""));
  },
  minLength(value, min) {
    return value.trim().length >= min;
  },
  required(value) {
    return value.trim().length > 0;
  }
};

/** Show a field error */
function showFieldError(inputId, message) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.classList.add("error");
  let errEl = input.parentElement.querySelector(".field-error");
  if (!errEl) {
    errEl = document.createElement("div");
    errEl.className = "field-error";
    input.after(errEl);
  }
  errEl.innerHTML = `⚠ ${message}`;
}

/** Clear a field error */
function clearFieldError(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.classList.remove("error");
  const errEl = input.parentElement.querySelector(".field-error");
  if (errEl) errEl.remove();
}

/** Setup live validation on blur */
function setupLiveValidation(inputId, validatorFn, errorMsg) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.addEventListener("blur", () => {
    if (!validatorFn(input.value)) {
      showFieldError(inputId, errorMsg);
    } else {
      clearFieldError(inputId);
      input.classList.add("success");
    }
  });
  input.addEventListener("input", () => {
    clearFieldError(inputId);
    input.classList.remove("success", "error");
  });
}

// ─────────────────────────────────────────────
// Navbar: Highlight active link & show user info
// ─────────────────────────────────────────────
function initNavbar() {
  // Highlight current page link
  const currentPage = window.location.pathname.split("/").pop();
  document.querySelectorAll(".nav-link").forEach(link => {
    if (link.getAttribute("href") === currentPage) {
      link.classList.add("active");
    }
  });

  // Show/hide nav items based on auth status
  const user = Auth.get();
  const guestLinks = document.querySelectorAll(".nav-guest");
  const authLinks = document.querySelectorAll(".nav-auth");
  const adminLinks = document.querySelectorAll(".nav-admin");
  const userNameEl = document.getElementById("nav-user-name");

  if (user) {
    guestLinks.forEach(el => el.classList.add("hidden"));
    authLinks.forEach(el => el.classList.remove("hidden"));
    if (user.role === "admin") {
      adminLinks.forEach(el => el.classList.remove("hidden"));
    }
    if (userNameEl) userNameEl.textContent = user.name;
  } else {
    authLinks.forEach(el => el.classList.add("hidden"));
    adminLinks.forEach(el => el.classList.add("hidden"));
  }
}

function logout() {
  Auth.clear();
  window.location.href = "index.html";
}

// Init navbar on every page load
document.addEventListener("DOMContentLoaded", initNavbar);
