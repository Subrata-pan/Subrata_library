// Chatbot script
document.addEventListener('DOMContentLoaded', function() {
    const chatToggle = document.getElementById('chat-toggle');
    const chatContainer = document.getElementById('chat-container');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');

    // Toggle chat visibility
    function toggleChat() {
        if (chatContainer && chatInput) {
            const isHidden = chatContainer.style.display === 'none' || !chatContainer.style.display;
            if (isHidden) {
                chatContainer.style.display = 'block';
                document.body.classList.add('chat-open');
                if (chatToggle) {
                    chatToggle.setAttribute('aria-expanded', 'true');
                }
                chatInput.focus();
            } else {
                chatContainer.style.display = 'none';
                document.body.classList.remove('chat-open');
                if (chatToggle) {
                    chatToggle.setAttribute('aria-expanded', 'false');
                }
            }
        }
    }

    window.toggleChat = toggleChat;

    // Send message function
    function sendMessage() {
        if (!chatInput) return;
        const message = chatInput.value.trim();
        if (!message) return;

        // Add user message
        addMessage(message, 'user');
        chatInput.value = '';

        // Simulate bot response (replace with actual chatbot logic)
        setTimeout(() => {
            const responses = [
                "Hello! How can I help you with KitabGhar today?",
                "I'm here to assist you with book recommendations and library features.",
                "Feel free to ask me about uploading books, browsing categories, or any other questions!",
                "Thanks for using KitabGhar! What would you like to know?"
            ];
            const randomResponse = responses[Math.floor(Math.random() * responses.length)];
            addMessage(randomResponse, 'bot');
        }, 1000);
    }

    // Add message to chat
    function addMessage(text, sender) {
        if (!chatMessages) return;
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Event listeners
    if (chatToggle) {
        chatToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleChat();
        });
    }

    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }

    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    // Close chat when clicking outside
    document.addEventListener('click', function(e) {
        if (chatContainer && chatToggle && !chatContainer.contains(e.target) && e.target !== chatToggle) {
            chatContainer.style.display = 'none';
            chatToggle.setAttribute('aria-expanded', 'false');
        }
    });
});

