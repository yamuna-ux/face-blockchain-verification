/* =========================================================
   FACE ID BLOCKCHAIN
   PROFESSIONAL DASHBOARD JAVASCRIPT
========================================================= */

"use strict";

/* =========================================================
   GLOBAL STATE
========================================================= */

const Dashboard = {

    settings: {
        animations: true,
        notifications: true,
        autoRefresh: true
    },

    refreshInterval: null,

    init() {

        this.loadSettings();

        this.setupNavigation();

        this.setupPanels();

        this.setupClock();

        this.setupDashboardStatus();

        this.setupSettings();

        this.setupRegistrySearch();

        this.setupMobileMenu();

        this.setupNotifications();

        this.setupAnimations();

        this.startAutoRefresh();

        this.updateLastCheck();

        console.log("FaceID Dashboard initialized.");
    }
};


/* =========================================================
   NAVIGATION
========================================================= */

Dashboard.setupNavigation = function () {

    const links = document.querySelectorAll(".sidebar-link[data-section]");

    const sections = document.querySelectorAll(".dashboard-section");

    links.forEach(link => {

        link.addEventListener("click", function (event) {

            event.preventDefault();

            const sectionName =
                this.dataset.section;

            links.forEach(item => {

                item.classList.remove("active");

            });

            this.classList.add("active");

            sections.forEach(section => {

                section.classList.remove("active");

            });

            const target =
                document.getElementById(sectionName);

            if (target) {

                target.classList.add("active");

            }

            const breadcrumb =
                document.getElementById("breadcrumbCurrent");

            if (breadcrumb) {

                breadcrumb.textContent =
                    this.querySelector("span")
                        ?.textContent || "Dashboard";

            }

            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });

        });

    });

};


/* =========================================================
   REGISTER / VERIFY BUTTONS
========================================================= */

Dashboard.setupPanels = function () {

    const registerButtons =
        document.querySelectorAll("[data-action='register']");

    registerButtons.forEach(button => {

        button.addEventListener("click", function () {

            window.location.href = "/register";

        });

    });


    const verifyButtons =
        document.querySelectorAll("[data-action='verify']");

    verifyButtons.forEach(button => {

        button.addEventListener("click", function () {

            window.location.href = "/verify";

        });

    });

};


/* =========================================================
   LIVE CLOCK
========================================================= */

Dashboard.setupClock = function () {

    const clock =
        document.getElementById("liveClock");

    const dateDisplay =
        document.getElementById("liveDate");

    function updateClock() {

        const now = new Date();

        const time =
            new Intl.DateTimeFormat(
                "en-IN",
                {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                    hour12: true,
                    timeZone: "Asia/Kolkata"
                }
            ).format(now);

        const date =
            new Intl.DateTimeFormat(
                "en-IN",
                {
                    weekday: "short",
                    day: "2-digit",
                    month: "short",
                    year: "numeric",
                    timeZone: "Asia/Kolkata"
                }
            ).format(now);

        if (clock) {

            clock.textContent =
                time + " IST";

        }

        if (dateDisplay) {

            dateDisplay.textContent =
                date;

        }

    }

    updateClock();

    setInterval(updateClock, 1000);

};


/* =========================================================
   DASHBOARD STATUS
========================================================= */

Dashboard.setupDashboardStatus = function () {

    this.fetchStatus();

};


Dashboard.fetchStatus = async function () {

    try {

        const response =
            await fetch("/api/status", {
                cache: "no-store"
            });

        if (!response.ok) {

            throw new Error(
                "Status request failed"
            );

        }

        const data =
            await response.json();

        this.applyStatus(data);

    }

    catch (error) {

        console.warn(
            "Unable to update dashboard status:",
            error
        );

        this.setOfflineState();

    }

};


/* =========================================================
   APPLY API STATUS
========================================================= */

