# EventFlow visual assets

Added for the interface redesign on 2026-10-26. Files are hosted locally by Vite;
rendering does not require Google Fonts or Unsplash requests from the visitor.

## Font

Onest variable font, weights 100–900:
- Source: https://github.com/google/fonts/tree/main/ofl/onest
- File: frontend/public/assets/fonts/onest-variable.ttf
- Included licence: frontend/public/assets/fonts/OFL-Onest.txt (verbatim source OFL).

## Illustrative photographs

- community.jpg: https://images.unsplash.com/photo-1515187029135-18ee286d815b
- workshop.jpg: https://images.unsplash.com/photo-1517048676732-d65bc937f952

Provider: Unsplash. Both sources were downloaded and visually inspected. Their
source URLs and illustrative purpose are embedded in JPEG comments in the image files.
These are generic community/workshop illustrations, not documentary photos of the
seed events. Demo covers visibly say «Иллюстрация встречи». User-created events
use a typographic fallback instead of being assigned a misleading stock photograph.

Icons are small original inline SVG paths with consistent stroke weight. They
represent controls and statuses; they are not photo substitutes or external widgets.
The date block, event titles, capacity and ticket codes are live semantic HTML.
