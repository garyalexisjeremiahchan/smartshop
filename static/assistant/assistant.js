/**
 * Shopping Assistant - Frontend JavaScript
 * Handles chat interface, API communication, and UI interactions
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        chatEndpoint: '/assistant/chat/',
        maxMessageLength: 500,
        typingDelay: 300
    };

    // State
    let conversationId = null;
    let isOpen = false;
    let isLoading = false;

    // DOM Elements
    const elements = {
        fab: null,
        drawer: null,
        overlay: null,
        closeBtn: null,
        messagesContainer: null,
        form: null,
        input: null,
        sendBtn: null,
        loading: null,
        suggestions: null,
        welcome: null
    };

    /**
     * Initialize the assistant widget
     */
    function init() {
        // Get DOM elements
        elements.fab = document.getElementById('assistant-fab');
        elements.drawer = document.getElementById('assistant-drawer');
        elements.overlay = document.getElementById('assistant-overlay');
        elements.closeBtn = document.getElementById('assistant-close');
        elements.messagesContainer = document.getElementById('assistant-messages');
        elements.form = document.getElementById('assistant-form');
        elements.input = document.getElementById('assistant-input');
        elements.sendBtn = document.getElementById('assistant-send');
        elements.loading = document.getElementById('assistant-loading');
        elements.suggestions = document.getElementById('assistant-suggestions');
        elements.welcome = document.getElementById('assistant-welcome');

        if (!elements.fab || !elements.drawer) {
            console.error('Assistant: Required elements not found');
            return;
        }

        // Event listeners
        elements.fab.addEventListener('click', openDrawer);
        elements.closeBtn.addEventListener('click', closeDrawer);
        elements.overlay.addEventListener('click', closeDrawer);
        elements.form.addEventListener('submit', handleSubmit);

        // Suggestion chips
        const suggestionChips = document.querySelectorAll('.assistant-suggestion-chip');
        suggestionChips.forEach(chip => {
            chip.addEventListener('click', function() {
                const message = this.dataset.message;
                if (message) {
                    sendMessage(message);
                }
            });
        });

        // Add initial New Chat button
        addNewChatButton();

        // Load conversation ID from localStorage
        conversationId = localStorage.getItem('assistant_conversation_id');

        // Restore chat history from sessionStorage
        restoreChatHistory();

        console.log('Assistant: Initialized');
    }

    /**
     * Open the chat drawer
     */
    function openDrawer() {
        isOpen = true;
        elements.drawer.classList.remove('collapsed');
        elements.overlay.classList.add('active');
        elements.input.focus();

        // Show welcome message on first open
        const hasOpenedBefore = localStorage.getItem('assistant_opened');
        if (!hasOpenedBefore && elements.welcome) {
            elements.welcome.style.display = 'block';
            localStorage.setItem('assistant_opened', 'true');
        }

        // Scroll to bottom
        scrollToBottom();
    }

    /**
     * Close the chat drawer
     */
    function closeDrawer() {
        isOpen = false;
        elements.drawer.classList.add('collapsed');
        elements.overlay.classList.remove('active');
    }

    /**
     * Handle form submission
     */
    function handleSubmit(e) {
        e.preventDefault();

        const message = elements.input.value.trim();
        if (!message || isLoading) return;

        sendMessage(message);
    }

    /**
     * Send a message to the assistant
     */
    async function sendMessage(message) {
        if (isLoading) return;

        // Clear input
        elements.input.value = '';

        // Add user message to UI
        addMessage(message, 'user');

        // Hide welcome message if visible
        if (elements.welcome) {
            elements.welcome.style.display = 'none';
        }

        // Show loading indicator
        setLoading(true);

        // Get page context
        const pageContext = getPageContext();

        try {
            // Get CSRF token
            const csrfToken = getCsrfToken();

            // Send request
            const response = await fetch(CONFIG.chatEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: conversationId,
                    page_context: pageContext
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Store conversation ID
            if (data.conversation_id) {
                conversationId = data.conversation_id;
                localStorage.setItem('assistant_conversation_id', conversationId);
            }

            // Add assistant response to UI
            addMessage(data.reply, 'assistant', data.cards);

            // Update suggestions
            if (data.suggestions && data.suggestions.length > 0) {
                updateSuggestions(data.suggestions);
            }

        } catch (error) {
            console.error('Assistant: Error sending message', error);
            addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
        } finally {
            setLoading(false);
        }
    }

    /**
     * Add a message to the chat
     */
    function addMessage(text, role, cards = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `assistant-message assistant-message-${role}`;

        // Avatar
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'assistant-avatar';
        
        if (role === 'assistant') {
            avatarDiv.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01"></path>
                </svg>
            `;
        } else {
            avatarDiv.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                </svg>
            `;
        }

        // Content
        const contentDiv = document.createElement('div');
        contentDiv.className = 'assistant-message-content';

        const textP = document.createElement('p');
        // Convert markdown-style links to HTML links
        const htmlText = convertMarkdownLinks(text);
        textP.innerHTML = htmlText;
        contentDiv.appendChild(textP);

        // Add product cards if present
        if (cards && cards.length > 0) {
            const cardsContainer = document.createElement('div');
            cardsContainer.className = 'assistant-product-cards';

            cards.forEach(card => {
                const cardEl = createProductCard(card);
                cardsContainer.appendChild(cardEl);
            });

            contentDiv.appendChild(cardsContainer);
        }

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        elements.messagesContainer.appendChild(messageDiv);
        scrollToBottom();

        // Save to session storage
        saveChatHistory();
    }

    /**
     * Create a product card element
     */
    function createProductCard(product) {
        const card = document.createElement('a');
        card.className = 'assistant-product-card';
        card.href = product.url;

        // Image
        const img = document.createElement('img');
        img.className = 'assistant-product-image';
        img.src = product.image_url || 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23f0f0f0" width="200" height="200"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" font-family="Arial" font-size="16"%3ENo Image%3C/text%3E%3C/svg%3E';
        img.alt = product.title;
        img.onerror = function() {
            this.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23f0f0f0" width="200" height="200"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" font-family="Arial" font-size="16"%3ENo Image%3C/text%3E%3C/svg%3E';
        };

        // Info
        const info = document.createElement('div');
        info.className = 'assistant-product-info';

        const title = document.createElement('h6');
        title.className = 'assistant-product-title';
        title.textContent = product.title;

        const meta = document.createElement('div');
        meta.className = 'assistant-product-meta';

        const price = document.createElement('span');
        price.className = 'assistant-product-price';
        price.textContent = `$${product.price.toFixed(2)}`;

        meta.appendChild(price);

        // Rating
        if (product.rating > 0) {
            const rating = document.createElement('span');
            rating.className = 'assistant-product-rating';
            rating.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                </svg>
                ${product.rating.toFixed(1)}
            `;
            meta.appendChild(rating);
        }

        // Stock badge
        const badge = document.createElement('span');
        badge.className = `assistant-product-badge ${product.stock_status.replace('_', '-')}`;
        
        if (product.stock_status === 'in_stock') {
            badge.textContent = 'In Stock';
        } else if (product.stock_status === 'low_stock') {
            badge.textContent = 'Low Stock';
        } else {
            badge.textContent = 'Out of Stock';
        }

        info.appendChild(title);
        info.appendChild(meta);
        info.appendChild(badge);

        card.appendChild(img);
        card.appendChild(info);

        return card;
    }

    /**
     * Update suggestion chips
     */
    function updateSuggestions(suggestions) {
        if (!elements.suggestions) return;

        elements.suggestions.innerHTML = '';

        suggestions.forEach(suggestion => {
            const chip = document.createElement('button');
            chip.className = 'assistant-suggestion-chip';
            chip.textContent = suggestion;
            chip.dataset.message = suggestion;
            chip.addEventListener('click', function() {
                sendMessage(this.dataset.message);
            });

            elements.suggestions.appendChild(chip);
        });

        // Always add "New Chat" button
        addNewChatButton();
    }

    /**
     * Add New Chat button to suggestions
     */
    function addNewChatButton() {
        if (!elements.suggestions) return;

        const newChatChip = document.createElement('button');
        newChatChip.className = 'assistant-suggestion-chip new-chat';
        newChatChip.innerHTML = `
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 4px; vertical-align: text-bottom;">
                <polyline points="1 4 1 10 7 10"></polyline>
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
            </svg>
            New Chat
        `;
        newChatChip.title = 'Start a new conversation';
        newChatChip.addEventListener('click', clearChat);

        elements.suggestions.appendChild(newChatChip);
    }

    /**
     * Clear chat and start new conversation
     */
    function clearChat() {
        // Confirm with user
        if (elements.messagesContainer.children.length > 0) {
            if (!confirm('Are you sure you want to start a new conversation? This will clear the current chat.')) {
                return;
            }
        }

        // Clear conversation ID
        conversationId = null;
        localStorage.removeItem('assistant_conversation_id');

        // Clear chat history
        sessionStorage.removeItem('assistant_chat_history');

        // Clear messages from UI
        elements.messagesContainer.innerHTML = '';

        // Show welcome message
        if (elements.welcome) {
            elements.welcome.style.display = 'block';
        }

        // Clear suggestions except New Chat
        if (elements.suggestions) {
            elements.suggestions.innerHTML = '';
            addNewChatButton();
        }

        // Focus input
        elements.input.focus();

        console.log('Assistant: Chat cleared, new conversation ready');
    }

    /**
     * Set loading state
     */
    function setLoading(loading) {
        isLoading = loading;

        if (loading) {
            elements.loading.style.display = 'flex';
            elements.sendBtn.disabled = true;
            scrollToBottom();
        } else {
            elements.loading.style.display = 'none';
            elements.sendBtn.disabled = false;
        }
    }

    /**
     * Scroll messages to bottom
     */
    function scrollToBottom() {
        setTimeout(() => {
            elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
        }, 100);
    }

    /**
     * Convert markdown-style links to HTML links
     */
    function convertMarkdownLinks(text) {
        // Convert ### headings to <strong> (h3 style)
        text = text.replace(/^###\s+(.+)$/gm, '<strong style="font-size: 1.1em; display: block; margin: 8px 0 4px 0;">$1</strong>');
        
        // Convert ## headings to <strong> (h2 style)
        text = text.replace(/^##\s+(.+)$/gm, '<strong style="font-size: 1.2em; display: block; margin: 10px 0 5px 0;">$1</strong>');
        
        // Convert # headings to <strong> (h1 style)
        text = text.replace(/^#\s+(.+)$/gm, '<strong style="font-size: 1.3em; display: block; margin: 12px 0 6px 0;">$1</strong>');
        
        // Convert **bold** to <strong>
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Convert *italic* to <em> (but not ** which was already handled)
        text = text.replace(/(?<!\*)\*(?!\*)([^*]+)\*(?!\*)/g, '<em>$1</em>');
        
        // Convert [Text](URL) to <a href="URL">Text</a>
        // Strip out any yourstore.com or full URLs and keep only the path
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function(match, linkText, url) {
            // Remove any protocol and domain, keep only the path
            let cleanUrl = url.replace(/^https?:\/\/[^\/]+/, '');
            // If the URL doesn't start with /, add it
            if (!cleanUrl.startsWith('/')) {
                cleanUrl = '/' + cleanUrl;
            }
            return '<a href="' + cleanUrl + '" style="color: #ff6b35; text-decoration: underline;">' + linkText + '</a>';
        });
        
        // Convert newlines to <br> (single newline)
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }

    /**
     * Get page context from data attributes
     */
    function getPageContext() {
        const body = document.body;
        
        return {
            page_url: window.location.pathname,
            page_type: body.dataset.pageType || '',
            product_id: body.dataset.productId ? parseInt(body.dataset.productId) : null,
            category: body.dataset.category || '',
            search_query: body.dataset.searchQuery || '',
            cart_item_count: body.dataset.cartItemCount ? parseInt(body.dataset.cartItemCount) : 0,
            cart_total: body.dataset.cartTotal ? parseFloat(body.dataset.cartTotal) : null
        };
    }

    /**
     * Get CSRF token
     */
    function getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        
        return cookieValue;
    }

    /**
     * Save chat history to sessionStorage
     */
    function saveChatHistory() {
        try {
            const messages = [];
            const messageElements = elements.messagesContainer.querySelectorAll('.assistant-message');
            
            messageElements.forEach(el => {
                const role = el.classList.contains('assistant-message-user') ? 'user' : 'assistant';
                const content = el.querySelector('.assistant-message-content p');
                if (content) {
                    messages.push({
                        role: role,
                        text: content.innerHTML
                    });
                }
            });

            sessionStorage.setItem('assistant_chat_history', JSON.stringify(messages));
        } catch (e) {
            console.error('Assistant: Error saving chat history', e);
        }
    }

    /**
     * Restore chat history from sessionStorage
     */
    function restoreChatHistory() {
        try {
            const history = sessionStorage.getItem('assistant_chat_history');
            if (!history) return;

            const messages = JSON.parse(history);
            messages.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.className = `assistant-message assistant-message-${msg.role}`;

                // Avatar
                const avatarDiv = document.createElement('div');
                avatarDiv.className = 'assistant-avatar';
                
                if (msg.role === 'assistant') {
                    avatarDiv.innerHTML = `
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <path d="M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01"></path>
                        </svg>
                    `;
                } else {
                    avatarDiv.innerHTML = `
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                    `;
                }

                // Content
                const contentDiv = document.createElement('div');
                contentDiv.className = 'assistant-message-content';

                const textP = document.createElement('p');
                textP.innerHTML = msg.text;
                contentDiv.appendChild(textP);

                messageDiv.appendChild(avatarDiv);
                messageDiv.appendChild(contentDiv);

                elements.messagesContainer.appendChild(messageDiv);
            });

            scrollToBottom();
        } catch (e) {
            console.error('Assistant: Error restoring chat history', e);
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