Dashboard.applyStatus = function (data) {

    /*
       Expected backend values can include:

       registered
       blockchain_valid
       identities
       blocks
    */


    const registered =
        data.registered === true ||
        data.registered > 0;


    const blockchainValid =
        data.blockchain_valid === true;


    const identityCount =
        data.identities ??
        data.identity_count ??
        null;


    const blocks =
        data.blocks ??
        data.block_count ??
        null;


    /* Identity count */

    const identityElements =
        document.querySelectorAll(
            "[data-stat='identities']"
        );

    identityElements.forEach(element => {

        if (identityCount !== null) {

            element.textContent =
                identityCount;

        }

    });


    /* Blockchain blocks */

    const blockElements =
        document.querySelectorAll(
            "[data-stat='blocks']"
        );

    blockElements.forEach(element => {

        if (blocks !== null) {

            element.textContent =
                blocks;

        }

    });


    /* Blockchain status */

    const blockchainElements =
        document.querySelectorAll(
            "[data-stat='blockchain']"
        );

    blockchainElements.forEach(element => {

        element.textContent =
            blockchainValid
                ? "VALID"
                : "INVALID";

    });


    /* System status */

    const systemStatus =
        document.getElementById(
            "systemStatus"
        );

    if (systemStatus) {

        systemStatus.textContent =
            blockchainValid
                ? "SYSTEM SECURE"
                : "CHECK REQUIRED";

    }


    /* Status colors */

    const securityState =
        document.getElementById(
            "securityState"
        );

    if (securityState) {

        securityState.textContent =
            blockchainValid
                ? "SECURE"
                : "ATTENTION";

    }


    /* Update notification */

    this.updateNotificationFromStatus(
        blockchainValid,
        identityCount,
        blocks
    );

};


/* =========================================================
   OFFLINE FALLBACK
========================================================= */

Dashboard.setOfflineState = function () {

    const status =
        document.getElementById(
            "systemStatus"
        );

    if (status) {

        status.textContent =
            "SYSTEM CHECK";

    }

};


/* =========================================================
   LAST SYSTEM CHECK
========================================================= */

Dashboard.updateLastCheck = function () {

    const lastCheck =
        document.getElementById(
            "lastSystemCheck"
        );

    if (!lastCheck) {

        return;

    }

    lastCheck.textContent =
        "Just now";

};


/* =========================================================
   AUTO REFRESH
========================================================= */

Dashboard.startAutoRefresh = function () {

    if (this.refreshInterval) {

        clearInterval(
            this.refreshInterval
        );

    }

    if (!this.settings.autoRefresh) {

        return;

    }

    this.refreshInterval =
        setInterval(() => {

            this.fetchStatus();

            this.updateLastCheck();

        }, 15000);

};


/* =========================================================
   NOTIFICATIONS
========================================================= */

Dashboard.setupNotifications = function () {

    const button =
        document.getElementById(
            "notificationButton"
        );

    const panel =
        document.getElementById(
            "notificationPanel"
        );

    if (!button || !panel) {

        return;

    }

    button.addEventListener(
        "click",
        function (event) {

            event.stopPropagation();

            panel.classList.toggle(
                "show"
            );

        }
    );


    document.addEventListener(
        "click",
        function (event) {

            if (
                !panel.contains(event.target) &&
                !button.contains(event.target)
            ) {

                panel.classList.remove(
                    "show"
                );

            }

        }
    );


    const clearButton =
        document.getElementById(
            "clearNotifications"
        );

    if (clearButton) {

        clearButton.addEventListener(
            "click",
            function () {

                panel.querySelectorAll(
                    ".notification-item"
                ).forEach(item => {

                    item.remove();

                });

                const badge =
                    document.querySelector(
                        ".notification-badge"
                    );

                if (badge) {

                    badge.style.display =
                        "none";

                }

                Dashboard.showToast(
                    "Notifications cleared",
                    "All dashboard notifications have been cleared."
                );

            }
        );

    }

};


