/**
 * UI Components Module
 * Reusable UI component functions for buttons, modals, toasts, and spinners
 */

// ============================================
// Button Components
// ============================================

/**
 * Create a button element
 * @param {Object} options - Button configuration
 * @param {string} options.text - Button text
 * @param {string} options.type - Button type: 'primary', 'outline', 'ghost', 'icon'
 * @param {string} options.size - Button size: 'normal', 'large'
 * @param {string} options.icon - Font Awesome icon class (optional)
 * @param {Function} options.onClick - Click handler
 * @param {boolean} options.disabled - Disabled state
 * @param {string} options.id - Button ID (optional)
 * @param {string} options.className - Additional CSS classes (optional)
 * @returns {HTMLButtonElement} Button element
 */
function createButton(options) {
  const {
    text = '',
    type = 'primary',
    size = 'normal',
    icon = null,
    onClick = null,
    disabled = false,
    id = null,
    className = ''
  } = options;

  const button = document.createElement('button');
  
  // Add base classes
  const classes = [`btn-${type}`];
  if (size === 'large') classes.push('btn-large');
  if (className) classes.push(className);
  button.className = classes.join(' ');
  
  // Set ID if provided
  if (id) button.id = id;
  
  // Add icon if provided
  if (icon) {
    const iconElement = document.createElement('i');
    iconElement.className = icon;
    button.appendChild(iconElement);
  }
  
  // Add text if provided (not for icon-only buttons)
  if (text) {
    const textNode = document.createTextNode(text);
    button.appendChild(textNode);
  }
  
  // Set disabled state
  button.disabled = disabled;
  
  // Add click handler
  if (onClick) {
    button.addEventListener('click', onClick);
  }
  
  return button;
}

// ============================================
// Modal Component
// ============================================

/**
 * Create and show a modal
 * @param {Object} options - Modal configuration
 * @param {string} options.title - Modal title
 * @param {string} options.subtitle - Modal subtitle (optional)
 * @param {string|HTMLElement} options.content - Modal body content
 * @param {Array} options.actions - Array of action button configs
 * @param {boolean} options.large - Use large modal size
 * @param {boolean} options.closeButton - Show close button (default: true)
 * @param {Function} options.onClose - Callback when modal closes
 * @param {string} options.id - Modal ID (optional)
 * @returns {HTMLElement} Modal element
 */
function createModal(options) {
  const {
    title = '',
    subtitle = '',
    content = '',
    actions = [],
    large = false,
    closeButton = true,
    onClose = null,
    id = null
  } = options;

  // Create modal container
  const modal = document.createElement('div');
  modal.className = 'modal';
  if (id) modal.id = id;

  // Create modal content
  const modalContent = document.createElement('div');
  modalContent.className = large ? 'modal-content large' : 'modal-content';

  // Create header
  const header = document.createElement('div');
  header.className = 'modal-header';
  
  const titleElement = document.createElement('h3');
  titleElement.textContent = title;
  header.appendChild(titleElement);
  
  if (subtitle) {
    const subtitleElement = document.createElement('p');
    subtitleElement.textContent = subtitle;
    header.appendChild(subtitleElement);
  }
  
  modalContent.appendChild(header);

  // Add close button if enabled
  if (closeButton) {
    const closeBtn = document.createElement('button');
    closeBtn.className = 'modal-close';
    closeBtn.innerHTML = '<i class="fas fa-times"></i>';
    closeBtn.setAttribute('aria-label', 'Close modal');
    closeBtn.addEventListener('click', () => closeModal(modal, onClose));
    modalContent.appendChild(closeBtn);
  }

  // Create body
  const body = document.createElement('div');
  body.className = 'modal-body';
  
  if (typeof content === 'string') {
    body.innerHTML = content;
  } else if (content instanceof HTMLElement) {
    body.appendChild(content);
  }
  
  modalContent.appendChild(body);

  // Create actions footer if actions provided
  if (actions.length > 0) {
    const footer = document.createElement('div');
    footer.className = 'modal-actions';
    
    actions.forEach(actionConfig => {
      const actionButton = createButton(actionConfig);
      footer.appendChild(actionButton);
    });
    
    modalContent.appendChild(footer);
  }

  modal.appendChild(modalContent);
  document.body.appendChild(modal);

  // Add keyboard support (Esc to close)
  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      closeModal(modal, onClose);
      document.removeEventListener('keydown', handleKeyDown);
    }
  };
  document.addEventListener('keydown', handleKeyDown);

  // Close on overlay click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeModal(modal, onClose);
    }
  });

  return modal;
}

/**
 * Show a modal
 * @param {HTMLElement} modal - Modal element
 */
function showModal(modal) {
  modal.classList.add('active');
  // Focus trap for accessibility
  const focusableElements = modal.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  if (focusableElements.length > 0) {
    focusableElements[0].focus();
  }
}

/**
 * Close a modal
 * @param {HTMLElement} modal - Modal element
 * @param {Function} onClose - Callback function
 */
function closeModal(modal, onClose = null) {
  modal.classList.remove('active');
  setTimeout(() => {
    modal.remove();
    if (onClose) onClose();
  }, 200); // Wait for animation
}

