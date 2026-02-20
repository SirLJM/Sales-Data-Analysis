from __future__ import annotations

import streamlit.components.v1 as components


def render_navigation_menu(tab_names: list[str]) -> None:
    nav_js = _build_navigation_js(tab_names)
    components.html(nav_js, height=0)


def _build_navigation_js(tab_names: list[str]) -> str:
    return """
<script>
(function() {
    try {
    var storageKey = 'stockmonitor_active_tab';
    var tabNames = """ + str(tab_names) + """;
    var doc = window.parent.document;
    var store = window.parent.sessionStorage;
    var NAV_ID = 'nav-menu-injected';
    var STYLE_ID = 'nav-menu-style';
    var TIMER_KEY = '_navPollTimer';

    function cleanup() {
        try {
            var oldNav = doc.getElementById(NAV_ID);
            if (oldNav) oldNav.remove();
            var oldStyle = doc.getElementById(STYLE_ID);
            if (oldStyle) oldStyle.remove();
            if (window.parent[TIMER_KEY]) {
                clearTimeout(window.parent[TIMER_KEY]);
                window.parent[TIMER_KEY] = null;
            }
        } catch(e) {}
    }

    function getTabsContainer() {
        try { return doc.querySelector('div[data-testid="stTabs"]'); }
        catch(e) { return null; }
    }

    function getAllTabs() {
        try { return doc.querySelectorAll('button[data-baseweb="tab"]'); }
        catch(e) { return []; }
    }

    function restoreSavedTab() {
        try {
            var saved = store.getItem(storageKey);
            if (saved === null) return;
            var idx = parseInt(saved);
            if (isNaN(idx) || idx <= 0) return;
            var tabs = getAllTabs();
            if (idx >= tabs.length) return;
            if (tabs[idx].getAttribute('aria-selected') === 'true') return;
            tabs[idx].click();
        } catch(e) {}
    }

    function restoreSavedTabWithRetry(attempts) {
        try {
            var tabs = getAllTabs();
            if (tabs.length === 0 && attempts > 0) {
                setTimeout(function() { restoreSavedTabWithRetry(attempts - 1); }, 100);
                return;
            }
            restoreSavedTab();
        } catch(e) {}
    }

    function injectNavStyle() {
        try {
            if (doc.getElementById(STYLE_ID)) return;
            var style = doc.createElement('style');
            style.id = STYLE_ID;
            style.textContent =
                '#' + NAV_ID + ' { position: absolute; left: -40px; top: 0; z-index: 1000; }' +
                '#nav-btn { background: transparent; border: none; font-size: 20px; cursor: pointer; padding: 4px 8px; border-radius: 4px; }' +
                '#nav-btn:hover { background: rgba(0,0,0,0.05); }' +
                '#nav-dropdown { display: none; position: absolute; top: 100%; left: 0; background: white; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); min-width: 220px; padding: 4px; }' +
                '.nav-item { display: block; width: 100%; padding: 6px 10px; border: none; background: transparent; text-align: left; cursor: pointer; font-size: 12px; border-radius: 3px; }' +
                '.nav-item:hover { background: #f5f5f5; }';
            doc.head.appendChild(style);
        } catch(e) {}
    }

    function injectNavMenu() {
        try {
            var tabsContainer = getTabsContainer();
            if (!tabsContainer) return false;
            if (doc.getElementById(NAV_ID)) return true;

            injectNavStyle();

            var nav = doc.createElement('div');
            nav.id = NAV_ID;

            var btnEl = doc.createElement('button');
            btnEl.id = 'nav-btn';
            btnEl.textContent = '\\u2630';
            nav.appendChild(btnEl);

            var dropdownEl = doc.createElement('div');
            dropdownEl.id = 'nav-dropdown';

            for (var i = 0; i < tabNames.length; i++) {
                var item = doc.createElement('button');
                item.className = 'nav-item';
                item.setAttribute('data-idx', i);
                item.textContent = tabNames[i];
                dropdownEl.appendChild(item);
            }
            nav.appendChild(dropdownEl);

            tabsContainer.parentNode.insertBefore(nav, tabsContainer);

            btnEl.addEventListener('click', function(e) {
                try {
                    e.stopPropagation();
                    dropdownEl.style.display = dropdownEl.style.display === 'none' ? 'block' : 'none';
                } catch(err) {}
            });

            dropdownEl.addEventListener('click', function(e) {
                try {
                    var target = e.target.closest('.nav-item');
                    if (!target) return;
                    var idx = parseInt(target.getAttribute('data-idx'));
                    var tabs = getAllTabs();
                    if (tabs[idx]) {
                        store.setItem(storageKey, idx);
                        tabs[idx].click();
                    }
                    dropdownEl.style.display = 'none';
                } catch(err) {}
            });

            return true;
        } catch(e) { return false; }
    }

    function setupTabTracking() {
        try {
            if (window.parent._tabTrackingSetup) return;
            window.parent._tabTrackingSetup = true;

            doc.addEventListener('click', function(e) {
                try {
                    var tab = e.target.closest('button[data-baseweb="tab"]');
                    if (tab) {
                        var tabs = getAllTabs();
                        var idx = Array.from(tabs).indexOf(tab);
                        if (idx >= 0) {
                            store.setItem(storageKey, idx);
                        }
                    }
                    var dropdown = doc.getElementById('nav-dropdown');
                    if (dropdown && !e.target.closest('#' + NAV_ID)) {
                        dropdown.style.display = 'none';
                    }
                } catch(err) {}
            });
        } catch(e) {}
    }

    function schedulePoll() {
        try {
            window.parent[TIMER_KEY] = setTimeout(function() {
                try {
                    if (!doc.getElementById(NAV_ID)) {
                        injectNavMenu();
                    }
                    schedulePoll();
                } catch(e) { schedulePoll(); }
            }, 1500);
        } catch(e) {}
    }

    cleanup();

    setTimeout(function() {
        try {
            injectNavMenu();
            setupTabTracking();
            schedulePoll();
            restoreSavedTabWithRetry(10);
        } catch(e) {}
    }, 200);

    } catch(e) {}
})();
</script>
"""