/* =========================================================
   STATUS NOTIFICATION
========================================================= */

Dashboard.updateNotificationFromStatus =
    function (
        blockchainValid,
        identityCount,
        blocks
    ) {

        if (!this.settings.notifications) {

            return;

        }

        const badge =
            document.querySelector(
                ".notification-badge"
            );

        if (badge) {

            badge.textContent = "1";

            badge.style.display =
                "flex";

        }

        const statusMessage =
            document.getElementById(
                "statusNotification"
            );

        if (statusMessage) {

            statusMessage.innerHTML =
                blockchainValid
                    ? `
                        <div class="notification-icon">
                            <i class="bi bi-shield-check"></i>
                        </div>
                        <div>
                            <strong>System secure</strong>
                            <p>Blockchain integrity verified successfully.</p>
                        </div>
                    `
                    : `
                        <div class="notification-icon">
                            <i class="bi bi-exclamation-triangle"></i>
                        </div>
                        <div>
                            <strong>Integrity check required</strong>
                            <p>The blockchain status requires attention.</p>
                        </div>
                    `;

        }

    };


/* =========================================================
   SETTINGS
========================================================= */

Dashboard.setupSettings = function () {

    const animationToggle =
        document.getElementById(
            "animationToggle"
        );

    const notificationToggle =
        document.getElementById(
            "notificationToggle"
        );

    const refreshToggle =
        document.getElementById(
            "refreshToggle"
        );


    if (animationToggle) {

        animationToggle.addEventListener(
            "click",
            () => {

                this.settings.animations =
                    !this.settings.animations;

                animationToggle.classList.toggle(
                    "active",
                    this.settings.animations
                );

                document.body.classList.toggle(
                    "no-animations",
                    !this.settings.animations
                );

                this.saveSettings();

                this.showToast(
                    "Animation setting updated",
                    this.settings.animations
                        ? "Dashboard animations enabled."
                        : "Dashboard animations disabled."
                );

            }
        );

    }


    if (notificationToggle) {

        notificationToggle.addEventListener(
            "click",
            () => {

                this.settings.notifications =
                    !this.settings.notifications;

                notificationToggle.classList.toggle(
                    "active",
                    this.settings.notifications
                );

                this.saveSettings();

                this.showToast(
                    "Notification setting updated",
                    this.settings.notifications
                        ? "Notifications enabled."
                        : "Notifications disabled."
                );

            }
        );

    }


    if (refreshToggle) {

        refreshToggle.addEventListener(
            "click",
            () => {

                this.settings.autoRefresh =
                    !this.settings.autoRefresh;

                refreshToggle.classList.toggle(
                    "active",
                    this.settings.autoRefresh
                );

                this.saveSettings();

                this.startAutoRefresh();

                this.showToast(
                    "Auto refresh updated",
                    this.settings.autoRefresh
                        ? "Automatic system refresh enabled."
                        : "Automatic system refresh disabled."
                );

            }
        );

    }

};


/* =========================================================
   LOAD SETTINGS
========================================================= */

Dashboard.loadSettings = function () {

    try {

        const saved =
            localStorage.getItem(
                "faceid_dashboard_settings"
            );

        if (saved) {

            this.settings =
                {
                    ...this.settings,
                    ...JSON.parse(saved)
                };

        }

    }

    catch (error) {

        console.warn(
            "Could not load dashboard settings."
        );

    }


    const animationToggle =
        document.getElementById(
            "animationToggle"
        );

    const notificationToggle =
        document.getElementById(
            "notificationToggle"
        );

    const refreshToggle =
        document.getElementById(
            "refreshToggle"
        );


    if (animationToggle) {

        animationToggle.classList.toggle(
            "active",
            this.settings.animations
        );

    }

    if (notificationToggle) {

        notificationToggle.classList.toggle(
            "active",
            this.settings.notifications
        );

    }

    if (refreshToggle) {

        refreshToggle.classList.toggle(
            "active",
            this.settings.autoRefresh
        );

    }

    document.body.classList.toggle(
        "no-animations",
        !this.settings.animations
    );

};


