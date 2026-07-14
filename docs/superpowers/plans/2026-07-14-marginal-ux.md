# Marginal UX & Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve Marginal visual presentation, resolve metadata card overflow, configure references scrollbars, integrate branding (logo, favicon), add an "About" modal, and write a repository README.

**Architecture:** Extend existing HTML/CSS modal patterns and responsive layouts. Ensure clean flexbox alignments and text-overflow configurations to isolate structural layout from text length changes.

**Tech Stack:** HTML5, CSS3, Vanilla JavaScript, FastAPI backend.

## Global Constraints
- Do not introduce breaking dependencies.
- Match parchment theme styling aesthetics (charcoal ink, off-white background, brass/burgundy highlights).

---

### Task 1: Update Frontend Files (HTML & styles.css)

**Files:**
- Modify: `c:\Users\wisdo\OneDrive\Documents\GitHub\Marginal\frontend\index.html`
- Modify: `c:\Users\wisdo\OneDrive\Documents\GitHub\Marginal\frontend\styles.css`

- [ ] **Step 1: Edit index.html to add favicon, brand logo, about button, and modal**

Modify `c:\Users\wisdo\OneDrive\Documents\GitHub\Marginal\frontend\index.html` as follows:
- Add favicon tag inside `<head>` (around line 7).
- Replace `<div class="brand-mark">M</div>` with `<img src="logo.png" alt="Marginal Logo" class="brand-logo">` (around line 21).
- Add the `catalog-footer` containing `#aboutBtn` inside the `<aside class="catalog">` element, right after `.papers-list-container` closing `</div>`.
- Add `#aboutModal` right before the scripts at the bottom.

Snippet of changes in `index.html`:
```html
    <!-- Add favicon link in <head> -->
    <link rel="icon" type="image/png" href="favicon.png">
```
```html
                <!-- Replace brand-mark M in brand div -->
                <div class="brand">
                    <img src="logo.png" alt="Marginal Logo" class="brand-logo">
                    <div class="brand-name">Marginal</div>
                </div>
```
```html
                <!-- Add footer in aside after papers-list-container -->
                <div class="catalog-footer" style="margin-top: auto;">
                    <button id="aboutBtn" class="btn btn-secondary" style="width: 100%; justify-content: center; padding: 10px; border-radius: 8px;">
                        <i data-lucide="info" style="width: 14.5px; height: 14.5px; display: inline-block; vertical-align: middle; margin-right: 4px;"></i> About Marginal
                    </button>
                </div>
```
```html
    <!-- Add Modal at bottom before </body> -->
    <!-- Custom About Modal -->
    <div id="aboutModal" class="modal-overlay" style="display: none;">
        <div class="modal-card" style="max-width: 480px;">
            <h3>About Marginal</h3>
            <p><strong>Marginal</strong> is a local, lightweight research paper reader and AI companion designed for scholars and researchers.</p>
            <p>It parses academic PDFs to generate structured breakdowns—highlighting TL;DR summaries, methodology, key contributions, results, limitations, and bibliographies. It also features a conversational companion to ask grounding questions with source citations.</p>
            <p style="font-size: 13px; color: var(--ink-soft); border-top: 1px solid var(--navy-line); padding-top: 14px; margin-top: 14px;">
                Version 1.0.0 • Built with FastAPI, Uvicorn, and Vanilla JavaScript.
            </p>
            <div class="modal-actions" style="margin-top: 20px;">
                <button id="closeAboutBtn" class="btn btn-secondary" style="padding: 10px 16px;">Close</button>
            </div>
        </div>
    </div>
```

- [ ] **Step 2: Add styles to styles.css for logo, filename truncation, and references scrollbar**

Append or update styles in `c:\Users\wisdo\OneDrive\Documents\GitHub\Marginal\frontend\styles.css`:
- Add `.brand-logo` block.
- Add `.catalog-card-meta span:first-child` truncation.
- Update `.references-list` with `max-height: 300px` and `overflow-y: auto`, plus scrolling properties.

Code additions:
```css
/* Logo Styling */
.brand-logo {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  object-fit: cover;
}

/* Metadata Text Truncation */
.catalog-card-meta span:first-child {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-right: 8px;
  min-width: 0;
  flex: 1;
}

/* Reference List Scrollbar */
.references-list {
  margin: 0;
  padding-left: 20px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--ink-soft);
  line-height: 1.6;
  max-height: 300px;
  overflow-y: auto;
  padding-right: 10px;
}
.references-list::-webkit-scrollbar {
  width: 4px;
}
.references-list::-webkit-scrollbar-track {
  background: transparent;
}
.references-list::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.08);
  border-radius: 4px;
}
.references-list::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.15);
}
```

---

### Task 2: Implement Javascript Action Handlers

**Files:**
- Modify: `c:\Users\wisdo\OneDrive\Documents\GitHub\Marginal\frontend\app.js`

- [ ] **Step 1: Bind About button click events**

Add About modal trigger hooks at the end of the `DOMContentLoaded` listener block in `c:\Users\wisdo\OneDrive\Documents\GitHub\Marginal\frontend\app.js`:

```javascript
    // 10. About Modal Interactions
    const aboutBtn = document.getElementById('aboutBtn');
    const aboutModal = document.getElementById('aboutModal');
    const closeAboutBtn = document.getElementById('closeAboutBtn');

    if (aboutBtn && aboutModal && closeAboutBtn) {
        aboutBtn.addEventListener('click', () => {
            aboutModal.style.display = 'flex';
            aboutModal.offsetHeight; // force reflow
            aboutModal.classList.add('show');
        });

        closeAboutBtn.addEventListener('click', () => {
            aboutModal.classList.remove('show');
            setTimeout(() => { aboutModal.style.display = 'none'; }, 200);
        });

        // Close modal when clicking outside card
        aboutModal.addEventListener('click', (e) => {
            if (e.target === aboutModal) {
                aboutModal.classList.remove('show');
                setTimeout(() => { aboutModal.style.display = 'none'; }, 200);
            }
        });
    }
```

---

### Task 3: Create Project README.md

**Files:**
- Create: `c:\Users\wisdo\OneDrive\Documents\GitHub\Marginal\README.md`

- [ ] **Step 1: Write README.md**

Create `c:\Users\wisdo\OneDrive\Documents\GitHub\Marginal\README.md` with:
- System Overview.
- Tech Stack details (Uvicorn, FastAPI, HTML5/CSS3/ES6).
- Installation and Startup Guide.
- Endpoint specs and features breakdown.