// ============================================
// Toast Notification System
// ============================================

/**
 * Show a toast notification
 * @param {string} message - Toast message
 * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showToast(message, type = 'info', duration = 3000) {
  // Ensure toast container exists
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  // Create toast element
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  // Add icon based on type
  const iconMap = {
    success: 'fas fa-check-circle',
    error: 'fas fa-exclamation-circle',
    warning: 'fas fa-exclamation-triangle',
    info: 'fas fa-info-circle'
  };
  
  const icon = document.createElement('i');
  icon.className = iconMap[type] || iconMap.info;
  toast.appendChild(icon);
  
  // Add message
  const messageSpan = document.createElement('span');
  messageSpan.textContent = message;
  toast.appendChild(messageSpan);
  
  // Add to container
  container.appendChild(toast);
  
  // Trigger animation
  setTimeout(() => toast.classList.add('show'), 10);
  
  // Auto remove after duration
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 200);
  }, duration);
}

// ============================================
// Loading Spinner Component
// ============================================

/**
 * Create a loading spinner
 * @param {Object} options - Spinner configuration
 * @param {string} options.size - Spinner size: 'small', 'normal', 'large'
 * @param {string} options.text - Loading text (optional)
 * @returns {HTMLElement} Spinner container element
 */
function createSpinner(options = {}) {
  const { size = 'normal', text = '' } = options;
  
  const container = document.createElement('div');
  container.className = 'loading-container';
  
  const spinner = document.createElement('div');
  spinner.className = 'spinner';
  if (size === 'small') spinner.classList.add('spinner-small');
  if (size === 'large') spinner.classList.add('spinner-large');
  
  container.appendChild(spinner);
  
  if (text) {
    const textElement = document.createElement('div');
    textElement.className = 'loading-text';
    textElement.textContent = text;
    container.appendChild(textElement);
  }
  
  return container;
}

/**
 * Show loading spinner in an element
 * @param {HTMLElement} element - Target element
 * @param {string} text - Loading text (optional)
 */
function showLoading(element, text = 'Loading...') {
  const spinner = createSpinner({ text });
  element.innerHTML = '';
  element.appendChild(spinner);
}

/**
 * Set button loading state
 * @param {string|HTMLElement} button - Button element or ID
 * @param {boolean} loading - Loading state
 * @param {string} loadingText - Text to show while loading (optional)
 */
function setButtonLoading(button, loading, loadingText = '') {
  const btn = typeof button === 'string' ? document.getElementById(button) : button;
  if (!btn) return;
  
  if (loading) {
    btn.disabled = true;
    btn.dataset.originalText = btn.textContent;
    btn.innerHTML = '';
    
    const spinner = document.createElement('div');
    spinner.className = 'spinner spinner-small';
    spinner.style.display = 'inline-block';
    btn.appendChild(spinner);
    
    if (loadingText) {
      const text = document.createTextNode(' ' + loadingText);
      btn.appendChild(text);
    }
  } else {
    btn.disabled = false;
    btn.textContent = btn.dataset.originalText || '';
    delete btn.dataset.originalText;
  }
}

// ============================================
// Utility Functions
// ============================================

/**
 * Create a confirmation modal
 * @param {Object} options - Confirmation options
 * @param {string} options.title - Modal title
 * @param {string} options.message - Confirmation message
 * @param {string} options.confirmText - Confirm button text (default: 'Confirm')
 * @param {string} options.cancelText - Cancel button text (default: 'Cancel')
 * @param {Function} options.onConfirm - Callback on confirm
 * @param {Function} options.onCancel - Callback on cancel
 */
function showConfirmation(options) {
  const {
    title = 'Confirm',
    message = 'Are you sure?',
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    onConfirm = null,
    onCancel = null
  } = options;

  const modal = createModal({
    title,
    content: `<p>${message}</p>`,
    actions: [
      {
        text: cancelText,
        type: 'ghost',
        onClick: () => {
          closeModal(modal);
          if (onCancel) onCancel();
        }
      },
      {
        text: confirmText,
        type: 'primary',
        onClick: () => {
          closeModal(modal);
          if (onConfirm) onConfirm();
        }
      }
    ]
  });

  showModal(modal);
}

/**
 * Create an error modal
 * @param {string} message - Error message
 * @param {Array<string>} suggestions - Array of suggestion strings
 */
function showErrorModal(message, suggestions = []) {
  let content = `<p class="error-message" style="color: var(--color-error); margin-bottom: var(--spacing-md);">${message}</p>`;
  
  if (suggestions.length > 0) {
    content += '<div class="error-suggestions">';
    content += '<h4 style="margin-bottom: var(--spacing-sm);">Suggestions:</h4>';
    content += '<ul style="list-style: disc; padding-left: var(--spacing-lg);">';
    suggestions.forEach(suggestion => {
      content += `<li style="margin-bottom: var(--spacing-xs);">${suggestion}</li>`;
    });
    content += '</ul></div>';
  }

  const modal = createModal({
    title: 'Error',
    content,
    actions: [
      {
        text: 'OK',
        type: 'primary',
        onClick: () => closeModal(modal)
      }
    ]
  });

  showModal(modal);
}
