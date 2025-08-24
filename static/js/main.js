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
document.querySelector('.mobile-menu-toggle').addEventListener('click', function() {
    const navMenu = document.querySelector('.nav-menu');
    navMenu.classList.toggle('active');
});

// Close mobile menu when clicking on a link
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
        if (window.innerWidth <= 768) {
            const parentItem = this.closest('.nav-item');
            const dropdown = parentItem.querySelector('.dropdown');
            
            if (dropdown) {
                e.preventDefault();
                parentItem.classList.toggle('active');
                
                document.querySelectorAll('.nav-item.active').forEach(item => {
                    if (item !== parentItem) {
                        item.classList.remove('active');
                    }
                });
                return;
            }
        }
        
        const navMenu = document.querySelector('.nav-menu');
        navMenu.classList.remove('active');
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