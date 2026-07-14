# Design Spec: Marginal UX Improvements & Documentation

## Goal
Improve the visual presentation of card items, handle long reference list scrolling, add brand logo/favicon integration, introduce an "About" info modal, and provide a comprehensive project `README.md`.

## Proposed Changes

### 1. CSS & Layout Fixes
- **Filename Truncation**: Prevent long filenames from pushing status badges out of `.catalog-card` elements by applying ellipsis text-overflow to the filename text container.
- **Reference Scrolling**: Constrain the maximum height of the bibliography list (`.references-list`) and allow vertical scrolling with a styled scrollbar so pages do not stretch infinitely.

### 2. Branding (Logo & Favicon)
- Save generated image asset as `logo.png` and `favicon.png`.
- Update HTML header to load `favicon.png`.
- Replace the placeholder text monogram `M` with the logo image, and style it cleanly to preserve the parchment literary aesthetic.

### 3. About Section
- Add an "About Marginal" button at the bottom of the sidebar catalog.
- Implement an overlay modal displaying project details, features, version, and tech stack information.
- Bind show/hide handlers in JS.

### 4. Repository README.md
- Create a complete and professional `README.md` describing project setup, features, structure, and API interaction guidelines.
