// Set fixed header margin once (based on full header size)
function setFixedHeaderMargin() {
    const header = document.querySelector('.header');
    const mainContent = document.querySelector('.main-content');
    
    if (header && mainContent) {
        // Ensure header is in full size to measure correctly
        header.classList.remove('scrolled');
        const fullHeaderHeight = header.offsetHeight;
        mainContent.style.marginTop = fullHeaderHeight + 'px';
        
        console.log(`Fixed margin set to: ${fullHeaderHeight}px`);
    }
}

// Set margin once on load and resize, but never change it during scroll
window.addEventListener('load', setFixedHeaderMargin);
window.addEventListener('resize', setFixedHeaderMargin);

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    if (mobileToggle) {
        mobileToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            const navMenu = document.querySelector('.nav-menu');
            navMenu.classList.toggle('active');
            console.log('Mobile menu toggled'); // Debug log
        });
    }
});

// Handle mobile dropdown toggles
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            // Only handle on mobile
            if (window.innerWidth <= 768) {
                const parentItem = this.closest('.nav-item');
                const dropdown = parentItem.querySelector('.dropdown');
                
                if (dropdown) {
                    e.preventDefault();
                    
                    // Close all other dropdowns
                    document.querySelectorAll('.nav-item.active').forEach(item => {
                        if (item !== parentItem) {
                            item.classList.remove('active');
                        }
                    });
                    
                    // Toggle current dropdown
                    parentItem.classList.toggle('active');
                    return;
                }
                
                // Close mobile menu for non-dropdown links
                document.querySelector('.nav-menu').classList.remove('active');
                document.querySelectorAll('.nav-item.active').forEach(item => {
                    item.classList.remove('active');
                });
            }
        });
    });
});

// Close dropdowns when clicking outside on mobile
document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768) {
            const navMenu = document.querySelector('.nav-menu');
            const clickedInsideNav = e.target.closest('.nav-menu');
            const clickedToggle = e.target.closest('.mobile-menu-toggle');
            
            if (!clickedInsideNav && !clickedToggle && navMenu && navMenu.classList.contains('active')) {
                // Close all dropdowns
                document.querySelectorAll('.nav-item.active').forEach(item => {
                    item.classList.remove('active');
                    console.log('Closed dropdown due to outside click'); // Debug log
                });
            }
        }
    });
});

// Header scroll behavior
let lastScrollTop = 0;
let currentState = 'large';
const header = document.querySelector('.header');
let ticking = false;

function updateHeader() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const THRESHOLD = 100;
    
    if (scrollTop > THRESHOLD && currentState === 'large') {
        header.classList.add('scrolled');
        currentState = 'small';
    } else if (scrollTop <= THRESHOLD && currentState === 'small') {
        header.classList.remove('scrolled');
        currentState = 'large';
    }
    
    lastScrollTop = scrollTop;
}

window.addEventListener('scroll', function() {
    if (!ticking) {
        ticking = true;
        requestAnimationFrame(function() {
            updateHeader(); // Only update header, no margin changes
            ticking = false;
        });
    }
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});