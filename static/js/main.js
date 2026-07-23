// ResumeIQ - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {

    // ===== TOOLTIPS =====
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(el) { return new bootstrap.Tooltip(el); });

    // ===== AUTO-DISMISS ALERTS =====
    setTimeout(function() {
        document.querySelectorAll('.alert-dismissible').forEach(function(alert) {
            new bootstrap.Alert(alert).close();
        });
    }, 5000);

    // ===== SCROLL FADE-IN OBSERVER =====
    var fadeEls = document.querySelectorAll('.fade-up');
    if (fadeEls.length > 0) {
        var fadeObserver = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
        fadeEls.forEach(function(el) { fadeObserver.observe(el); });
    }

    // ===== ANIMATED COUNTERS =====
    var counters = document.querySelectorAll('.stat-number[data-count]');
    if (counters.length > 0) {
        var counterObserver = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    var el = entry.target;
                    var target = parseInt(el.dataset.count);
                    var suffix = el.dataset.suffix || '+';
                    var current = 0;
                    var increment = target / 50;
                    var timer = setInterval(function() {
                        current += increment;
                        if (current >= target) {
                            current = target;
                            clearInterval(timer);
                        }
                        el.textContent = Math.floor(current).toLocaleString() + suffix;
                    }, 30);
                    counterObserver.unobserve(el);
                }
            });
        }, { threshold: 0.5 });
        counters.forEach(function(el) { counterObserver.observe(el); });
    }

    // ===== SCORE BAR ANIMATION =====
    var scoreBars = document.querySelectorAll('.score-bar-fill');
    if (scoreBars.length > 0) {
        var barObserver = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    var width = entry.target.getAttribute('data-width');
                    if (width) entry.target.style.width = width + '%';
                    barObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.3 });
        scoreBars.forEach(function(bar) {
            bar.style.width = '0%';
            barObserver.observe(bar);
        });
    }

    // ===== UPLOAD DRAG & DROP =====
    var uploadArea = document.querySelector('.upload-area');
    if (uploadArea) {
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('dragover');
        });
        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
        });
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
            var files = e.dataTransfer.files;
            if (files.length > 0) {
                var fileInput = document.querySelector('#id_file');
                if (fileInput) {
                    fileInput.files = files;
                    fileInput.dispatchEvent(new Event('change'));
                }
            }
        });
        uploadArea.addEventListener('click', function() {
            var fileInput = document.querySelector('#id_file');
            if (fileInput) fileInput.click();
        });
    }

    var fileInput = document.querySelector('#id_file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            var fileName = this.files[0] ? this.files[0].name : 'No file selected';
            var display = document.querySelector('.file-name');
            if (display) display.textContent = fileName;
        });
    }

    // ===== AI BUTTON SPINNER =====
    document.querySelectorAll('.btn-ai-action').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            var form = this.closest('form');
            if (form && !form.checkValidity()) return;
            this.disabled = true;
            this._originalHTML = this._originalHTML || this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>AI is working...';
            var self = this;
            setTimeout(function() {
                self.disabled = false;
                self.innerHTML = self._originalHTML;
            }, 60000);
        });
    });

    // ===== SMOOTH SCROLL FOR ANCHORS =====
    document.querySelectorAll('a[href^="#"]').forEach(function(a) {
        a.addEventListener('click', function(e) {
            var target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // ===== NAVBAR SCROLL SHADOW =====
    var navbar = document.querySelector('.navbar-main');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 20) {
                navbar.style.boxShadow = '0 4px 20px rgba(0,0,0,0.3)';
            } else {
                navbar.style.boxShadow = 'none';
            }
        });
    }
});

// ===== SKILL TAG INPUT HELPER =====
function addSkillTag(input, container) {
    var value = input.value.trim();
    if (value) {
        var tag = document.createElement('span');
        tag.className = 'skill-tag current';
        tag.innerHTML = value + ' <i class="fas fa-times ms-1" onclick="this.parentElement.remove()" style="cursor:pointer;"></i>';
        container.appendChild(tag);
        input.value = '';
    }
}

// ===== COPY TO CLIPBOARD =====
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Copied to clipboard!');
    });
}

function showToast(message) {
    var toast = document.createElement('div');
    toast.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;background:#1e293b;color:#fff;padding:14px 24px;border-radius:12px;font-size:0.9rem;font-weight:600;box-shadow:0 8px 30px rgba(0,0,0,0.2);animation:fadeInDown 0.3s ease;';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(function() {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(function() { toast.remove(); }, 300);
    }, 2500);
}