// Google Books API Integration
document.addEventListener('DOMContentLoaded', function() {
    const googleSearchInput = document.getElementById('google-books-search');
    const googleSearchBtn = document.getElementById('google-books-search-btn');
    const googleLoading = document.getElementById('google-books-loading');
    const googleError = document.getElementById('google-books-error');
    const googleResults = document.getElementById('google-books-results');
    const googleGrid = document.getElementById('google-books-grid');
    const clearResultsBtn = document.getElementById('clear-google-results');
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    const fallbackCover = '/static/images/recent_add.jpg';

    // Check if required elements exist
    if (!googleSearchInput || !googleSearchBtn || !googleLoading || !googleError || !googleResults || !googleGrid || !clearResultsBtn) {
        return;
    }

    // Search button click handler
    if (googleSearchBtn) {
        googleSearchBtn.addEventListener('click', searchGoogleBooks);
    }

    // Enter key handler for search input
    if (googleSearchInput) {
        googleSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchGoogleBooks();
            }
        });
    }

    // Clear results button handler
    if (clearResultsBtn) {
        clearResultsBtn.addEventListener('click', clearGoogleResults);
    }

    // Favorite buttons handler
    document.addEventListener('click', function(e) {
        if (e.target.closest('.favorite-btn')) {
            e.preventDefault();
            const btn = e.target.closest('.favorite-btn');
            const bookId = btn.dataset.bookId;
            const isGoogleBook = btn.dataset.isGoogleBook === 'true';
            toggleFavorite(bookId, btn, isGoogleBook);
        }
    });

    // Save book buttons handler
    document.addEventListener('click', function(e) {
        if (e.target.closest('.save-book-btn')) {
            e.preventDefault();
            const btn = e.target.closest('.save-book-btn');
            saveGoogleBook(btn);
        }
    });

    // Preview book buttons handler
    document.addEventListener('click', function(e) {
        if (e.target.closest('.preview-book-btn')) {
            e.preventDefault();
            const btn = e.target.closest('.preview-book-btn');
            showBookPreview(btn);
        }
    });

    async function searchGoogleBooks() {
        const query = googleSearchInput.value.trim();
        if (!query) {
            showGoogleError('Please enter a book name to search.');
            return;
        }

        // Show loading, hide error
        googleLoading.classList.remove('d-none');
        googleError.classList.add('d-none');
        googleResults.classList.add('d-none');

        try {
            let data;
            try {
                data = await searchGoogleBooksFromBackend(query);
            } catch (backendError) {
                console.warn('Backend Google Books search failed, trying browser fallback:', backendError);
                try {
                    data = await searchGoogleBooksDirectly(query);
                } catch (googleError) {
                    console.warn('Browser Google Books search failed, trying Open Library fallback:', googleError);
                    data = await searchOpenLibraryDirectly(query);
                }
            }

            if (!data.items || data.items.length === 0) {
                data = await searchOpenLibraryDirectly(query);
            }

            if (data.items && data.items.length > 0) {
                displayGoogleBooks(data.items);
                if (data.source === 'open_library') {
                    showToast(data.message || 'Google Books is unavailable, showing fallback book results.', 'info');
                }
            } else {
                showGoogleError('No books found. Try a different search term.');
            }
        } catch (error) {
            console.error('Error fetching Google Books:', error);
            showGoogleError('An error occurred while searching. Please try again.');
        } finally {
            googleLoading.classList.add('d-none');
        }
    }

    async function searchGoogleBooksFromBackend(query) {
        const response = await fetch(`/api/google-books/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.message || 'Backend Google Books search failed.');
        }
        return data;
    }

    async function searchGoogleBooksDirectly(query) {
        const url = `https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(query)}&maxResults=12&printType=books`;
        const response = await fetch(url);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error?.message || 'Direct Google Books search failed.');
        }
        return {
            items: (data.items || []).map(normalizeGoogleBook)
        };
    }

    async function searchOpenLibraryDirectly(query) {
        const response = await fetch(`https://openlibrary.org/search.json?q=${encodeURIComponent(query)}&limit=12`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error('Fallback book search failed.');
        }
        return {
            source: 'open_library',
            message: 'Google Books is unavailable, showing fallback book results.',
            items: (data.docs || []).map(normalizeOpenLibraryBook)
        };
    }

    function normalizeGoogleBook(item) {
        const volume = item.volumeInfo || {};
        const imageLinks = volume.imageLinks || {};
        const thumbnail = (imageLinks.thumbnail || imageLinks.smallThumbnail || '').replace(/^http:\/\//, 'https://');
        return {
            id: item.id,
            title: volume.title || 'Unknown Title',
            authors: Array.isArray(volume.authors) && volume.authors.length ? volume.authors.join(', ') : 'Unknown Author',
            published_year: (volume.publishedDate || 'Unknown Year').slice(0, 4),
            thumbnail,
            preview_link: volume.previewLink || volume.infoLink || ''
        };
    }

    function normalizeOpenLibraryBook(item) {
        const coverId = item.cover_i;
        return {
            id: item.key || (Array.isArray(item.edition_key) ? item.edition_key[0] : ''),
            title: item.title || 'Unknown Title',
            authors: Array.isArray(item.author_name) && item.author_name.length ? item.author_name.join(', ') : 'Unknown Author',
            published_year: item.first_publish_year ? String(item.first_publish_year) : 'Unknown Year',
            thumbnail: coverId ? `https://covers.openlibrary.org/b/id/${coverId}-M.jpg` : '',
            preview_link: item.key ? `https://openlibrary.org${item.key}` : ''
        };
    }

    function displayGoogleBooks(books) {
        googleGrid.innerHTML = '';

        books.forEach(book => {
            // Create book card
            const bookCard = document.createElement('div');
            bookCard.className = 'col-lg-4 col-md-6';
            const thumbnail = book.thumbnail || fallbackCover;
            const title = book.title || 'Unknown Title';
            const authors = book.authors || 'Unknown Author';
            const publishedYear = book.published_year || 'Unknown Year';
            const previewLink = book.preview_link || '#';

            bookCard.innerHTML = `
                <div class="card h-100 google-book-card">
                    <img src=""
                         alt=""
                         class="google-book-thumbnail"
                         onerror="this.src='${fallbackCover}'">
                    <div class="card-body d-flex flex-column">
                        <h6 class="google-book-title"></h6>
                        <p class="google-book-author"></p>
                        <p class="google-book-year"></p>
                        <div class="d-flex gap-2 mt-auto">
                            <button class="btn btn-outline-info btn-sm save-book-btn"
                                    type="button"
                                    title="Save to My Library">
                                <i class="fas fa-save me-1"></i>Save
                            </button>
                            <button class="btn btn-outline-primary btn-sm preview-book-btn"
                                    type="button"
                                    title="Preview Book">
                                <i class="fas fa-eye me-1"></i>Preview
                            </button>
                            <a href="#"
                               class="btn btn-outline-secondary btn-sm open-book-link"
                               target="_blank"
                               rel="noopener noreferrer"
                               title="Open book page">
                                <i class="fas fa-external-link-alt me-1"></i>Open
                            </a>
                        </div>
                    </div>
                </div>
            `;
            bookCard.querySelector('img').src = thumbnail;
            bookCard.querySelector('img').alt = title;
            bookCard.querySelector('.google-book-title').textContent = title;
            bookCard.querySelector('.google-book-author').textContent = `by ${authors}`;
            bookCard.querySelector('.google-book-year').textContent = `Published: ${publishedYear}`;

            const saveBtn = bookCard.querySelector('.save-book-btn');
            saveBtn.dataset.googleId = book.id || '';
            saveBtn.dataset.title = title;
            saveBtn.dataset.author = authors;
            saveBtn.dataset.thumbnail = thumbnail;
            saveBtn.dataset.preview = previewLink;
            saveBtn.dataset.year = publishedYear;

            const previewBtn = bookCard.querySelector('.preview-book-btn');
            previewBtn.dataset.preview = previewLink;

            const openLink = bookCard.querySelector('.open-book-link');
            openLink.href = previewLink;
            if (!previewLink || previewLink === '#') {
                openLink.classList.add('disabled');
                openLink.setAttribute('aria-disabled', 'true');
                openLink.removeAttribute('target');
            }

            googleGrid.appendChild(bookCard);
        });

        // Show results
        googleResults.classList.remove('d-none');

        // Scroll to results
        googleResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function showGoogleError(message) {
        googleError.textContent = message;
        googleError.classList.remove('d-none');
        googleResults.classList.add('d-none');
    }

    function clearGoogleResults() {
        googleResults.classList.add('d-none');
        googleGrid.innerHTML = '';
        googleSearchInput.value = '';
        googleError.classList.add('d-none');
    }

    // Toggle favorite function
    async function toggleFavorite(bookId, btn, isGoogleBook = false) {
        // For Google Books, show a message that favorites are not supported yet
        if (isGoogleBook) {
            showToast('Google Books favorites coming soon!', 'info');
            return;
        }

        try {
            const response = await fetch(`/toggle_favorite/${bookId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                }
            });

            const data = await response.json();

            if (data.success) {
                const icon = btn.querySelector('.favorite-icon');
                if (data.favorited) {
                    icon.classList.add('fas');
                    icon.classList.remove('far');
                    btn.classList.add('btn-warning');
                    btn.classList.remove('btn-outline-warning');
                } else {
                    icon.classList.add('far');
                    icon.classList.remove('fas');
                    btn.classList.add('btn-outline-warning');
                    btn.classList.remove('btn-warning');
                }

                // Show toast notification
                showToast(data.message, 'success');
            } else {
                if (data.status === 'login_required') {
                    showToast(data.message, 'error');
                } else {
                    showToast(data.message || 'Error updating favorite status', 'error');
                }
            }
        } catch (error) {
            console.error('Error toggling favorite:', error);
            showToast('Error updating favorite status', 'error');
        }
    }

    // Save Google Book function
    async function saveGoogleBook(btn) {
        const bookData = {
            google_books_id: btn.dataset.googleId,
            title: btn.dataset.title,
            author: btn.dataset.author,
            thumbnail_url: btn.dataset.thumbnail,
            preview_link: btn.dataset.preview,
            published_year: btn.dataset.year
        };

        try {
            const response = await fetch('/save_google_book', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify(bookData)
            });

            const data = await response.json();

            if (data.success) {
                showToast(data.message, 'success');
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-check me-1"></i>Saved';
            } else {
                if (data.status === 'login_required') {
                    showToast(data.message, 'error');
                } else {
                    showToast(data.message || 'Error saving book', 'error');
                }
            }
        } catch (error) {
            console.error('Error saving book:', error);
            showToast('Error saving book', 'error');
        }
    }

    // Show book preview function
    function showBookPreview(btn) {
        const previewLink = btn.dataset.preview;
        if (!previewLink || previewLink === '#') {
            showToast('Preview is not available for this book.', 'info');
            return;
        }
        window.open(previewLink, '_blank', 'noopener');
    }

    // Toast notification function
    function showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        // Add to page
        const container = document.querySelector('.toast-container') || createToastContainer();
        container.appendChild(toast);

        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove after hide
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    // Create toast container if it doesn't exist
    function createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }

    // Initialize favorite states on page load
    function initializeFavorites() {
        document.querySelectorAll('.favorite-btn').forEach(async (btn) => {
            const bookId = btn.dataset.bookId;
            try {
                const response = await fetch(`/check_favorite/${bookId}`);
                const data = await response.json();

                const icon = btn.querySelector('.favorite-icon');
                if (data.favorited) {
                    icon.classList.add('fas');
                    icon.classList.remove('far');
                    btn.classList.add('btn-warning');
                    btn.classList.remove('btn-outline-warning');
                } else {
                    icon.classList.add('far');
                    icon.classList.remove('fas');
                    btn.classList.add('btn-outline-warning');
                    btn.classList.remove('btn-warning');
                }
            } catch (error) {
                console.error('Error checking favorite status:', error);
            }
        });
    }

    // Initialize favorites when DOM is loaded
    initializeFavorites();
});

// Add your actual chatbot functionality here