/* =========================================================
   SAVE SETTINGS
========================================================= */

Dashboard.saveSettings = function () {

    localStorage.setItem(
        "faceid_dashboard_settings",
        JSON.stringify(
            this.settings
        )
    );

};


/* =========================================================
   REGISTRY SEARCH
========================================================= */

Dashboard.setupRegistrySearch = function () {

    const search =
        document.getElementById(
            "registrySearch"
        );

    if (!search) {

        return;

    }

    search.addEventListener(
        "input",
        function () {

            const query =
                this.value
                    .trim()
                    .toLowerCase();

            const rows =
                document.querySelectorAll(
                    ".registry-table tbody tr"
                );

            rows.forEach(row => {

                const text =
                    row.textContent
                        .toLowerCase();

                row.style.display =
                    text.includes(query)
                        ? ""
                        : "none";

            });

        }
    );

};


/* =========================================================
   MOBILE SIDEBAR
========================================================= */

Dashboard.setupMobileMenu = function () {

    const button =
        document.getElementById(
            "mobileMenuButton"
        );

    const sidebar =
        document.getElementById(
            "sidebar"
        );

    if (!button || !sidebar) {

        return;

    }

    button.addEventListener(
        "click",
        function () {

            sidebar.classList.toggle(
                "open"
            );

        }
    );


    document.addEventListener(
        "click",
        function (event) {

            if (
                window.innerWidth <= 800 &&
                sidebar.classList.contains("open") &&
                !sidebar.contains(event.target) &&
                !button.contains(event.target)
            ) {

                sidebar.classList.remove(
                    "open"
                );

            }

        }
    );


    sidebar.querySelectorAll(
        ".sidebar-link"
    ).forEach(link => {

        link.addEventListener(
            "click",
            () => {

                if (window.innerWidth <= 800) {

                    sidebar.classList.remove(
                        "open"
                    );

                }

            }
        );

    });

};


/* =========================================================
   ADMIN DROPDOWN
========================================================= */

Dashboard.setupAdminPanel = function () {

    const button =
        document.getElementById(
            "adminButton"
        );

    const panel =
        document.getElementById(
            "adminPanel"
        );

    if (!button || !panel) {

        return;

    }

    button.addEventListener(
        "click",
        function (event) {

            event.stopPropagation();

            panel.classList.toggle(
                "show"
            );

        }
    );


    document.addEventListener(
        "click",
        function (event) {

            if (
                !panel.contains(event.target) &&
                !button.contains(event.target)
            ) {

                panel.classList.remove(
                    "show"
                );

            }

        }
    );

};


/* =========================================================
   ANIMATION REVEAL
========================================================= */

Dashboard.setupAnimations = function () {

    const elements =
        document.querySelectorAll(
            ".stat-card-modern, .dashboard-card, .security-status-card"
        );

    elements.forEach(
        (element, index) => {

            element.style.opacity = "0";

            element.style.transform =
                "translateY(12px)";

            setTimeout(
                () => {

                    element.style.transition =
                        "opacity .45s ease, transform .45s ease";

                    element.style.opacity =
                        "1";

                    element.style.transform =
                        "translateY(0)";

                },
                70 * index
            );

        }
    );

};


/* =========================================================
   TOAST
========================================================= */

Dashboard.showToast = function (
    title,
    message
) {

    let toast =
        document.getElementById(
            "dashboardToast"
        );

    if (!toast) {

        toast =
            document.createElement(
                "div"
            );

        toast.id =
            "dashboardToast";

        toast.className =
            "toast-modern";

        document.body.appendChild(
            toast
        );

    }

    toast.innerHTML = `
        <i class="bi bi-check-lg"></i>

        <div>
            <strong>${this.escapeHTML(title)}</strong>
            <p>${this.escapeHTML(message)}</p>
        </div>
    `;

    requestAnimationFrame(() => {

        toast.classList.add(
            "show"
        );

    });


    setTimeout(() => {

        toast.classList.remove(
            "show"
        );

    }, 3000);

};


