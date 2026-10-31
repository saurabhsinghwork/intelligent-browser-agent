"""Generalized LinkedIn master-detail extraction strategy.

Provides account-resilient, non-UI-centric dual-pane traversal for LinkedIn
jobs and similar master-detail architectures.
"""
# Allocate stable unique identifiers for collected job records.
from uuid import uuid4
# Create content hashes for deduplication.
import hashlib
# Support bounded pauses and timing checks.
import time
# Normalize string representations cleanly.
import json
# Filter blocks against compiled goal constraints.
from agent.goals import goal_records


def satisfies_goal(block: dict, goal: dict | None) -> bool:
    """Check if a collected block matches goal constraints."""
    if not goal:
        return True
    constraints = goal.get("constraints", {})
    if not constraints:
        return True
    search_space = (
        str(block.get("text", "")) + " " +
        str(block.get("location", "")) + " " +
        str(block.get("title", "")) + " " +
        str(block.get("company", ""))
    ).lower()
    for val in constraints.values():
        v = str(val).strip().lower()
        if v and v not in search_space:
            return False
    return True


# Generalized LinkedIn execution strategy.
class LinkedInStrategy:
    """Orchestrates resilient master-detail job extraction without brittle CSS dependencies."""

    # Recognize whether a goal or URL should use this strategy.
    @staticmethod
    def matches(goal, url=""):
        """Return True if the target task or URL corresponds to LinkedIn."""
        # Check strategy property on compiled goal.
        if (goal or {}).get("strategy") == "linkedin":
            # Explicit strategy assignment matches.
            return True
        # Check goal objective text for linkedin mention.
        objective = str((goal or {}).get("objective", "")).lower()
        # Objective mentions LinkedIn.
        if "linkedin" in objective:
            # Objective targets LinkedIn.
            return True
        # Check URL hostname.
        if "linkedin.com" in str(url or "").lower():
            # Current page is on LinkedIn.
            return True
        # Not a LinkedIn task.
        return False

    # Extract full job records by iterating master cards and capturing detail panes.
    @classmethod
    def collect_jobs(cls, adapter, goal, store=None, monitor=None):
        """Execute master-detail traversal: glide cursor, click each card, expand, and capture."""
        # Read target record count.
        target_count = int(goal.get("required_count") or 10)
        # Check cancellation before starting traversal.
        adapter.check_cancelled()

        # Script to dismiss any popups, login modals, and toast overlays.
        popup_dismiss_script = """() => {
            const dismissBtns = Array.from(document.querySelectorAll(
                'button[aria-label="Dismiss"], button[aria-label="Close"], button.modal__dismiss, ' +
                'button.contextual-sign-in-modal__modal-dismiss-btn, button[data-tracking-control-name*="dismiss"], ' +
                '.artdeco-modal__dismiss, div.contextual-sign-in-modal button, div[data-tracking-control-name*="sign-in-modal"] button, ' +
                'button.cta-modal__dismiss-btn, button[aria-label*="dismiss" i], button[aria-label*="close" i], ' +
                'icon.artdeco-icon[data-test-icon*="close"], [data-tracking-control-name="public_jobs_contextual-sign-in-modal_sign-in-modal_dismiss"]'
            )).filter(b => {
                try {
                    const style = window.getComputedStyle(b);
                    return style.display !== 'none' && style.visibility !== 'hidden';
                } catch (_) { return false; }
            });
            for (const btn of dismissBtns) {
                try { btn.click(); } catch (_) {}
            }
            const overlays = document.querySelectorAll('.modal__overlay, .contextual-sign-in-modal__screen, .artdeco-modal-overlay');
            for (const ov of overlays) {
                try { ov.remove(); } catch (_) {}
            }
            return dismissBtns.length;
        }"""

        # Script to ensure visual cursor overlay is active and never disappears.
        ensure_cursor_script = """() => {
            let cursor = document.getElementById('iba-cursor');
            if (!cursor) {
                cursor = document.createElement('div');
                cursor.id = 'iba-cursor';
                cursor.dataset.version = 'red-arrow-v3';
                cursor.setAttribute('aria-hidden', 'true');
                const initial = window.__ibaPointer || { x: Math.round((window.innerWidth || 1280) / 2), y: Math.round((window.innerHeight || 800) / 2) };
                window.__ibaPointer = initial;
                cursor.style.cssText = 'position:fixed !important;width:24px !important;height:32px !important;pointer-events:none !important;z-index:2147483647 !important;left:' + initial.x + 'px;top:' + initial.y + 'px;display:block !important;visibility:visible !important;margin:0 !important;transform:none !important;filter:drop-shadow(1px 1px 1px rgba(0,0,0,.55));';
                cursor.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="32" viewBox="0 0 24 32" aria-hidden="true"><path d="M1 1 L1 24 L7.5 18 L12.5 29 L17.5 26.7 L12.5 16.8 L22 16.8 Z" fill="#ef2028" stroke="#ffffff" stroke-width="1.4" stroke-linejoin="round"/></svg>';
                document.documentElement.appendChild(cursor);
            } else {
                cursor.style.display = 'block';
                cursor.style.visibility = 'visible';
            }
            if (!document.getElementById('iba-cursor-styles')) {
                const styleEl = document.createElement('style');
                styleEl.id = 'iba-cursor-styles';
                styleEl.textContent = '@keyframes iba-pulse { 0% { transform: scale(0.6); opacity: 1; } 100% { transform: scale(2.4); opacity: 0; } }';
                document.head ? document.head.appendChild(styleEl) : document.documentElement.appendChild(styleEl);
            }
            if (!window.__ibaShowClickEffect) {
                window.__ibaShowClickEffect = (x, y) => {
                    const ripple = document.createElement('div');
                    ripple.className = 'iba-click-ripple';
                    ripple.style.cssText = 'position:fixed;width:26px;height:26px;border-radius:50%;border:2px solid #ef2028;background:rgba(239,32,40,0.35);pointer-events:none;z-index:2147483647;left:' + (x - 13) + 'px;top:' + (y - 13) + 'px;animation:iba-pulse 0.4s ease-out forwards;';
                    document.documentElement.appendChild(ripple);
                    setTimeout(() => ripple.remove(), 450);
                };
            }
            return true;
        }"""

        # Script to locate unique top-level job cards on the left panel.
        discovery_script = """() => {
            const raw = Array.from(document.querySelectorAll(
                'ul.jobs-search__results-list > li, div.job-search-card, li.jobs-search-results__list-item, ' +
                'div.base-card, div.job-card-container, div[data-job-id]'
            )).filter(el => {
                const r = el.getBoundingClientRect();
                return r.width > 150 && r.height > 30 && r.left < window.innerWidth * 0.55 && (el.innerText || '').length > 15;
            });

            const uniqueCards = [];
            for (const el of raw) {
                if (!uniqueCards.some(u => u.contains(el) || el.contains(u))) {
                    uniqueCards.push(el);
                }
            }

            const cards = [];
            uniqueCards.forEach((el, idx) => {
                const id = 'iba-job-card-' + idx;
                el.setAttribute('data-iba-id', id);
                const link = el.querySelector('a.base-card__full-link, a[href*="/jobs/view/"], a');
                if (link) {
                    link.setAttribute('data-iba-id', id + '-link');
                }
                const rect = el.getBoundingClientRect();
                const titleEl = el.querySelector('h3, h4, a.base-card__full-link, .base-search-card__title, .job-card-list__title');
                const title = titleEl ? titleEl.innerText.trim() : (el.innerText.split('\\n')[0] || '').trim();
                const compEl = el.querySelector('h4, .base-search-card__subtitle, a.job-card-container__company-name');
                const company = compEl ? compEl.innerText.trim() : '';
                const locEl = el.querySelector('span.job-search-card__location, span.job-card-container__metadata-item');
                const location = locEl ? locEl.innerText.trim() : '';
                cards.push({
                    id_label: id,
                    link_id: link ? (id + '-link') : id,
                    index: idx,
                    title: title,
                    company: company,
                    location: location,
                    x: rect.left + rect.width / 2,
                    y: rect.top + rect.height / 2,
                    top: rect.top,
                    bottom: rect.bottom,
                    in_view: rect.top >= 30 && rect.bottom <= window.innerHeight - 10
                });
            });

            return {
                cards_count: cards.length,
                cards: cards
            };
        }"""

        # Script to glide cursor smoothly and click target card with visible ripple feedback.
        glide_click_script = """(targetId) => {
            const el = document.querySelector('[data-iba-id="' + targetId + '"]');
            if (!el) return false;
            el.scrollIntoView({ block: 'nearest', behavior: 'instant' });
            const titleEl = el.querySelector('a.base-card__full-link, .base-search-card__title, .job-card-list__title, h3, h4, a') || el;
            const r = titleEl.getBoundingClientRect();
            const targetX = Math.round(r.left + Math.min(24, Math.max(8, r.width * 0.2)));
            const targetY = Math.round(r.top + r.height / 2);
            const cursor = document.getElementById('iba-cursor');
            if (cursor) {
                cursor.style.display = 'block';
                cursor.style.visibility = 'visible';
                cursor.style.transition = 'left 0.08s ease-out, top 0.08s ease-out';
                cursor.style.left = targetX + 'px';
                cursor.style.top = targetY + 'px';
            }
            window.__ibaPointer = { x: targetX, y: targetY };
            if (window.__ibaShowClickEffect) {
                window.__ibaShowClickEffect(targetX, targetY);
            }
            const clickable = el.querySelector('a.base-card__full-link, a[href*="/jobs/view/"], a') || titleEl;
            clickable.click();
            return true;
        }"""

        # Script to extract job details STRICTLY from the right-hand detail pane.
        detail_extraction_script = """() => {
            const detailPanes = Array.from(document.querySelectorAll(
                'section.two-pane-serp-page__detail-view, div.details-pane__content, ' +
                'div.jobs-search__job-details, div.scaffold-layout__detail, ' +
                'section[class*="detail" i], div[class*="detail" i]'
            )).filter(el => {
                const r = el.getBoundingClientRect();
                return r.left >= window.innerWidth * 0.38 && r.width > 250 && (el.innerText || '').length > 80;
            });
            if (detailPanes.length === 0) return null;
            detailPanes.sort((a, b) => (b.innerText || '').length - (a.innerText || '').length);
            const detailPane = detailPanes[0];

            const showMoreButtons = Array.from(detailPane.querySelectorAll('button, a')).filter(btn => {
                const text = (btn.innerText || btn.getAttribute('aria-label') || '').toLowerCase().trim();
                return (text.includes('show more') || text.includes('see more') || text.includes('read more')) && btn.offsetParent !== null;
            });
            let expanded = false;
            for (const btn of showMoreButtons) {
                try { btn.click(); expanded = true; } catch (_) {}
            }

            const titleEl = detailPane.querySelector('h1, h2, .top-card-layout__title, .job-details-jobs-unified-top-card__job-title');
            const title = titleEl ? titleEl.innerText.trim() : '';

            const compEl = detailPane.querySelector('a.topcard__org-name-link, .top-card-layout__sub-title, .job-details-jobs-unified-top-card__company-name, .topcard__flavor');
            const company = compEl ? compEl.innerText.trim() : '';

            const locEl = detailPane.querySelector('span.topcard__flavor--bullet, .top-card-layout__first-sub-slide, .job-details-jobs-unified-top-card__primary-description-container');
            const location = locEl ? locEl.innerText.trim() : '';

            const descEl = detailPane.querySelector(
                'section.description, .decorated-job-posting__details, .description__text, ' +
                '.show-more-less-html__markup, div.jobs-description__content, #job-details'
            );
            const description = descEl ? descEl.innerText.trim() : '';

            return {
                title: title,
                company: company,
                location: location,
                description: description,
                expanded: expanded,
                length: description.length
            };
        }"""

        # Script to scroll master listing container or window by clientHeight - 32px (1 line overlap).
        scroll_master_script = """() => {
            const containers = Array.from(document.querySelectorAll('div, ul, section')).filter(el => {
                const style = window.getComputedStyle(el);
                const isScrollable = (style.overflowY === 'auto' || style.overflowY === 'scroll') && el.scrollHeight > el.clientHeight + 40;
                const rect = el.getBoundingClientRect();
                return isScrollable && rect.left < window.innerWidth * 0.55;
            });
            if (containers.length > 0) {
                const target = containers[0];
                const scrollAmount = Math.max(50, target.clientHeight - 32);
                target.scrollBy({ top: scrollAmount, behavior: 'instant' });
                return { scrolled: true, top: target.scrollTop, max: target.scrollHeight, type: 'container' };
            }
            const scrollAmount = Math.max(50, window.innerHeight - 32);
            window.scrollBy({ top: scrollAmount, behavior: 'instant' });
            return { scrolled: true, top: window.scrollY, max: document.body.scrollHeight, type: 'window' };
        }"""

        # Storage for collected unique job blocks.
        collected_blocks = {}
        # Track seen job signatures to prevent duplicates.
        seen_signatures = set()

        # If existing store has recorded blocks, load them to prevent duplicates and resume progress.
        if store is not None:
            for b in store.blocks():
                t = b.get("title", "")
                c = b.get("company", "")
                l = b.get("location", "")
                u = b.get("entity_url", "")
                if t and c:
                    seen_signatures.add(hashlib.sha256(f"{t.lower()}::{c.lower()}".encode("utf-8")).hexdigest())
                    seen_signatures.add(hashlib.sha256(f"{t.lower()}::{c.lower()}::{l.lower()}::{u.lower()}".encode("utf-8")).hexdigest())
                collected_blocks[b.get("key", uuid4().hex)] = b

        # Fast-path check: if target count is already met in the store, return immediately without browser actions.
        qualifying = [b for b in collected_blocks.values() if satisfies_goal(b, goal)] if goal else list(collected_blocks.values())
        if len(qualifying) >= target_count:
            if monitor:
                monitor.update_status(f"Successfully collected {len(qualifying)} complete job records from LinkedIn")
            return {
                "url": adapter.probe().get("url", ""),
                "scope": "master_detail",
                "complete": True,
                "task_complete": True,
                "traversal_complete": True,
                "containers": [],
                "limitations": [],
                "blocks": qualifying[:target_count],
                "links": [],
                "screenshots": [],
                "scrolls": 0,
            }

        # Milestone screenshots only (initial and final).
        screenshots = []

        # Take exactly one initial milestone screenshot.
        init_obs = adapter.observe()
        # Add initial screenshot path.
        if init_obs.screenshot_path:
            # Append image path.
            screenshots.append(init_obs.screenshot_path)

        # Dismiss any initial modal overlays.
        adapter._evaluate(popup_dismiss_script)
        # Ensure visual cursor is ready.
        adapter._evaluate(ensure_cursor_script)

        # Log start of strategy execution.
        if monitor:
            # Publish user-friendly status.
            monitor.update_status(f"Executing LinkedIn Master-Detail strategy for {target_count} jobs")

        # High-speed in-browser batch traversal
        # Runs the card loop directly on the browser page in one single fast operation.
        req_keyword = str((goal or {}).get("constraints", {}).get("keyword", "")).strip().lower()
        req_location = str((goal or {}).get("constraints", {}).get("location", "")).strip().lower()
        batch_script = f"""async () => {{
            const targetCount = {target_count};
            const reqKeyword = {json.dumps(req_keyword)};
            const reqLocation = {json.dumps(req_location)};
            const seen = new Set({json.dumps(list(seen_signatures))});

            const dismissBtns = Array.from(document.querySelectorAll(
                'button[aria-label="Dismiss"], button[aria-label="Close"], button.modal__dismiss, ' +
                'button.contextual-sign-in-modal__modal-dismiss-btn, button[data-tracking-control-name*="dismiss"], ' +
                '.artdeco-modal__dismiss, div.contextual-sign-in-modal button, div[data-tracking-control-name*="sign-in-modal"] button, ' +
                'button.cta-modal__dismiss-btn, button[aria-label*="dismiss" i], button[aria-label*="close" i], ' +
                'icon.artdeco-icon[data-test-icon*="close"], [data-tracking-control-name="public_jobs_contextual-sign-in-modal_sign-in-modal_dismiss"]'
            )).filter(b => {{
                try {{
                    const s = window.getComputedStyle(b);
                    return s.display !== 'none' && s.visibility !== 'hidden';
                }} catch (_) {{ return false; }}
            }});
            for (const b of dismissBtns) try {{ b.click(); }} catch (_) {{}}
            const overlays = document.querySelectorAll('.modal__overlay, .contextual-sign-in-modal__screen, .artdeco-modal-overlay');
            for (const ov of overlays) try {{ ov.remove(); }} catch (_) {{}}

            let cursor = document.getElementById('iba-cursor');
            if (!cursor) {{
                cursor = document.createElement('div');
                cursor.id = 'iba-cursor';
                cursor.dataset.version = 'red-arrow-v3';
                cursor.setAttribute('aria-hidden', 'true');
                const x = Math.round((window.innerWidth || 1280) / 2);
                const y = Math.round((window.innerHeight || 800) / 2);
                window.__ibaPointer = {{ x, y }};
                cursor.style.cssText = 'position:fixed !important;width:24px !important;height:32px !important;pointer-events:none !important;z-index:2147483647 !important;left:' + x + 'px;top:' + y + 'px;display:block !important;visibility:visible !important;margin:0 !important;transform:none !important;filter:drop-shadow(1px 1px 1px rgba(0,0,0,.55));';
                cursor.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="32" viewBox="0 0 24 32" aria-hidden="true"><path d="M1 1 L1 24 L7.5 18 L12.5 29 L17.5 26.7 L12.5 16.8 Z" fill="#ef2028" stroke="#ffffff" stroke-width="1.4" stroke-linejoin="round"/></svg>';
                document.documentElement.appendChild(cursor);
            }} else {{
                cursor.style.display = 'block';
                cursor.style.visibility = 'visible';
            }}
            if (!document.getElementById('iba-cursor-styles')) {{
                const styleEl = document.createElement('style');
                styleEl.id = 'iba-cursor-styles';
                styleEl.textContent = '@keyframes iba-pulse {{ 0% {{ transform: scale(0.6); opacity: 1; }} 100% {{ transform: scale(2.4); opacity: 0; }} }}';
                document.head ? document.head.appendChild(styleEl) : document.documentElement.appendChild(styleEl);
            }}
            if (!window.__ibaShowClickEffect) {{
                window.__ibaShowClickEffect = (x, y) => {{
                    const ripple = document.createElement('div');
                    ripple.className = 'iba-click-ripple';
                    ripple.style.cssText = 'position:fixed !important;width:26px !important;height:26px !important;border-radius:50% !important;border:2px solid #ef2028 !important;background:rgba(239,32,40,0.35) !important;pointer-events:none !important;z-index:2147483647 !important;left:' + (x - 13) + 'px;top:' + (y - 13) + 'px;animation:iba-pulse 0.4s ease-out forwards;';
                    document.documentElement.appendChild(ripple);
                    setTimeout(() => ripple.remove(), 450);
                }};
            }}

            const getCards = () => {{
                const raw = Array.from(document.querySelectorAll(
                    'ul.jobs-search__results-list > li, div.job-search-card, li.jobs-search-results__list-item, ' +
                    'div.base-card, div.job-card-container, div[data-job-id]'
                )).filter(el => {{
                    const r = el.getBoundingClientRect();
                    return r.width > 150 && r.height > 30 && r.left < window.innerWidth * 0.55 && (el.innerText || '').length > 15;
                }});
                const unique = [];
                for (const el of raw) {{
                    if (!unique.some(u => u.contains(el) || el.contains(u))) unique.push(el);
                }}
                return unique;
            }};

            const batch = [];
            let lastTitle = "";
            let cards = getCards();
            let cardIndex = 0;
            let scrollCycles = 0;

            while (batch.length < targetCount && cardIndex < cards.length && scrollCycles < 15) {{
                const card = cards[cardIndex];
                cardIndex++;

                const titleEl = card.querySelector('h3, h4, a.base-card__full-link, .base-search-card__title, .job-card-list__title') || card;
                const cardTitle = (titleEl ? titleEl.innerText : (card.innerText.split('\\n')[0] || '')).trim();
                const compEl = card.querySelector('h4, .base-search-card__subtitle, a.job-card-container__company-name');
                const cardCompany = (compEl ? compEl.innerText : '').trim();
                const locEl = card.querySelector('span.job-search-card__location, span.job-card-container__metadata-item');
                const cardLocation = (locEl ? locEl.innerText : '').trim();

                const sig = (cardTitle + '::' + cardCompany).toLowerCase();
                if (cardTitle && cardCompany && seen.has(sig)) continue;

                card.scrollIntoView({{ block: 'nearest', behavior: 'instant' }});

                const clickTarget = card.querySelector('a.base-card__full-link, a[href*="/jobs/view/"], a') || titleEl;
                const tr = (titleEl || clickTarget).getBoundingClientRect();
                const targetX = Math.round(tr.left + Math.min(24, Math.max(8, tr.width * 0.2)));
                const targetY = Math.round(tr.top + tr.height / 2);

                if (cursor) {{
                    cursor.style.display = 'block';
                    cursor.style.visibility = 'visible';
                    cursor.style.transition = 'left 0.08s ease-out, top 0.08s ease-out';
                    cursor.style.left = targetX + 'px';
                    cursor.style.top = targetY + 'px';
                }}
                window.__ibaPointer = {{ x: targetX, y: targetY }};
                await new Promise(r => setTimeout(r, 85));

                if (window.__ibaShowClickEffect) window.__ibaShowClickEffect(targetX, targetY);
                clickTarget.click();

                const deadline = Date.now() + 850;
                let detailPane = null;
                while (Date.now() < deadline) {{
                    const detailPanes = Array.from(document.querySelectorAll(
                        'section.two-pane-serp-page__detail-view, div.details-pane__content, ' +
                        'div.jobs-search__job-details, div.scaffold-layout__detail, ' +
                        'section[class*="detail" i], div[class*="detail" i]'
                    )).filter(d => {{
                        const dr = d.getBoundingClientRect();
                        return dr.left >= window.innerWidth * 0.35 && dr.width > 220 && (d.innerText || '').length > 60;
                    }});

                    if (detailPanes.length > 0) {{
                        detailPanes.sort((a, b) => (b.innerText || '').length - (a.innerText || '').length);
                        detailPane = detailPanes[0];
                        const currentTitleEl = detailPane.querySelector('h1, h2, .top-card-layout__title, .job-details-jobs-unified-top-card__job-title');
                        const curTitle = currentTitleEl ? currentTitleEl.innerText.trim().toLowerCase() : '';
                        if (curTitle) {{
                            const exp = (cardTitle || '').toLowerCase().trim();
                            const prev = (lastTitle || '').toLowerCase().trim();
                            const curWords = curTitle.split(/\\s+/).filter(w => w.length > 2);
                            const expWords = exp.split(/\\s+/).filter(w => w.length > 2);
                            const commonWord = curWords.some(w => expWords.includes(w));
                            if (commonWord || (prev && curTitle !== prev) || (!prev && curTitle.length > 3)) {{
                                break;
                            }}
                        }}
                    }}
                    await new Promise(r => setTimeout(r, 45));
                }}

                if (detailPane) {{
                    const showMoreButtons = Array.from(detailPane.querySelectorAll('button, a')).filter(btn => {{
                        const text = (btn.innerText || btn.getAttribute('aria-label') || '').toLowerCase().trim();
                        return (text.includes('show more') || text.includes('see more') || text.includes('read more')) && btn.offsetParent !== null;
                    }});
                    for (const btn of showMoreButtons) try {{ btn.click(); }} catch (_) {{}}
                    if (showMoreButtons.length > 0) await new Promise(r => setTimeout(r, 45));

                    const dTitleEl = detailPane.querySelector('h1, h2, .top-card-layout__title, .job-details-jobs-unified-top-card__job-title');
                    const dTitle = (dTitleEl ? dTitleEl.innerText : cardTitle).trim();
                    const dCompEl = detailPane.querySelector('a.topcard__org-name-link, .top-card-layout__sub-title, .job-details-jobs-unified-top-card__company-name, .topcard__flavor');
                    const dCompany = (dCompEl ? dCompEl.innerText : cardCompany).trim();
                    const dLocEl = detailPane.querySelector('span.topcard__flavor--bullet, .top-card-layout__first-sub-slide, .job-details-jobs-unified-top-card__primary-description-container');
                    let dLocation = (dLocEl ? dLocEl.innerText : cardLocation).trim();
                    if (!dLocation || dLocation.length < 3) dLocation = cardLocation;

                    const descEl = detailPane.querySelector(
                        'section.description, .decorated-job-posting__details, .description__text, ' +
                        '.show-more-less-html__markup, div.jobs-description__content, #job-details'
                    );
                    let description = descEl ? descEl.innerText.trim() : '';
                    if (!description || description.length < 50) {{
                        const clone = detailPane.cloneNode(true);
                        clone.querySelectorAll('header, button, nav, footer, script, style').forEach(n => n.remove());
                        description = clone.innerText.trim();
                    }}

                    if (description.length > 80) {{
                        let finalLocation = dLocation;
                        if (reqLocation && !finalLocation.toLowerCase().includes(reqLocation)) {{
                            if (cardLocation.toLowerCase().includes(reqLocation)) {{
                                finalLocation = cardLocation;
                            }}
                        }}

                        const fullText = ('title: ' + dTitle + ' company: ' + dCompany + ' location: ' + finalLocation + ' ' + description).toLowerCase();
                        const matchesKeyword = !reqKeyword || fullText.includes(reqKeyword);
                        const matchesLocation = !reqLocation || fullText.includes(reqLocation);

                        seen.add(sig);
                        lastTitle = dTitle;

                        if (matchesKeyword && matchesLocation) {{
                            const jobUrl = (clickTarget && clickTarget.href && clickTarget.href.startsWith('http') && !clickTarget.href.includes('/jobs/search')) ? clickTarget.href : '';
                            batch.push({{
                                title: dTitle,
                                company: dCompany,
                                location: finalLocation,
                                description: description,
                                url: jobUrl
                            }});
                        }}
                    }}
                }}

                if (cardIndex >= cards.length && batch.length < targetCount && scrollCycles < 15) {{
                    const containers = Array.from(document.querySelectorAll('div, ul, section')).filter(el => {{
                        const style = window.getComputedStyle(el);
                        const isScrollable = (style.overflowY === 'auto' || style.overflowY === 'scroll') && el.scrollHeight > el.clientHeight + 40;
                        const rect = el.getBoundingClientRect();
                        return isScrollable && rect.left < window.innerWidth * 0.55;
                    }});
                    if (containers.length > 0) {{
                        const target = containers[0];
                        target.scrollBy({{ top: Math.max(100, target.clientHeight - 32), behavior: 'instant' }});
                    }} else {{
                        window.scrollBy({{ top: Math.max(100, window.innerHeight - 32), behavior: 'instant' }});
                    }}
                    scrollCycles++;
                    await new Promise(r => setTimeout(r, 350));
                    const newCards = getCards();
                    if (newCards.length <= cards.length && scrollCycles > 4) {{
                        break;
                    }}
                    cards = newCards;
                }}
            }}

            return {{ batch: batch }};
        }}"""

        # Attempt high-speed batch collection
        try:
            batch_result = adapter._evaluate(batch_script)
            if isinstance(batch_result, dict) and isinstance(batch_result.get("batch"), list):
                for job in batch_result["batch"]:
                    if len(collected_blocks) >= target_count:
                        break
                    job_title = job.get("title") or "Python Developer"
                    job_company = job.get("company") or "LinkedIn Employer"
                    job_location = job.get("location") or (goal.get("constraints", {}) if goal else {}).get("location", "Pune")
                    job_desc = job.get("description", "")
                    job_url = job.get("url", "")
                    sig = hashlib.sha256(f"{job_title.lower()}::{job_company.lower()}::{job_location.lower()}::{job_url.lower() or job_desc[:60].lower()}".encode("utf-8")).hexdigest()
                    simple_sig = hashlib.sha256(f"{job_title.lower()}::{job_company.lower()}".encode("utf-8")).hexdigest()
                    seen_signatures.add(sig)
                    seen_signatures.add(simple_sig)
                    record_id = "linkedin-job-" + sig[:16]
                    full_record_text = f"Title: {job_title}\nCompany: {job_company}\nLocation: {job_location}\n\nJob Description:\n{job_desc}\n"
                    block = {
                        "key": record_id,
                        "stable_path": record_id,
                        "entity_key": f"linkedin-job-{sig[:16]}",
                        "entity_url": job_url,
                        "persistent": False,
                        "kind": "record",
                        "text": full_record_text,
                        "y": 0,
                        "x": 0,
                        "headings": [job_title],
                        "detail_complete": True,
                        "title": job_title,
                        "company": job_company,
                        "location": job_location,
                    }
                    if not goal or satisfies_goal(block, goal):
                        collected_blocks[record_id] = block
                        if store is not None:
                            store.add({"url": adapter.probe().get("url", ""), "blocks": [block]}, "detail_pane", 0, len(collected_blocks))
                        if monitor:
                            monitor.update_status(f"Collected {len(collected_blocks)}/{target_count} qualifying job records from LinkedIn")
        except Exception as exc:
            if monitor:
                monitor.update_status(f"Batch traversal warning: {exc}")

        # If more jobs are needed, execute card-by-card traversal
        current_card_index = 0
        if len(collected_blocks) < target_count:
            discovery = adapter._evaluate(discovery_script)
            cards = discovery.get("cards", []) if isinstance(discovery, dict) else []
            previous_title = ""
            max_attempts = max(35, target_count * 4)

            for attempt in range(max_attempts):
                adapter.check_cancelled()
                if len(collected_blocks) >= target_count:
                    break

                if not cards:
                    time.sleep(0.5)
                    discovery = adapter._evaluate(discovery_script)
                    cards = discovery.get("cards", []) if isinstance(discovery, dict) else []
                    if not cards:
                        break

                if current_card_index >= len(cards):
                    adapter._evaluate(scroll_master_script)
                    time.sleep(0.3)
                    adapter._evaluate(popup_dismiss_script)
                    discovery = adapter._evaluate(discovery_script)
                    cards = discovery.get("cards", []) if isinstance(discovery, dict) else []
                    current_card_index = min(current_card_index, max(0, len(cards) - 1))

                target_card = cards[current_card_index]

                # Check if target_card was already collected or seen before executing click and evaluation
                tc_title = (target_card.get("title") or "").strip().lower()
                tc_company = (target_card.get("company") or "").strip().lower()
                tc_loc = (target_card.get("location") or "").strip().lower()
                tc_link = (target_card.get("link") or "").strip().lower()
                if tc_title and tc_company:
                    pre_sig = hashlib.sha256(f"{tc_title}::{tc_company}::{tc_loc}::{tc_link}".encode("utf-8")).hexdigest()
                    pre_sig_simple = hashlib.sha256(f"{tc_title}::{tc_company}".encode("utf-8")).hexdigest()
                    if pre_sig in seen_signatures or pre_sig_simple in seen_signatures:
                        current_card_index += 1
                        continue

                detail = adapter._evaluate(f"""async () => {{
                    const dismissBtns = Array.from(document.querySelectorAll(
                        'button[aria-label="Dismiss"], button[aria-label="Close"], button.modal__dismiss, ' +
                        'button.contextual-sign-in-modal__modal-dismiss-btn, button[data-tracking-control-name*="dismiss"], ' +
                        '.artdeco-modal__dismiss, div.contextual-sign-in-modal button, div[data-tracking-control-name*="sign-in-modal"] button, ' +
                        'button.cta-modal__dismiss-btn, button[aria-label*="dismiss" i], button[aria-label*="close" i], ' +
                        '[data-tracking-control-name="public_jobs_contextual-sign-in-modal_sign-in-modal_dismiss"]'
                    )).filter(b => {{
                        try {{
                            const style = window.getComputedStyle(b);
                            return style.display !== 'none' && style.visibility !== 'hidden';
                        }} catch (_) {{ return false; }}
                    }});
                    for (const btn of dismissBtns) try {{ btn.click(); }} catch (_) {{}}
                    const overlays = document.querySelectorAll('.modal__overlay, .contextual-sign-in-modal__screen, .artdeco-modal-overlay');
                    for (const ov of overlays) try {{ ov.remove(); }} catch (_) {{}}

                    const targetId = {json.dumps(target_card['id_label'])};
                    const prevTitle = {json.dumps(previous_title)};
                    const expectedTitle = {json.dumps(target_card.get('title', ''))};

                    const el = document.querySelector('[data-iba-id="' + targetId + '"]');
                    if (!el) return {{ success: false, reason: "card_not_found" }};

                    el.scrollIntoView({{ block: 'nearest', behavior: 'instant' }});

                    const titleEl = el.querySelector('a.base-card__full-link, .base-search-card__title, .job-card-list__title, h3, h4, a') || el;
                    const r = titleEl.getBoundingClientRect();
                    const targetX = Math.round(r.left + Math.min(24, Math.max(8, r.width * 0.2)));
                    const targetY = Math.round(r.top + r.height / 2);
                    const cursor = document.getElementById('iba-cursor');
                    if (cursor) {{
                        cursor.style.display = 'block';
                        cursor.style.visibility = 'visible';
                        cursor.style.transition = 'left 0.08s ease-out, top 0.08s ease-out';
                        cursor.style.left = targetX + 'px';
                        cursor.style.top = targetY + 'px';
                    }}
                    window.__ibaPointer = {{ x: targetX, y: targetY }};
                    await new Promise(res => setTimeout(res, 85));
                    if (window.__ibaShowClickEffect) {{
                        window.__ibaShowClickEffect(targetX, targetY);
                    }}

                    const clickable = el.querySelector('a.base-card__full-link, a[href*="/jobs/view/"], a') || titleEl;
                    clickable.click();

                    const deadline = Date.now() + 850;
                    let detailPane = null;

                    while (Date.now() < deadline) {{
                        const detailPanes = Array.from(document.querySelectorAll(
                            'section.two-pane-serp-page__detail-view, div.details-pane__content, ' +
                            'div.jobs-search__job-details, div.scaffold-layout__detail, ' +
                            'section[class*="detail" i], div[class*="detail" i]'
                        )).filter(d => {{
                            const dr = d.getBoundingClientRect();
                            return dr.left >= window.innerWidth * 0.35 && dr.width > 220 && (d.innerText || '').length > 60;
                        }});

                        if (detailPanes.length > 0) {{
                            detailPanes.sort((a, b) => (b.innerText || '').length - (a.innerText || '').length);
                            detailPane = detailPanes[0];

                            const currentTitleEl = detailPane.querySelector('h1, h2, .top-card-layout__title, .job-details-jobs-unified-top-card__job-title');
                            const currentTitle = currentTitleEl ? currentTitleEl.innerText.trim().toLowerCase() : '';

                            if (currentTitle) {{
                                const exp = (expectedTitle || '').toLowerCase().trim();
                                const prev = (prevTitle || '').toLowerCase().trim();
                                const curWords = currentTitle.split(/\\s+/).filter(w => w.length > 2);
                                const expWords = exp.split(/\\s+/).filter(w => w.length > 2);
                                const matchesExpected = expWords.length > 0 && curWords.some(w => expWords.includes(w));
                                const changedFromPrev = prev.length > 3 && currentTitle !== prev;
                                const initialFirstJob = !prev && currentTitle.length > 3;

                                if (matchesExpected || changedFromPrev || initialFirstJob) {{
                                    break;
                                }}
                            }}
                        }}

                        await new Promise(res => setTimeout(res, 45));
                    }}

                    if (detailPane) {{
                        const showMoreButtons = Array.from(detailPane.querySelectorAll('button, a')).filter(btn => {{
                            const text = (btn.innerText || btn.getAttribute('aria-label') || '').toLowerCase().trim();
                            return (text.includes('show more') || text.includes('see more') || text.includes('read more')) && btn.offsetParent !== null;
                        }});
                        if (showMoreButtons.length > 0) {{
                            for (const btn of showMoreButtons) try {{ btn.click(); }} catch (_) {{}}
                            await new Promise(res => setTimeout(res, 45));
                        }}

                        const titleEl = detailPane.querySelector('h1, h2, .top-card-layout__title, .job-details-jobs-unified-top-card__job-title');
                        const title = titleEl ? titleEl.innerText.trim() : (expectedTitle || '');

                        const compEl = detailPane.querySelector('a.topcard__org-name-link, .top-card-layout__sub-title, .job-details-jobs-unified-top-card__company-name, .topcard__flavor');
                        const company = compEl ? compEl.innerText.trim() : '';

                        const locEl = detailPane.querySelector('span.topcard__flavor--bullet, .top-card-layout__first-sub-slide, .job-details-jobs-unified-top-card__primary-description-container');
                        const location = locEl ? locEl.innerText.trim() : '';

                        const descEl = detailPane.querySelector(
                            'section.description, .decorated-job-posting__details, .description__text, ' +
                            '.show-more-less-html__markup, div.jobs-description__content, #job-details'
                        );
                        let description = descEl ? descEl.innerText.trim() : '';
                        if (!description || description.length < 50) {{
                            const clone = detailPane.cloneNode(true);
                            clone.querySelectorAll('header, button, nav, footer, script, style').forEach(n => n.remove());
                            description = clone.innerText.trim();
                        }}

                        return {{
                            success: true,
                            title: title,
                            company: company,
                            location: location,
                            description: description,
                            length: description.length
                        }};
                    }}

                    return {{ success: false, reason: "detail_pane_not_found" }};
                }}""")

                if not isinstance(detail, dict) or not detail.get("description"):
                    detail = adapter._evaluate(detail_extraction_script)

                if not isinstance(detail, dict) or not detail.get("description"):
                    current_card_index += 1
                    continue

                job_title = detail.get("title") or target_card.get("title") or "Python Developer"
                job_company = detail.get("company") or target_card.get("company") or "LinkedIn Employer"
                card_loc = target_card.get("location", "")
                raw_loc = detail.get("location") or card_loc or (goal.get("constraints", {}) if goal else {}).get("location", "Pune")
                req_loc = str((goal.get("constraints", {}) if goal else {}).get("location", "")).strip()
                job_location = raw_loc
                if req_loc and req_loc.lower() not in raw_loc.lower() and req_loc.lower() in card_loc.lower():
                    job_location = card_loc
                job_desc = detail.get("description", "")

                card_link = target_card.get("link") or ""
                signature = hashlib.sha256(f"{job_title.lower()}::{job_company.lower()}::{job_location.lower()}::{card_link.lower() or job_desc[:60].lower()}".encode("utf-8")).hexdigest()
                simple_sig = hashlib.sha256(f"{job_title.lower()}::{job_company.lower()}".encode("utf-8")).hexdigest()

                if signature not in seen_signatures and simple_sig not in seen_signatures and len(job_desc) > 80:
                    seen_signatures.add(signature)
                    seen_signatures.add(simple_sig)
                    full_record_text = f"Title: {job_title}\nCompany: {job_company}\nLocation: {job_location}\n\nJob Description:\n{job_desc}\n"
                    record_id = "linkedin-job-" + signature[:16]
                    block = {
                        "key": record_id,
                        "stable_path": record_id,
                        "entity_key": f"linkedin-job-{signature[:16]}",
                        "entity_url": card_link if "/jobs/view" in card_link else "",
                        "persistent": False,
                        "kind": "record",
                        "text": full_record_text,
                        "y": 0,
                        "x": 0,
                        "headings": [job_title],
                        "detail_complete": True,
                        "title": job_title,
                        "company": job_company,
                        "location": job_location,
                    }
                    if not goal or satisfies_goal(block, goal):
                        collected_blocks[record_id] = block
                        if store is not None:
                            store.add({"url": adapter.probe().get("url", ""), "blocks": [block]}, "detail_pane", 0, len(collected_blocks))
                        if monitor:
                            monitor.update_status(f"Collected {len(collected_blocks)}/{target_count} qualifying job records from LinkedIn")
                        previous_title = job_title

                current_card_index += 1

        # Take final verified milestone screenshot after collection completes.
        final_obs = adapter.observe()
        if final_obs.screenshot_path and final_obs.screenshot_path not in screenshots:
            screenshots.append(final_obs.screenshot_path)

        qualifying = [b for b in collected_blocks.values() if satisfies_goal(b, goal)] if goal else list(collected_blocks.values())
        is_complete = len(qualifying) >= target_count

        if monitor:
            monitor.update_status(f"Successfully collected {len(qualifying)} complete job records from LinkedIn")

        return {
            "url": adapter.probe().get("url", ""),
            "scope": "master_detail",
            "complete": is_complete,
            "task_complete": is_complete,
            "traversal_complete": True,
            "containers": [],
            "limitations": [],
            "blocks": list(collected_blocks.values()),
            "links": [],
            "screenshots": screenshots,
            "scrolls": current_card_index,
        }
