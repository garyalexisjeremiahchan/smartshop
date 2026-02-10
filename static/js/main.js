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

    // AI-Powered Search with Autocomplete and Debounce
    const searchInput = document.getElementById('searchInput');
    const autocompleteDropdown = document.getElementById('autocompleteDropdown');
    const autocompleteList = document.getElementById('autocompleteList');
    const searchForm = document.getElementById('searchForm');
    
    // Debug: Check if elements exist
    if (!searchInput) {
        console.warn('Search input element not found');
    }
    if (!autocompleteDropdown) {
        console.warn('Autocomplete dropdown element not found');
    }
    if (!autocompleteList) {
        console.warn('Autocomplete list element not found');
    }
    if (!searchForm) {
        console.warn('Search form element not found');
    }
    
    let debounceTimer;
    let currentFocus = -1;
    
    // Debounce function - delays execution until user stops typing
    function debounce(func, delay) {
        return function(...args) {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => func.apply(this, args), delay);
        };
    }
    
    // Fetch autocomplete suggestions from API
    async function fetchAutocomplete(query) {
        try {
            // Add loading indicator
            searchInput.classList.add('search-loading');
            
            const response = await fetch(`/api/autocomplete/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            // Remove loading indicator
            searchInput.classList.remove('search-loading');
            
            return data.suggestions || [];
        } catch (error) {
            console.error('Autocomplete error:', error);
            searchInput.classList.remove('search-loading');
            return [];
        }
    }
    
    // Display autocomplete suggestions
    function displayAutocomplete(suggestions) {
        autocompleteList.innerHTML = '';
        
        if (suggestions.length === 0) {
            autocompleteDropdown.style.display = 'none';
            return;
        }
        
        suggestions.forEach((suggestion, index) => {
            const li = document.createElement('li');
            li.innerHTML = `
                <i class="bi bi-search me-2"></i>
                <span>${highlightMatch(suggestion, searchInput.value)}</span>
            `;
            li.setAttribute('data-value', suggestion);
            li.setAttribute('data-index', index);
            
            // Click handler
            li.addEventListener('click', function() {
                selectSuggestion(suggestion);
            });
            
            autocompleteList.appendChild(li);
        });
        
        autocompleteDropdown.style.display = 'block';
        currentFocus = -1;
    }
    
    // Highlight matching text in suggestions
    function highlightMatch(text, query) {
        if (!query) return text;
        
        const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
        return text.replace(regex, '<strong>$1</strong>');
    }
    
    // Escape special regex characters
    function escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    // Select a suggestion
    function selectSuggestion(value) {
        searchInput.value = value;
        autocompleteDropdown.style.display = 'none';
        searchForm.submit();
    }
    
    // Navigate suggestions with keyboard
    function navigateSuggestions(direction) {
        const items = autocompleteList.querySelectorAll('li');
        if (items.length === 0) return;
        
        // Remove active class from all
        items.forEach(item => item.classList.remove('active'));
        
        // Update focus
        currentFocus += direction;
        
        // Loop around
        if (currentFocus >= items.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = items.length - 1;
        
        // Add active class
        items[currentFocus].classList.add('active');
        items[currentFocus].scrollIntoView({ block: 'nearest' });
    }
    
    // Handle search input events
    if (searchInput && autocompleteDropdown && autocompleteList && searchForm) {
        console.log('AI Search autocomplete initialized successfully');
        
        // Input event with debounce
        searchInput.addEventListener('input', debounce(async function(e) {
            const query = e.target.value.trim();
            console.log('Search input:', query);
            
            if (query.length >= 2) {
                console.log('Fetching autocomplete for:', query);
                const suggestions = await fetchAutocomplete(query);
                console.log('Received suggestions:', suggestions);
                displayAutocomplete(suggestions);
            } else if (query.length === 0) {
                // Show trending searches when input is empty
                const suggestions = await fetchAutocomplete('');
                displayAutocomplete(suggestions);
            } else {
                autocompleteDropdown.style.display = 'none';
            }
        }, 300)); // 300ms debounce delay
        
        // Focus event - show trending if empty
        searchInput.addEventListener('focus', async function(e) {
            if (!e.target.value.trim()) {
                const suggestions = await fetchAutocomplete('');
                displayAutocomplete(suggestions);
            } else if (autocompleteList.children.length > 0) {
                autocompleteDropdown.style.display = 'block';
            }
        });
        
        // Keyboard navigation
        searchInput.addEventListener('keydown', function(e) {
            const items = autocompleteList.querySelectorAll('li');
            
            switch(e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    navigateSuggestions(1);
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    navigateSuggestions(-1);
                    break;
                case 'Enter':
                    if (currentFocus > -1 && items[currentFocus]) {
                        e.preventDefault();
                        const value = items[currentFocus].getAttribute('data-value');
                        selectSuggestion(value);
                    }
                    break;
                case 'Escape':
                    autocompleteDropdown.style.display = 'none';
                    currentFocus = -1;
                    break;
            }
        });
        
        // Close autocomplete when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchForm.contains(e.target)) {
                autocompleteDropdown.style.display = 'none';
                currentFocus = -1;
            }
        });
        
        console.log('✓ All event listeners attached successfully');
    } else {
        console.error('AI Search autocomplete could not initialize - missing required elements');
    }

    // Search form enhancement (original code removed - using autocomplete instead)
    // const searchForm = document.querySelector('form[action*="categories"]');
    // ... removed old code ...

    // Smooth scroll to top
    const scrollToTop = document.createElement('button');
    scrollToTop.innerHTML = '<i class="bi bi-arrow-up"></i>';
    scrollToTop.className = 'btn btn-primary rounded-circle position-fixed bottom-0 start-0 m-3';
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
