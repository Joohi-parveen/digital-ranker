// Force light mode and clean up any lingering dark styles
(function() {
    localStorage.setItem("jazzmin-theme-mode", "light");
    
    // Run immediately to prevent flash of dark background
    if (document.body) {
        document.body.classList.remove("dark-mode");
    }
    
    // Also run on DOM content loaded to ensure all classes are resolved
    document.addEventListener("DOMContentLoaded", function() {
        document.body.classList.remove("dark-mode");
        
        // Ensure sidebar is styled light
        const sidebar = document.querySelector(".main-sidebar");
        if (sidebar) {
            sidebar.classList.remove("sidebar-dark-primary");
            sidebar.classList.add("sidebar-light-primary");
        }
        
        // Ensure navbar header is styled light
        const navbar = document.querySelector(".main-header");
        if (navbar) {
            navbar.classList.remove("navbar-dark");
            navbar.classList.remove("navbar-primary");
            navbar.classList.add("navbar-light");
            navbar.classList.add("navbar-white");
        }
    });
})();
