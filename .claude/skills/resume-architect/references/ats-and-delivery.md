# ATS, readability and artifact QA

1. Use a single text column, conventional headings (Summary, Technical Skills, Professional Experience, Education), and reverse-chronological employment.
2. Keep name/contact as real selectable text. Avoid emojis, floating boxes, text-only images, headers/footers that conceal important contact info, and complicated tables.
3. Distinguish DOCX package integrity from ATS compatibility: ZIP-valid DOCX can still have problematic reading order. A PDF can extract successfully and still have ambiguous columns.
4. Check all dates, contact spelling, URLs, bullets, en/em dashes, ligatures, nonbreaking spaces, control characters, HTML entities (e.g. `&#x20;`), and page numbers.
5. Prefer professionally balanced two-page layout for 10+ year engineering candidates, but retain meaningful details rather than shrinking to tiny fonts.
6. For each generated DOCX: unzip/parse XML; inspect paragraphs, fields and tables. Run `scripts/docx_audit.py` when possible.
7. For each PDF: render all pages and inspect at 100%; extract text in natural order and compare header, roles, dates, metrics, education; verify no clipped lines or orphan employer headings. If a renderer is unavailable, say visual QA was not performed.
8. Before sharing a file, verify that it actually exists and can be reopened. Do not claim "verified" on visual inspection unless done.
9. Deliver two outputs if requested: DOCX editable and PDF submission copy. If DOCX→PDF conversion is missing, give DOCX and explain the limitation rather than inventing a PDF.
10. No universal ATS score exists. Any "score" must be labeled as an editorial heuristic and should be paired with a specific JD to discuss keyword fit.
11. Keep candidate personal details off GitHub and published examples. The final brief may list unresolved candidate questions; remove internal evidence IDs from the public resume.
12. An audit-only request produces findings and stops; never overwrite a user's original file.

## Delivery checklist
- [ ] Evidence gate passed on the claims used.
- [ ] Unverified facts are omitted or explicitly labeled in a Working draft.
- [ ] Timeline overlap addressed; career years calculated without double-counting concurrent work.
- [ ] Numeric achievements have usable measurement support.
- [ ] Top skills match the real implementation history.
- [ ] Page 1 establishes senior positioning and latest role.
- [ ] Contact and employment dates survive text extraction.
- [ ] Every output file has been opened or otherwise verified.
- [ ] User sees a readiness label and remaining validation tasks.
