# UI Components Guide

This document describes the reusable UI components available in the EvalGenius AI OMR Evaluation System.

## Overview

The UI component system provides a set of reusable, accessible components that follow the design system defined in `style.css`. All components are implemented in `js/utils/ui-components.js`.

## Components

### 1. Button Components

Reusable button components with different styles and sizes.

#### Button Types

- **Primary**: Main action buttons (blue background)
- **Outline**: Secondary actions (transparent with border)
- **Ghost**: Tertiary actions (transparent, minimal styling)
- **Icon**: Icon-only buttons (circular, minimal)

#### Usage

```javascript
const button = createButton({
  text: 'Click Me',
  type: 'primary',        // 'primary', 'outline', 'ghost', 'icon'
  size: 'normal',         // 'normal', 'large'
  icon: 'fas fa-check',   // Font Awesome icon class (optional)
  onClick: () => {
    console.log('Button clicked!');
  },
  disabled: false,
  id: 'my-button',        // Optional ID
  className: 'custom-class' // Optional additional classes
});

document.body.appendChild(button);
```

#### CSS Classes

- `.btn-primary` - Primary button style
- `.btn-outline` - Outline button style
- `.btn-ghost` - Ghost button style
- `.btn-icon` - Icon button style
- `.btn-large` - Large button size
- `.btn-full` - Full width button

### 2. Modal Component

Modal dialogs with overlay, close button, and keyboard support (Esc to close).

#### Features

- Overlay with blur effect
- Close button (X)
- Keyboard support (Esc to close)
- Click outside to close
- Customizable actions
- Large size option
- Smooth animations

#### Usage

```javascript
const modal = createModal({
  title: 'Modal Title',
  subtitle: 'Optional subtitle',
  content: '<p>Modal content goes here</p>',
  large: false,           // Use large modal size
  closeButton: true,      // Show close button (X)
  actions: [
    {
      text: 'Cancel',
      type: 'ghost',
      onClick: () => closeModal(modal)
    },
    {
      text: 'Confirm',
      type: 'primary',
      onClick: () => {
        // Handle confirmation
        closeModal(modal);
      }
    }
  ],
  onClose: () => {
    console.log('Modal closed');
  },
  id: 'my-modal'
});

showModal(modal);
```

#### Helper Functions

**Confirmation Modal**
```javascript
showConfirmation({
  title: 'Confirm Action',
  message: 'Are you sure?',
  confirmText: 'Yes',
  cancelText: 'No',
  onConfirm: () => console.log('Confirmed'),
  onCancel: () => console.log('Cancelled')
});
```

**Error Modal**
```javascript
showErrorModal(
  'An error occurred',
  [
    'Suggestion 1',
    'Suggestion 2',
    'Suggestion 3'
  ]
);
```

#### CSS Classes

- `.modal` - Modal container
- `.modal.active` - Active/visible modal
- `.modal-content` - Modal content box
- `.modal-content.large` - Large modal
- `.modal-header` - Modal header section
- `.modal-body` - Modal body section
- `.modal-actions` - Modal footer with action buttons
- `.modal-close` - Close button (X)

### 3. Toast Notification System

Non-intrusive notifications that appear in the top-right corner.

#### Toast Types

- **Success**: Green, with checkmark icon
- **Error**: Red, with exclamation icon
- **Warning**: Orange, with warning icon
- **Info**: Blue, with info icon

#### Usage

```javascript
showToast('Operation successful!', 'success', 3000);
showToast('An error occurred', 'error', 5000);
showToast('Please review your input', 'warning');
showToast('This is informational', 'info');
```

#### Parameters

- `message` (string): The message to display
- `type` (string): Toast type - 'success', 'error', 'warning', 'info'
- `duration` (number): Duration in milliseconds (default: 3000)

#### CSS Classes

- `#toast-container` - Container for all toasts
- `.toast` - Individual toast element
- `.toast.show` - Visible toast (animated)
- `.toast-success` - Success toast styling
- `.toast-error` - Error toast styling
- `.toast-warning` - Warning toast styling
- `.toast-info` - Info toast styling

### 4. Loading Spinner Component

Animated loading spinners for indicating loading states.

#### Spinner Sizes

- **Small**: 20px diameter
- **Normal**: 40px diameter (default)
- **Large**: 60px diameter