/* =========================================================
   ESCAPE HTML
========================================================= */

Dashboard.escapeHTML = function (value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

};


/* =========================================================
   UPDATE SYSTEM LOG TIME
========================================================= */

Dashboard.getCurrentTime = function () {

    return new Intl.DateTimeFormat(
        "en-IN",
        {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: true,
            timeZone: "Asia/Kolkata"
        }
    ).format(new Date());

};


/* =========================================================
   VERIFICATION HISTORY
========================================================= */

Dashboard.saveVerificationHistory =
    function (result) {

        try {

            const history =
                JSON.parse(
                    localStorage.getItem(
                        "faceid_verification_history"
                    ) || "[]"
                );

            history.unshift({

                result:
                    result.result || "UNKNOWN",

                identity:
                    result.identity || "Unknown",

                similarity:
                    result.similarity || 0,

                timestamp:
                    new Date().toISOString()

            });


            const limited =
                history.slice(0, 50);

            localStorage.setItem(
                "faceid_verification_history",
                JSON.stringify(limited)
            );

        }

        catch (error) {

            console.warn(
                "Unable to save verification history."
            );

        }

    };


/* =========================================================
   LOAD VERIFICATION HISTORY
========================================================= */

Dashboard.loadVerificationHistory =
    function () {

        const container =
            document.getElementById(
                "verificationHistory"
            );

        if (!container) {

            return;

        }

        try {

            const history =
                JSON.parse(
                    localStorage.getItem(
                        "faceid_verification_history"
                    ) || "[]"
                );


            if (!history.length) {

                container.innerHTML = `
                    <div class="history-empty">
                        <i class="bi bi-clock-history"></i>
                        <h4>No verification history</h4>
                        <p>
                            Face verification activity will appear here.
                        </p>
                    </div>
                `;

                return;

            }


            container.innerHTML =
                history.map(item => {

                    const success =
                        String(item.result)
                            .toLowerCase()
                            .includes("success") ||
                        String(item.result)
                            .toLowerCase()
                            .includes("verified");

                    return `
                        <div class="activity-item">

                            <div class="activity-icon">
                                <i class="bi ${
                                    success
                                        ? "bi-shield-check"
                                        : "bi-shield-x"
                                }"></i>
                            </div>

                            <div class="activity-content">

                                <strong>
                                    ${
                                        success
                                            ? "Identity verified"
                                            : "Verification failed"
                                    }
                                </strong>

                                <p>
                                    ${
                                        this.escapeHTML(
                                            item.identity || "Unknown identity"
                                        )
                                    }

                                    ${
                                        item.similarity
                                            ? " • Similarity " +
                                              item.similarity +
                                              "%"
                                            : ""
                                    }
                                </p>

                            </div>

                            <span class="activity-time">
                                ${this.formatHistoryTime(
                                    item.timestamp
                                )}
                            </span>

                        </div>
                    `;

                }).join("");

        }

        catch (error) {

            console.warn(
                "Unable to load verification history."
            );

        }

    };


/* =========================================================
   HISTORY TIME
========================================================= */

Dashboard.formatHistoryTime =
    function (timestamp) {

        if (!timestamp) {

            return "Unknown";

        }

        const date =
            new Date(timestamp);

        return new Intl.DateTimeFormat(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
                hour: "2-digit",
                minute: "2-digit",
                hour12: true
            }
        ).format(date);

    };


/* =========================================================
   START DASHBOARD
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        Dashboard.init();

        Dashboard.setupAdminPanel();

        Dashboard.loadVerificationHistory();

    }
);