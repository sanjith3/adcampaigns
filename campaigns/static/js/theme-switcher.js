// Theme Switcher for AdSoft
class ThemeManager {
    constructor() {
        this.themes = ['light', 'dark'];
        this.currentTheme = this.getStoredTheme() || 'light';
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.createThemeSwitcher();
        this.addThemeChangeListeners();
    }

    getStoredTheme() {
        return localStorage.getItem('adsoft-theme');
    }

    setStoredTheme(theme) {
        localStorage.setItem('adsoft-theme', theme);
    }

    applyTheme(theme) {
        // Remove all theme classes
        document.body.classList.remove('dark-theme');
        
        // Apply selected theme
        if (theme !== 'light') {
            document.body.classList.add(`${theme}-theme`);
        }
        
        this.currentTheme = theme;
        this.setStoredTheme(theme);
        
        // Update theme switcher UI
        this.updateThemeSwitcherUI();
        
        // Dispatch theme change event
        document.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    }

    createThemeSwitcher() {
        // Create theme switcher button if it doesn't exist
        if (!document.getElementById('theme-switcher')) {
            const themeSwitcher = document.createElement('div');
            themeSwitcher.id = 'theme-switcher';
            themeSwitcher.className = 'theme-switcher';
            themeSwitcher.innerHTML = `
                <button class="theme-btn" id="theme-toggle">
                    <i class="fas fa-palette"></i>
                </button>
                <div class="theme-options" id="theme-options" style="display: none;">
                    <button class="theme-option" data-theme="light">
                        <i class="fas fa-sun"></i> Light
                    </button>
                    <button class="theme-option" data-theme="dark">
                        <i class="fas fa-moon"></i> Dark
                    </button>
                   
                </div>
            `;
            document.body.appendChild(themeSwitcher);
        }
    }

    updateThemeSwitcherUI() {
        const themeOptions = document.querySelectorAll('.theme-option');
        themeOptions.forEach(option => {
            option.classList.remove('active');
            if (option.dataset.theme === this.currentTheme) {
                option.classList.add('active');
            }
        });
    }

    addThemeChangeListeners() {
        // Toggle theme options
        document.addEventListener('click', (e) => {
            if (e.target.id === 'theme-toggle' || e.target.closest('#theme-toggle')) {
                const options = document.getElementById('theme-options');
                options.style.display = options.style.display === 'none' ? 'block' : 'none';
            }

            // Change theme
            if (e.target.classList.contains('theme-option')) {
                const theme = e.target.dataset.theme;
                this.applyTheme(theme);
                document.getElementById('theme-options').style.display = 'none';
            }

            // Close options when clicking outside
            if (!e.target.closest('.theme-switcher')) {
                document.getElementById('theme-options').style.display = 'none';
            }
        });
    }

    nextTheme() {
        const currentIndex = this.themes.indexOf(this.currentTheme);
        const nextIndex = (currentIndex + 1) % this.themes.length;
        this.applyTheme(this.themes[nextIndex]);
    }
}

// Initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.themeManager = new ThemeManager();
    
    // Add keyboard shortcut (Alt+T) to cycle themes
    document.addEventListener('keydown', function(e) {
        if (e.altKey && e.key === 't') {
            e.preventDefault();
            window.themeManager.nextTheme();
        }
    });
});