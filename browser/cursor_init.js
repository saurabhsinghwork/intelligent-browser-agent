// Show a red Windows-style arrow driven only by genuine browser mouse events.
() => {
  // Render the application pointer only in the top-level browsing document.
  if (window.top !== window.self) {
    // Remove an indicator left by an older script when an existing frame is upgraded.
    const embeddedCursor = document.getElementById('iba-cursor');
    // Keep frame content clean because the top-level pointer already represents native input.
    if (embeddedCursor) embeddedCursor.remove();
    // Do not register pointer listeners or create a second visible arrow in this frame.
    return false;
  }
  // Install the passive arrow once the new document exposes its root element.
  const install = () => {
    // Preserve one current arrow; replace an older circular indicator when upgrading a live page.
    const previous = document.getElementById('iba-cursor');
    // Idempotent observation must ensure visibility without duplicate pointer listeners.
    if (previous?.dataset.version === 'red-arrow-v3') {
      previous.style.display = 'block';
      previous.style.visibility = 'visible';
      return false;
    }
    // Remove only this application's obsolete visual indicator.
    if (previous) previous.remove();
    // Create an inert overlay without source text or a hit-testing surface.
    const cursor = document.createElement('div');
    // Keep the existing exclusion identity used by rendered-source extraction.
    cursor.id = 'iba-cursor';
    // Distinguish document-start persistence from the previous observation-only arrow.
    cursor.dataset.version = 'red-arrow-v3';
    // Accessibility tools must not mistake the visual indicator for website content.
    cursor.setAttribute('aria-hidden', 'true');
    // Start at the real initial browser-input position used immediately after navigation.
    const initial = window.__ibaPointer || {x: Math.round((innerWidth || 1280) / 2), y: Math.round((innerHeight || 800) / 2)};
    // Preserve the initial point for the first visible native trajectory on this document.
    window.__ibaPointer = initial;
    // Place the arrow's top-left hotspot exactly at the current CSS browser pointer position.
    cursor.style.cssText = 'position:fixed !important;width:24px !important;height:32px !important;pointer-events:none !important;z-index:2147483647 !important;left:' + initial.x + 'px;top:' + initial.y + 'px;display:block !important;visibility:visible !important;margin:0 !important;transform:none !important;filter:drop-shadow(1px 1px 1px rgba(0,0,0,.55));';
    // Use a Windows-style arrow silhouette with a red fill and contrasting outline.
    cursor.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="32" viewBox="0 0 24 32" aria-hidden="true"><path d="M1 1 L1 24 L7.5 18 L12.5 29 L17.5 26.7 L12.5 16.8 L22 16.8 Z" fill="#ef2028" stroke="#ffffff" stroke-width="1.4" stroke-linejoin="round"/></svg>';
    // Attach without modifying website controls, layout, or the operating-system pointer.
    document.documentElement.appendChild(cursor);
    // Add CSS keyframe animation for prominent click ripple effect if not already injected.
    if (!document.getElementById('iba-cursor-styles')) {
      const styleEl = document.createElement('style');
      styleEl.id = 'iba-cursor-styles';
      styleEl.textContent = '@keyframes iba-pulse { 0% { transform: scale(0.6); opacity: 1; } 100% { transform: scale(2.4); opacity: 0; } }';
      document.head ? document.head.appendChild(styleEl) : document.documentElement.appendChild(styleEl);
    }
    // Expose visible click indicator helper.
    window.__ibaShowClickEffect = (x, y) => {
      const ripple = document.createElement('div');
      ripple.className = 'iba-click-ripple';
      ripple.style.cssText = 'position:fixed;width:26px;height:26px;border-radius:50%;border:2px solid #ef2028;background:rgba(239,32,40,0.35);pointer-events:none;z-index:2147483647;left:' + (x - 13) + 'px;top:' + (y - 13) + 'px;animation:iba-pulse 0.4s ease-out forwards;';
      document.documentElement.appendChild(ripple);
      setTimeout(() => ripple.remove(), 450);
    };
    // Remove only a listener previously installed by this same arrow implementation.
    if (window.__ibaPointerListener) {
      document.removeEventListener('mousemove', window.__ibaPointerListener, true);
      document.removeEventListener('mousedown', window.__ibaPointerListener, true);
    }
    // One native event drives both the visible arrow and the recorded trajectory origin.
    window.__ibaPointerListener = event => {
      // Preserve the actual native input position, independent of the overlay's shape.
      window.__ibaPointer = {x:event.clientX,y:event.clientY};
      // The arrow tip is the click hotspot; no circle-center correction is applied.
      cursor.style.left = event.clientX + 'px';
      // Match actual CSS viewport coordinates without screenshot scaling assumptions.
      cursor.style.top = event.clientY + 'px';
      // Show subtle feedback on mouse down.
      if (event.type === 'mousedown' && window.__ibaShowClickEffect) {
        window.__ibaShowClickEffect(event.clientX, event.clientY);
      }
    };
    // Listen to mousemove and mousedown for instant cursor synchronization.
    document.addEventListener('mousemove', window.__ibaPointerListener, true);
    document.addEventListener('mousedown', window.__ibaPointerListener, true);
    // Report that this document received a new cursor instance.
    return true;
  };
  // Document-start scripts may run before the root element exists.
  if (!document.documentElement) {
    // Install at the earliest safe lifecycle event without waiting for images or analytics.
    document.addEventListener('DOMContentLoaded', install, {once:true});
    // Report scheduled installation so the adapter can still dispatch native input.
    return true;
  }
  // Install immediately in already-created documents and observation recovery paths.
  return install();
}
