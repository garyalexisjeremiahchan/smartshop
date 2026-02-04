// SmartShop JavaScript

document.addEventListener('DOMContentLoaded', function() {
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Quantity input validation
    const quantityInputs = document.querySelectorAll('input[type="number"][name="quantity"]');
    quantityInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const min = parseInt(this.min) || 1;
            const max = parseInt(this.max) || Infinity;
            let value = parseInt(this.value);

            if (value < min) {
                this.value = min;
            } else if (value > max) {
                this.value = max;
                alert(`Maximum ${max} items available.`);
            }
        });
    });

    // Search form enhancement
    const searchForm = document.querySelector('form[action*="categories"]');
    if (searchForm) {
        const searchInput = searchForm.querySelector('input[name="search"]');
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                // You can add live search functionality here
            });
        }
    }

    // Smooth scroll to top
    const scrollToTop = document.createElement('button');
    scrollToTop.innerHTML = '<i class="bi bi-arrow-up"></i>';
    scrollToTop.className = 'btn btn-primary rounded-circle position-fixed bottom-0 end-0 m-3';
    scrollToTop.style.cssText = 'width: 50px; height: 50px; display: none; z-index: 1000;';
    document.body.appendChild(scrollToTop);

    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            scrollToTop.style.display = 'block';
        } else {
            scrollToTop.style.display = 'none';
        }
    });

    scrollToTop.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // Cart update confirmation
    const removeButtons = document.querySelectorAll('form[action*="remove-from-cart"] button');
    removeButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to remove this item from cart?')) {
                e.preventDefault();
            }
        });
    });

    // Image preview for product images
    const thumbnails = document.querySelectorAll('.img-thumbnail[onclick]');
    thumbnails.forEach(function(thumb) {
        thumb.style.cursor = 'pointer';
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Navbar dropdown hover (desktop only)
    if (window.innerWidth > 992) {
        const dropdowns = document.querySelectorAll('.navbar .dropdown');
        dropdowns.forEach(function(dropdown) {
            dropdown.addEventListener('mouseenter', function() {
                const dropdownToggle = this.querySelector('.dropdown-toggle');
                const dropdownMenu = this.querySelector('.dropdown-menu');
                if (dropdownToggle && dropdownMenu) {
                    dropdownToggle.classList.add('show');
                    dropdownMenu.classList.add('show');
                }
            });
            dropdown.addEventListener('mouseleave', function() {
                const dropdownToggle = this.querySelector('.dropdown-toggle');
                const dropdownMenu = this.querySelector('.dropdown-menu');
                if (dropdownToggle && dropdownMenu) {
                    dropdownToggle.classList.remove('show');
                    dropdownMenu.classList.remove('show');
                }
            });
        });
    }

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});
