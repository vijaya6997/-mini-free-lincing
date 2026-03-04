/* ─── Flash Messages ─── */
document.addEventListener('DOMContentLoaded', () => {

  // Auto-dismiss flashes
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach((flash, i) => {
    setTimeout(() => dismissFlash(flash), 5000 + i * 500);
  });

  // Close button
  document.querySelectorAll('.flash-close').forEach(btn => {
    btn.addEventListener('click', () => dismissFlash(btn.closest('.flash')));
  });

  function dismissFlash(el) {
    if (!el) return;
    el.style.animation = 'slideOut 0.35s ease forwards';
    setTimeout(() => el.remove(), 350);
  }

  // ─── Mobile Nav ───
  const hamburger = document.getElementById('hamburger');
  const navLinks = document.getElementById('navLinks');
  const navActions = document.getElementById('navActions');

  if (hamburger) {
    hamburger.addEventListener('click', () => {
      const open = navLinks?.classList.toggle('open');
      navActions?.classList.toggle('open');
      hamburger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // ─── Star Rating Picker ───
  const starInputs = document.querySelectorAll('.stars-interactive input[type="radio"]');
  starInputs.forEach(input => {
    input.addEventListener('change', () => {
      const hiddenInput = document.getElementById('ratingValue');
      if (hiddenInput) hiddenInput.value = input.value;
    });
  });

  // ─── Character Counter ───
  document.querySelectorAll('[data-maxlength]').forEach(el => {
    const max = parseInt(el.dataset.maxlength);
    const counter = document.createElement('div');
    counter.className = 'form-hint char-counter';
    counter.textContent = `0 / ${max}`;
    el.parentNode.insertBefore(counter, el.nextSibling);
    el.addEventListener('input', () => {
      const len = el.value.length;
      counter.textContent = `${len} / ${max}`;
      counter.style.color = len > max * 0.9 ? 'var(--warning)' : 'var(--text-muted)';
      if (len > max) counter.style.color = 'var(--danger)';
    });
  });

  // ─── Job Search Live Filter (optional enhancement) ───
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        searchInput.closest('form')?.submit();
      }
    });
  }

  // ─── Auto-resize textarea ───
  document.querySelectorAll('textarea.auto-resize').forEach(ta => {
    ta.style.height = 'auto';
    ta.addEventListener('input', () => {
      ta.style.height = 'auto';
      ta.style.height = ta.scrollHeight + 'px';
    });
  });

  // ─── Scroll to bottom of chat ───
  const chatWindow = document.querySelector('.chat-window');
  if (chatWindow) {
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  // ─── Confirm dialogs ───
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', (e) => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // ─── Budget display formatter ───
  const budgetInput = document.getElementById('budgetInput');
  if (budgetInput) {
    budgetInput.addEventListener('input', () => {
      const preview = document.getElementById('budgetPreview');
      if (preview) {
        const val = parseFloat(budgetInput.value);
        preview.textContent = isNaN(val) ? '' : `₹${val.toLocaleString('en-IN')}`;
      }
    });
  }

  // ─── Animate elements on scroll ───
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(el => {
      if (el.isIntersecting) {
        el.target.classList.add('loaded');
        observer.unobserve(el.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.animate-in').forEach(el => observer.observe(el));

  // ─── Profile picture preview ───
  const fileInput = document.getElementById('profilePicInput');
  const filePreview = document.getElementById('profilePicPreview');
  if (fileInput && filePreview) {
    fileInput.addEventListener('change', () => {
      const file = fileInput.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          filePreview.src = e.target.result;
          filePreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // ─── Smooth navbar active highlight ───
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });
});
