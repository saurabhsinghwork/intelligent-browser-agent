// Observe, capture, resolve, or scroll rendered UI without model-generated code.
(request) => {
  // Persist actual node identities across observations of the same document.
  const state = window.__ibaState || (window.__ibaState = {prefix: Date.now().toString(36) + Math.random().toString(36).slice(2, 6), next: 0});
  // Assign stable identities instead of re-querying positional element indices.
  const identify = element => {
    // Reuse a reference only for this concrete node.
    if (!element.hasAttribute('data-iba-id')) element.setAttribute('data-iba-id', state.prefix + '-' + (++state.next));
    // Return the identity used by native input.
    return element.getAttribute('data-iba-id');
  };
  // Recognize rendered content without mistaking hidden labels for visible text.
  const visible = element => {
    // Exclude absent nodes and the passive cursor.
    if (!element || element.id === 'iba-cursor') return false;
    // Read computed visibility and layout geometry.
    const style = element.ownerDocument.defaultView.getComputedStyle(element);
    // Measure without changing scrolling or focus.
    const box = element.getBoundingClientRect();
    // Retain rendered below-fold nodes, while excluding hidden or zero-area nodes.
    return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0' && box.width > 0 && box.height > 0;
  };
  // Build a document-reload-stable structural path without screen coordinates.
  const structuralPath = element => {
    // Accumulate only a bounded ancestry path to keep capture payloads compact.
    const parts = [];
    // Walk from the source node toward the document root.
    for (let current = element; current && current.nodeType === Node.ELEMENT_NODE && parts.length < 12; current = current.parentElement) {
      // Prefer a website-owned ID while excluding the transient application identity.
      const ownedId = current.id && current.id !== 'iba-cursor' ? '#' + current.id : '';
      // Stable record attributes survive framework node replacement when available.
      const logical = current.getAttribute('data-job-id') || current.getAttribute('data-entity-urn') || current.getAttribute('data-id') || current.getAttribute('aria-rowindex') || current.getAttribute('data-index') || '';
      // Positional structure distinguishes equal sibling values without using scroll position.
      const siblings = current.parentElement ? Array.from(current.parentElement.children).filter(item => item.tagName === current.tagName) : [];
      // Use one-based source order only when a stronger website identity is absent.
      const position = !ownedId && !logical && siblings.length > 1 ? ':nth-of-type(' + (siblings.indexOf(current) + 1) + ')' : '';
      // Preserve tag, stable identity, and structural position as one segment.
      parts.unshift(current.tagName.toLowerCase() + ownedId + (logical ? '[logical=' + logical + ']' : '') + position);
      // A website-owned ID already anchors the remaining path.
      if (ownedId) break;
    }
    // Join segments into a deterministic semantic path.
    return parts.join('>');
  };
  // Resolve the nearest logical record and its real destination for entity deduplication.
  const entityContext = element => {
    // Cards, rows, articles, and list items are common cross-site record containers.
    const container = element.closest('article,li,tr,[role=listitem],[role=row],[data-job-id],[data-entity-urn],[data-product-id]') || element;
    // Prefer a link inside the record, or the record itself when it is a link.
    const anchor = container.matches?.('a[href]') ? container : container.querySelector?.('a[href]');
    // Retain an actual web destination only.
    const url = anchor && /^https?:/i.test(anchor.href || '') ? anchor.href : '';
    // Prefer explicit website record IDs before falling back to the link or path.
    const explicit = container.getAttribute?.('data-job-id') || container.getAttribute?.('data-entity-urn') || container.getAttribute?.('data-product-id') || container.getAttribute?.('data-id') || '';
    // Return enough provenance for Python-side canonicalization and task-scoped output.
    return {key: explicit || url || structuralPath(container), url, path: structuralPath(container)};
  };
  // Describe whether a control belongs to a rendered dialog or floating interruption.
  const overlayContext = element => {
    // Retain the richest matching ancestor instead of stopping at a close button named `modal-*`.
    let best = null;
    // Walk across ordinary and open-shadow ancestry without relying on one site's classes.
    for (let current = element; current; current = current.parentElement || current.getRootNode?.().host || null) {
      // Read semantic dialog attributes and broad conventional overlay tokens.
      const token = ((current.id || '') + ' ' + (current.className?.baseVal || current.className || '')).toLowerCase();
      // Measure actual rendered positioning rather than treating every container as a popup.
      const style = current.ownerDocument.defaultView.getComputedStyle(current);
      // Dialog semantics are strongest; a substantial fixed element covers toast/banner variants.
      const semantic = current.tagName === 'DIALOG' || current.getAttribute('role') === 'dialog' || current.getAttribute('aria-modal') === 'true' || /(?:^|[\s_-])(modal|popup|overlay|toast)(?:$|[\s_-])/.test(token);
      // Small fixed icon controls inherit interruption context from their substantial fixed ancestor.
      const box = current.getBoundingClientRect();
      // Require useful size so fixed navigation icons are not misclassified as overlays.
      const floating = style.position === 'fixed' && box.width >= 120 && box.height >= 60;
      // Compare every qualifying ancestor because a close icon's own class may contain `modal`.
      if (semantic || floating) {
        // Preserve rendered surrounding wording rather than only the icon's accessible name.
        const text = (current.innerText || current.getAttribute('aria-label') || '').slice(0, 1200);
        // Prefer the container that supplies the most useful interruption-purpose context.
        if (!best || text.length > best.text.length) best = {overlay: true, text};
      }
    }
    // Ordinary page controls have no automatic interruption authority.
    return best || {overlay: false, text: ''};
  };
  // Verify that a control currently receives pointer input instead of sitting behind another layer.
  const actionable = element => {
    // Intersect the element with the visible CSS viewport before hit testing.
    const box = element.getBoundingClientRect();
    // A fully off-screen element cannot be the current topmost interruption control.
    if (box.right <= 0 || box.bottom <= 0 || box.left >= innerWidth || box.top >= innerHeight) return false;
    // Choose a point inside both the element and actual viewport.
    const x = Math.max(0, Math.min(innerWidth - 1, box.left + box.width / 2));
    // Use the same center that native input will target.
    const y = Math.max(0, Math.min(innerHeight - 1, box.top + box.height / 2));
    // Shadow roots expose their own hit test; ordinary controls use their owner document.
    const root = element.getRootNode();
    // Resolve the concrete node currently receiving pointer input at that point.
    const hit = typeof root.elementFromPoint === 'function' ? root.elementFromPoint(x, y) : element.ownerDocument.elementFromPoint(x, y);
    // Accept the control itself or one of its rendered children, never a covering ancestor/layer.
    return !!hit && (hit === element || element.contains(hit));
  };
  // Include open shadow roots; inaccessible frames are reported as limitations.
  const roots = [document];
  // Track uninspected interface regions instead of claiming universal coverage.
  const limitations = [];
  // Discover additional accessible roots once per observation.
  for (let index = 0; index < roots.length; index++) {
    // Inspect current descendants, including hosts of open shadow DOM.
    for (const element of roots[index].querySelectorAll('*')) {
      // Preserve open shadow content in the same traversal.
      if (element.shadowRoot) roots.push(element.shadowRoot);
      // Record embedded documents separately until their frame is explicitly collected.
      if (element.tagName === 'IFRAME' && visible(element)) limitations.push('Frame requires separate inspection: ' + (element.src || 'inline frame'));
    }
  }
  // Resolve only unique identities across the accessible roots.
  const find = id => {
    // Give the document scroller an explicit identity.
    if (id === 'window') return document.scrollingElement;
    // Escape the application-generated token as an attribute value.
    const selector = '[data-iba-id=' + JSON.stringify(id) + ']';
    // Search real rendered roots instead of interpreting accessibility refs as DOM attributes.
    const matches = roots.flatMap(root => Array.from(root.querySelectorAll(selector)));
    // Missing or duplicated references require re-observation.
    return matches.length === 1 ? matches[0] : null;
  };
  // Measure actual scroll ranges in the intended container.
  const measure = element => ({id: element === document.scrollingElement ? 'window' : identify(element), top: element.scrollTop, height: element.scrollHeight, viewport: element === document.scrollingElement ? innerHeight : element.clientHeight, bottom: element.scrollTop + (element === document.scrollingElement ? innerHeight : element.clientHeight) >= element.scrollHeight - 2, text: element === document.scrollingElement ? '' : (element.innerText || '').slice(0, 1200)});
  // Resolve one actual target for authorization and effect verification.
  if (request.mode === 'resolve') {
    // A current identity must refer to a visible, unique element.
    const element = find(request.target);
    // Signal staleness instead of clicking a guessed replacement.
    if (!visible(element)) throw new Error('Target is stale, hidden, or ambiguous');
    // Return current properties without exposing password contents.
    return {id: request.target, tag: element.tagName, type: element.type || '', text: element.innerText || element.getAttribute('aria-label') || '', href: element.href || '', value: element.type === 'password' ? '' : element.value || '', disabled: !!element.disabled, expanded: element.getAttribute('aria-expanded'), checked: element.checked};
  }
  // Use the same deterministic measurements across all three browser methods.
  if (['measure', 'reset', 'scroll'].includes(request.mode)) {
    // Resolve the requested panel; never silently fall back to outer-page scrolling.
    const element = find(request.target || 'window');
    // A removed container must be rediscovered.
    if (!element) throw new Error('Scroll container is stale');
    // Restore the document position where this panel had a usable viewport; fixed sidebars may collapse at the footer.
    if (request.mode === 'reset' && element !== document.scrollingElement && state.scrollAnchors?.has(request.target)) window.scrollTo({top:state.scrollAnchors.get(request.target),behavior:'instant'});
    // Bring a nested panel into view before scanning its content.
    if (request.mode === 'reset' && element !== document.scrollingElement) element.scrollIntoView({block: 'center', behavior: 'instant'});
    // Begin complete collection at the top of the relevant region.
    if (request.mode === 'reset') element.scrollTo({top: 0, behavior: 'instant'});
    // Advance till last line of current screen so new screen retains exactly 1 line (~32px) of overlap.
    if (request.mode === 'scroll') element.scrollBy({top: (request.direction === 'up' ? -1 : 1) * Math.max(50, measure(element).viewport - 32), behavior: 'instant'});
    // Return a typed object, not an ambiguously truthy Boolean string.
    return measure(element);
  }
  // Default to the full UI only when the task has not requested a narrower region.
  let scope = document.body;
  // Explicit single-page tasks prefer the actual article/main region over unrelated site navigation.
  if (request.scope === '__iba_page_content__' || ['main','article','[role=main]'].includes(request.scope) && document.querySelectorAll(request.scope).length === 0) {
    // Support semantic landmarks and common actual main-content IDs, including tutorial layouts.
    const candidates = Array.from(document.querySelectorAll('main,[role=main],article,#main,#main-content')).filter(visible);
    // Nested article/main landmarks describe the same region; prefer its unique outermost root.
    const outer = candidates.filter(element => !candidates.some(other => other !== element && other.contains(element)));
    // Ambiguous layouts retain body scope rather than silently choosing an arbitrary article.
    if (outer.length === 1) scope = outer[0];
  }
  // Resolve a uniquely identified extraction region.
  else if (request.scope && request.scope !== 'body') {
    // Support an observed region identity first.
    scope = find(request.scope);
    // CSS region selectors must also resolve uniquely.
    if (!scope) {
      // Search open roots without selecting a convenient first match.
      const matches = roots.flatMap(root => Array.from(root.querySelectorAll(request.scope)));
      // Refuse ambiguous extraction instead of silently omitting other regions.
      if (matches.length !== 1) throw new Error('Extraction region must be unique');
      // Preserve the actual requested region.
      scope = matches[0];
    }
  }
  // Resolve the actual viewport point that receives native wheel input during visible execution.
  if (request.mode === 'scroll_target') {
    // Preserve the exact requested panel; never silently scroll a different region.
    const panel = find(request.target || 'window');
    // Removed panels require fresh observation rather than guessed pointer input.
    if (!panel) throw new Error('Scroll container is stale');
    // For outer scrolling, target requested content instead of a navigation sidebar.
    const box = (panel === document.scrollingElement ? scope : panel).getBoundingClientRect();
    // Intersect source geometry with the actual CSS viewport.
    const left = Math.max(0, box.left), right = Math.min(innerWidth, box.right);
    // Keep the wheel point inside the panel's visible vertical intersection.
    const top = Math.max(0, box.top), bottom = Math.min(innerHeight, box.bottom);
    // A scrolled-past content region may have no intersection at the document footer.
    const usable = right > left && bottom > top;
    // Return CSS coordinates and the exact 1-line overlap distance (viewport - 32px).
    return {x: usable ? left + (right-left)*0.7 : innerWidth*0.7, y:usable ? top+(bottom-top)*0.7 : innerHeight*0.7, delta:Math.max(50,measure(panel).viewport - 32)*(request.direction==='up'?-1:1)};
  }
  // Only requested-scope frame omissions prevent that region's extraction completeness.
  if (request.mode === 'capture') {
    // Do not confuse an unrelated advertising frame with requested article content.
    limitations.length = 0;
    // Canvas-only data cannot be certified as exact DOM source by this collector.
    for (const canvas of scope.querySelectorAll('canvas')) if (visible(canvas)) limitations.push('Canvas content requires verified visual transcription');
    // Record genuinely uninspected embedded content inside the requested region.
    for (const frame of scope.querySelectorAll('iframe')) if (visible(frame)) limitations.push('Frame requires separate inspection: ' + (frame.src || 'inline frame'));
  }
  // Keep navigation targets separate from the complete link frontier.
  const elements = [];
  // Retain every discovered rendered link for bounded relevance review.
  const links = [];
  // Always inspect outer scrolling before nested panel traversal.
  const containers = [measure(document.scrollingElement)];
  // Expose substantial rendered content regions so the planner can isolate a detail pane from a sibling result list.
  const regions = [];
  // Deduplicate candidate regions that are discovered through several descendant controls.
  const regionNodes = new Set();
  // Detail-oriented wording identifies information panels without depending on one website's classes.
  const detailPattern = /\b(description|responsibilities|qualifications|requirements|about|skills|employment type|seniority|show more|read more|details)\b/i;
  // Consider semantic regions and ancestors of controls that reveal or act on detailed information.
  const regionSeeds = roots.flatMap(root => Array.from(root.querySelectorAll('article,main,[role=main],section,button,summary,[role=button]')));
  // Walk bounded ancestry from every useful seed to find a complete panel rather than one label.
  for (const seed of regionSeeds) {
    // Hidden source cannot define a currently observable detail region.
    if (!visible(seed)) continue;
    // Controls without detail context do not need generic ancestor expansion.
    const seedText = seed.innerText || seed.getAttribute?.('aria-label') || '';
    // Semantic regions remain candidates; ordinary controls require detail-related wording nearby.
    const semantic = seed.matches?.('article,main,[role=main],section');
    // Skip unrelated control ancestry to keep the observation compact.
    if (!semantic && !detailPattern.test(seedText + ' ' + (seed.parentElement?.innerText || '').slice(0, 600))) continue;
    // Inspect no more than eight ancestors and never use the whole document as a record region.
    for (let current = seed, depth = 0; current && current !== document.body && current !== document.documentElement && depth < 8; current = current.parentElement, depth++) {
      // Require an actual visible panel-sized box.
      if (!visible(current)) continue;
      // Read rendered text only; generated labels are not extraction source.
      const text = current.innerText || '';
      // Tiny wrappers and page-sized near-duplicates are not useful extraction boundaries.
      const box = current.getBoundingClientRect();
      // Keep substantial bounded regions that contain at least one detail marker.
      if (text.length >= 180 && text.length <= 24000 && box.width >= 240 && box.height >= 120 && detailPattern.test(text)) regionNodes.add(current);
    }
  }
  // Rank richer regions first while keeping a bounded payload for model-independent selection.
  for (const element of Array.from(regionNodes).sort((left, right) => {
    // Count distinct cross-site detail markers before comparing rendered text size.
    const score = value => ((value.innerText || '').match(new RegExp(detailPattern.source, 'ig')) || []).length * 100000 + Math.min((value.innerText || '').length, 24000);
    // Rich complete panels precede narrow description fragments.
    return score(right) - score(left);
  }).slice(0, 24)) {
    // Publish a stable live identity and enough rendered context for deterministic ranking.
    const box = element.getBoundingClientRect();
    // Regions are collection targets, not reconstructed source output.
    regions.push({id: identify(element), text: (element.innerText || '').slice(0, 5000), width: box.width, height: box.height, top: box.top, left: box.left});
  }
  // Inspect actual accessible roots.
  for (const root of roots) {
    // Enumerate semantic controls and relevant role-based controls.
    for (const element of root.querySelectorAll('a,button,input,textarea,select,summary,[role=button],[role=link],[role=tab],[role=checkbox]')) {
      // Keep hidden and zero-area controls out of model targeting.
      if (!visible(element)) continue;
      // Preserve visible labels; fallback labels help targeting but are not extraction text.
      const text = element.innerText || element.getAttribute('aria-label') || element.getAttribute('placeholder') || '';
      // Resolve overlay ancestry once for shared interruption policy metadata.
      const overlay = overlayContext(element);
      // Record actual properties and an identity bound to this node.
      elements.push({id_label: identify(element), text: text.slice(0, 250), aria_label: element.getAttribute('aria-label') || '', title: element.getAttribute('title') || '', context: (element.closest('section,article,li,tr,form,nav')?.innerText || '').slice(0, 350), overlay: overlay.overlay, overlay_context: overlay.text, actionable: actionable(element), in_scope: scope.contains(element) || !!element.getRootNode().host && scope.contains(element.getRootNode().host), in_view: element.getBoundingClientRect().bottom > 0 && element.getBoundingClientRect().top < innerHeight, pagination: !!element.closest('[aria-label*=pagination i],.pagination,[data-pagination]'), dom_id: element.id, role: element.getAttribute('role') || element.tagName.toLowerCase(), tag: element.tagName, type: element.type || '', href: element.href || '', value: element.type === 'password' ? '' : element.value || '', disabled: !!element.disabled || element.getAttribute('aria-disabled') === 'true', expanded: element.tagName === 'SUMMARY' ? String(element.parentElement.open) : element.getAttribute('aria-expanded'), selected: element.getAttribute('aria-selected'), checked: element.checked});
      // Preserve links independently from prompt-sized control lists.
      if (element.href && /^https?:/.test(element.href)) links.push({url: element.href, text, order: links.length});
    }
    // Discover scroll panels inside the requested content scope.
    for (const element of root.querySelectorAll('*')) {
      // Ignore invisible or unrelated panels.
      if (!visible(element) || !(scope.contains(element) || element === scope)) continue;
      // Distinguish actual scrolling from decorative overflow.
      const style = element.ownerDocument.defaultView.getComputedStyle(element);
      // Require a real viewport and scroll range.
      if (/(auto|scroll)/.test(style.overflowY) && element.scrollHeight > element.clientHeight + 2 && element.clientHeight > 40) {
        // Remember the first usable outer position rather than a later footer-collapsed layout.
        state.scrollAnchors ||= new Map();
        // Bind restoration to this concrete observed panel, preserving its actual identity.
        const id = identify(element);
        // Only the initial usable context should define this panel's traversal origin.
        if (!state.scrollAnchors.has(id)) state.scrollAnchors.set(id, scrollY);
        // Keep typed geometry for real end checks.
        containers.push(measure(element));
      }
    }
  }
  // Capture blocks independently of the bounded text sent to the model.
  const blocks = [];
  // Preserve the current heading hierarchy in structural metadata.
  const headings = [];
  // Store exact text and source position without trimming indentation.
  const add = (element, kind, text, extra = {}) => {
    // Exclude empty layout whitespace without modifying meaningful block text.
    if (!text || !text.trim()) return;
    // Read the rendered source position.
    const box = element.getBoundingClientRect();
    // Account for a nested container's scroll offset.
    const panel = request.container && request.container !== 'window' ? find(request.container) : null;
    // Preserve absolute content coordinates as virtualized rows are recycled.
    const y = box.top + scrollY + (panel && panel.contains(element) ? panel.scrollTop : 0);
    // Prefer explicit logical row identifiers over recycled DOM identity.
    const logical = element.getAttribute('aria-rowindex') || element.getAttribute('data-index');
    // Resolve the nearest entity/card independently from viewport overlap.
    const entity = entityContext(element);
    // Recreated virtualized rows and ordinary DOM nodes retain structural identity across scrolling.
    const record = logical ? entity.key + ':logical:' + logical : entity.key + ':' + structuralPath(element);
    // Identify global chrome whose viewport position changes while the document scrolls.
    const position = getComputedStyle(element).position;
    // Retain relationships and exact content for deterministic output.
    blocks.push({key: record, stable_path: structuralPath(element), entity_key: entity.key, entity_url: entity.url, persistent: position === 'sticky' || position === 'fixed', kind, text, y, x: box.left + scrollX, headings: [...headings].filter(Boolean), ...extra});
  };
  // Walk rendered semantic blocks, avoiding parent/child duplicate transcripts.
  const walk = element => {
    // Scripts, hidden content, and the indicator are not displayed source information.
    if (!visible(element) || /^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE)$/.test(element.tagName)) return;
    // Retain preceding offscreen headings as context for later viewport captures.
    if (/^H[1-6]$/.test(element.tagName)) {
      // Replace only this heading level and its descendants.
      headings.length = Number(element.tagName[1]) - 1;
      // Preserve the source wording in the structural path.
      headings.push(element.innerText);
    }
    // Read the current viewport position.
    const box = element.getBoundingClientRect();
    // Clip collection to the selected nested viewport when appropriate.
    const panel = request.container && request.container !== 'window' ? find(request.container) : null;
    // Preserve only content visible through the current scroll container.
    const clip = panel ? panel.getBoundingClientRect() : {top: 0, bottom: innerHeight};
    // Respect every clipping ancestor, not just the outer viewport.
    let clipTop = Math.max(0, clip.top), clipBottom = Math.min(innerHeight, clip.bottom);
    // Nested overflow can hide rows even when their geometry lies inside the window.
    for (let parent = element.parentElement; parent; parent = parent.parentElement) {
      // Check the actual ancestor's clipping policy.
      const overflow = getComputedStyle(parent).overflowY;
      // Intersect with real scroll/hidden ancestor viewports.
      if (/(auto|scroll|hidden|clip)/.test(overflow)) {
        // Read the clipping box without moving another element.
        const bounds = parent.getBoundingClientRect();
        // Keep only the visible intersection of all ancestor containers.
        clipTop = Math.max(clipTop, bounds.top);
        // Preserve the lower clipping boundary independently.
        clipBottom = Math.min(clipBottom, bounds.bottom);
      }
    }
    // Skip offscreen children while allowing tall parents to expose visible descendants.
    if (box.bottom <= clipTop || box.top >= clipBottom) return;
    // Capture headings with their original wording and hierarchy.
    if (/^H[1-6]$/.test(element.tagName)) {
      // Preserve this source block separately from its context metadata.
      add(element, 'heading', element.innerText, {level: Number(element.tagName[1])});
      // Do not duplicate the heading's child text.
      return;
    }
    // Preserve code as one exact preformatted block.
    if (element.tagName === 'PRE' || element.matches('.w3-code,.code-block,[role=code]')) {
      // Keep indentation and line breaks exactly as rendered.
      add(element, 'code', element.innerText);
      // Avoid duplicating syntax-highlighting spans.
      return;
    }
    // Capture tables row-by-row so virtualized data survives DOM replacement.
    if (element.tagName === 'TR' || element.getAttribute('role') === 'row') {
      // Preserve cell boundaries, headings, and spanning relationships.
      const cells = Array.from(element.querySelectorAll(':scope > th,:scope > td,:scope > [role=cell],:scope > [role=columnheader]')).map(cell => ({text: cell.innerText, header: cell.tagName === 'TH', colspan: cell.colSpan || 1, rowspan: cell.rowSpan || 1}));
      // Record rows with actual visible cells.
      if (cells.length) {
        // Link rows to their source table without inventing labels or values.
        add(element, 'table_row', element.innerText, {cells, table: identify(element.closest('table,[role=grid],[role=table]') || element.parentElement)});
        // Child cells are already represented exactly.
        return;
      }
    }
    // Semantic prose retains its full internal whitespace and wording.
    if (/^(P|LI|DT|DD|BLOCKQUOTE|SUMMARY)$/.test(element.tagName)) {
      // Record source text without turning a paragraph into a generated summary.
      add(element, element.tagName.toLowerCase(), element.innerText);
      // Avoid capturing embedded labels twice.
      return;
    }
    // Preserve one rendered inline run instead of inserting artificial newlines between syntax spans.
    const inlineChildren = Array.from(element.children).filter(visible);
    // Shadow content needs its separate accessible-root traversal below.
    if (!element.shadowRoot && element.innerText?.trim() && inlineChildren.every(child => child.tagName === 'BR' || /^(inline|contents)/.test(getComputedStyle(child).display))) {
      // innerText retains browser-rendered spacing and line breaks across adjacent inline nodes.
      add(element, 'text', element.innerText);
      // Descendant spans are already represented in this exact rendered run.
      return;
    }
    // Capture generic layouts without requiring semantic article markup.
    for (const node of element.childNodes) {
      // Recurse into visible child elements.
      if (node.nodeType === Node.ELEMENT_NODE) walk(node);
      // Preserve meaningful direct text nodes in generic cards and panels.
      else if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) add(element, 'text', node.textContent, {key: identify(element) + ':text:' + Array.from(element.childNodes).indexOf(node) + ':' + Math.round(box.top + scrollY)});
    }
    // Include rendered open-shadow children in their host's source order.
    if (element.shadowRoot) for (const child of element.shadowRoot.children) walk(child);
  };
  // Observation-only calls avoid collecting the full block tree unnecessarily.
  if (request.mode === 'capture') walk(scope);
  // Identify visible busy indicators instead of assuming a fixed sleep completes loading.
  const loading = Array.from(scope.querySelectorAll('[aria-busy=true],[role=progressbar],.loading,.spinner')).some(visible);
  // Return explicit typed state for all browser transports.
  return {url: location.href, title: document.title, text: document.body.innerText, view_state: elements.filter(item => item.selected === 'true').map(item => item.text).concat(Array.from(scope.querySelectorAll('[aria-current=page]')).map(item => item.innerText)), elements, links, containers, regions, blocks, loading, limitations, viewport: {width: innerWidth, height: innerHeight, dpr: devicePixelRatio}};
}
