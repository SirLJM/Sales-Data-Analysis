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

    function getTabsContainer() {
        return window.parent.document.querySelector('div[data-testid="stTabs"]');
    }

    function getAllTabs() {
        return window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
    }

    function getCurrentTabIndex() {
        var tabs = getAllTabs();
        for (var i = 0; i < tabs.length; i++) {
            if (tabs[i].getAttribute('aria-selected') === 'true') return i;
        }
        return 0;
    }

    function injectNavMenu() {
        var tabsContainer = getTabsContainer();
        if (!tabsContainer) return false;

        var existingNav = window.parent.document.getElementById('nav-menu-injected');
        if (existingNav) return true;

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

        var btn = window.parent.document.getElementById('nav-btn');
        var dropdown = window.parent.document.getElementById('nav-dropdown');

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

        window.parent.document.addEventListener('click', function(e) {
            var tab = e.target.closest('button[data-baseweb="tab"]');
            if (tab) {
                var tabs = getAllTabs();
                var idx = Array.from(tabs).indexOf(tab);
                if (idx >= 0) {
                    window.parent.sessionStorage.setItem(storageKey, idx);
                }
            }

            var dropdown = window.parent.document.getElementById('nav-dropdown');
            if (dropdown && !e.target.closest('#nav-menu-injected')) {
                dropdown.style.display = 'none';
            }
        });
    }

    function setupMutationObserver() {
        if (window.parent._navObserver) {
            window.parent._navObserver.disconnect();
        }

        var observer = new MutationObserver(function(mutations) {
            var tabsContainer = getTabsContainer();
            if (tabsContainer && !window.parent.document.getElementById('nav-menu-injected')) {
                injectNavMenu();
            }
        });

        observer.observe(window.parent.document.body, {
            childList: true,
            subtree: true
        });

        window.parent._navObserver = observer;
    }

    function ensureNavExists() {
        var navExists = window.parent.document.getElementById('nav-menu-injected');
        if (!navExists) {
            injectNavMenu();
        }
    }

    setTimeout(function() {
        injectNavMenu();
        setupTabTracking();
        setupMutationObserver();
        setInterval(ensureNavExists, 500);
    }, 100);
})();
</script>
"""