#### Usage

**Create Standalone Spinner**
```javascript
const spinner = createSpinner({
  size: 'normal',        // 'small', 'normal', 'large'
  text: 'Loading...'     // Optional loading text
});

document.getElementById('container').appendChild(spinner);
```

**Show Loading in Element**
```javascript
const element = document.getElementById('content');
showLoading(element, 'Loading data...');
```

**Button Loading State**
```javascript
const button = document.getElementById('submit-btn');

// Set loading
setButtonLoading(button, true, 'Processing...');

// Restore normal state
setTimeout(() => {
  setButtonLoading(button, false);
}, 2000);
```

#### CSS Classes

- `.spinner` - Spinner element
- `.spinner-small` - Small spinner
- `.spinner-large` - Large spinner
- `.loading-container` - Container with spinner and text
- `.loading-text` - Loading text below spinner

## Accessibility Features

All components follow accessibility best practices:

### Buttons
- Minimum touch target size: 44x44px
- Clear focus indicators
- Disabled state properly indicated
- ARIA labels where appropriate

### Modals
- Focus trap (focus stays within modal)
- Keyboard navigation (Tab, Esc)
- ARIA roles and labels
- Focus management (auto-focus first element)

### Toasts
- Non-intrusive positioning
- Auto-dismiss after timeout
- Color-coded with icons for clarity
- Sufficient contrast ratios

### Spinners
- Animated rotation for visual feedback
- Loading text for screen readers
- Proper color contrast

## Design Tokens

All components use CSS custom properties defined in `style.css`:

### Colors
- `--color-primary`: Primary blue (#3b82f6)
- `--color-success`: Green (#10b981)
- `--color-error`: Red (#ef4444)
- `--color-warning`: Orange (#f59e0b)
- `--color-info`: Blue (#3b82f6)

### Spacing
- `--spacing-xs`: 4px
- `--spacing-sm`: 8px
- `--spacing-md`: 16px
- `--spacing-lg`: 24px
- `--spacing-xl`: 32px

### Transitions
- `--transition-fast`: 150ms
- `--transition-base`: 200ms
- `--transition-slow`: 300ms

### Z-index Layers
- `--z-base`: 1
- `--z-dropdown`: 100
- `--z-modal`: 1000
- `--z-toast`: 2000

## Testing

A comprehensive test suite is available at `tests/test_ui_components.html`. Open this file in a browser to:

- Test all button types and sizes
- Test toast notifications
- Test modal variations
- Test loading spinners
- View interactive examples

## Examples

### Complete Modal Example

```javascript
// Create a modal with form content
const formContent = document.createElement('div');
formContent.innerHTML = `
  <div style="margin-bottom: 1rem;">
    <label>Name:</label>
    <input type="text" id="name-input" style="width: 100%; padding: 0.5rem;">
  </div>
  <div>
    <label>Email:</label>
    <input type="email" id="email-input" style="width: 100%; padding: 0.5rem;">
  </div>
`;

const modal = createModal({
  title: 'User Information',
  subtitle: 'Please enter your details',
  content: formContent,
  actions: [
    {
      text: 'Cancel',
      type: 'ghost',
      onClick: () => closeModal(modal)
    },
    {
      text: 'Submit',
      type: 'primary',
      onClick: () => {
        const name = document.getElementById('name-input').value;
        const email = document.getElementById('email-input').value;
        
        if (name && email) {
          showToast('Form submitted successfully!', 'success');
          closeModal(modal);
        } else {
          showToast('Please fill all fields', 'error');
        }
      }
    }
  ]
});

showModal(modal);
```

### Button with Loading State

```javascript
const submitButton = createButton({
  text: 'Submit Form',
  type: 'primary',
  size: 'large',
  icon: 'fas fa-paper-plane',
  onClick: async () => {
    setButtonLoading(submitButton, true, 'Submitting...');
    
    try {
      await submitForm();
      showToast('Form submitted successfully!', 'success');
    } catch (error) {
      showToast('Submission failed', 'error');
    } finally {
      setButtonLoading(submitButton, false);
    }
  }
});
```

## Browser Support

All components are tested and supported on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Future Enhancements

Planned improvements:
- Dropdown component
- Tooltip component
- Progress bar component
- Badge component
- Card component
- Alert/banner component
