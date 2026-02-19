from __future__ import annotations

import streamlit.components.v1 as components


def render_navigation_menu(tab_names: list[str]) -> None:
    nav_js = _build_navigation_js(tab_names)
    components.html(nav_js, height=0)


def _build_navigation_js(tab_names: list[str]) -> str:
    return """
<script>
(function() {
    var storageKey = 'stockmonitor_active_tab';
    var tabNames = """ + str(tab_names) + """;
    var doc = window.parent.document;
    var store = window.parent.sessionStorage;

    function getTabsContainer() {
        return doc.querySelector('div[data-testid="stTabs"]');
    }

    function getAllTabs() {
        return doc.querySelectorAll('button[data-baseweb="tab"]');
    }

    function restoreSavedTab() {
        var saved = store.getItem(storageKey);
        if (saved === null) return;
        var idx = parseInt(saved);
        if (isNaN(idx) || idx <= 0) return;
        var tabs = getAllTabs();
        if (idx >= tabs.length) return;
        if (tabs[idx].getAttribute('aria-selected') === 'true') return;
        tabs[idx].click();
    }

    function restoreSavedTabWithRetry(attempts) {
        var tabs = getAllTabs();
        if (tabs.length === 0 && attempts > 0) {
            setTimeout(function() { restoreSavedTabWithRetry(attempts - 1); }, 100);
            return;
        }
        restoreSavedTab();
    }

    function injectNavMenu() {
        var tabsContainer = getTabsContainer();
        if (!tabsContainer) return false;

        if (doc.getElementById('nav-menu-injected')) return true;

        var navHtml = '<div id="nav-menu-injected" style="position:absolute;left:-40px;top:0;z-index:1000;">' +
            '<button id="nav-btn" style="background:transparent;border:none;font-size:20px;cursor:pointer;padding:4px 8px;border-radius:4px;">☰</button>' +
            '<div id="nav-dropdown" style="display:none;position:absolute;top:100%;left:0;background:white;border:1px solid #ddd;border-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,0.15);min-width:220px;padding:4px;">';

        for (var i = 0; i < tabNames.length; i++) {
            navHtml += '<button class="nav-item" data-idx="' + i + '" style="display:block;width:100%;padding:6px 10px;border:none;background:transparent;text-align:left;cursor:pointer;font-size:12px;border-radius:3px;">' + tabNames[i] + '</button>';
        }
        navHtml += '</div></div>';

        tabsContainer.style.position = 'relative';
        tabsContainer.style.marginLeft = '45px';
        tabsContainer.insertAdjacentHTML('afterbegin', navHtml);

        var btn = doc.getElementById('nav-btn');
        var dropdown = doc.getElementById('nav-dropdown');

        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
        });

        dropdown.querySelectorAll('.nav-item').forEach(function(item) {
            item.addEventListener('mouseover', function() { this.style.background = '#f5f5f5'; });
            item.addEventListener('mouseout', function() { this.style.background = 'transparent'; });
            item.addEventListener('click', function() {
                var idx = parseInt(this.getAttribute('data-idx'));
                var tabs = getAllTabs();
                if (tabs[idx]) {
                    store.setItem(storageKey, idx);
                    tabs[idx].click();
                }
                dropdown.style.display = 'none';
            });
        });
        return true;
    }

    function setupTabTracking() {
        if (window.parent._tabTrackingSetup) return;
        window.parent._tabTrackingSetup = true;

        doc.addEventListener('click', function(e) {
            var tab = e.target.closest('button[data-baseweb="tab"]');
            if (tab) {
                var tabs = getAllTabs();
                var idx = Array.from(tabs).indexOf(tab);
                if (idx >= 0) {
                    store.setItem(storageKey, idx);
                }
            }

            var dropdown = doc.getElementById('nav-dropdown');
            if (dropdown && !e.target.closest('#nav-menu-injected')) {
                dropdown.style.display = 'none';
            }
        });
    }

    function setupMutationObserver() {
        if (window.parent._navObserver) {
            window.parent._navObserver.disconnect();
        }

        var debounceTimer = null;
        var observer = new MutationObserver(function() {
            if (debounceTimer) return;
            debounceTimer = setTimeout(function() {
                debounceTimer = null;
                if (getTabsContainer() && !doc.getElementById('nav-menu-injected')) {
                    injectNavMenu();
                }
            }, 200);
        });

        observer.observe(doc.querySelector('[data-testid="stAppViewContainer"]') || doc.body, {
            childList: true,
            subtree: true
        });

        window.parent._navObserver = observer;
    }

    if (window.parent._navInterval) {
        clearInterval(window.parent._navInterval);
    }

    setTimeout(function() {
        injectNavMenu();
        setupTabTracking();
        setupMutationObserver();
        restoreSavedTabWithRetry(10);

        window.parent._navInterval = setInterval(function() {
            if (!doc.getElementById('nav-menu-injected')) {
                injectNavMenu();
            }
        }, 2000);
    }, 200);
})();
</script>
"""
