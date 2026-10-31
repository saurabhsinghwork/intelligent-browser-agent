// Batch readiness inspection inside the selected browser to avoid repeated CLI/RPC startup.
async (inspect, request) => {
  // Use a longer grace interval only at an apparent bottom where delayed growth matters.
  const quiet = request.bottom ? 1000 : 120;
  // Bound this readiness operation without limiting the overall task duration.
  const deadline = performance.now() + 10000;
  // Retain the last actual rendered-source signature.
  let previous = '', stableSince = performance.now();
  // Observe until source and loader state establish readiness.
  while (performance.now() < deadline) {
    // Capture before virtualized elements can be discarded by another scroll.
    const capture = inspect({mode: 'capture', scope: request.scope, container: request.container});
    // Read measurements locally rather than another transport round trip.
    const metrics = inspect({mode: 'measure', target: request.container});
    // Compare actual source identities, values, position, and size.
    const signature = JSON.stringify([metrics.height, metrics.top, capture.blocks.map(block => [block.key, block.text])]);
    // DOM growth or changed records restart the quiet interval.
    if (signature !== previous) {
      // Keep the last meaningful state.
      previous = signature;
      // Require stability after each actual source change.
      stableSince = performance.now();
    }
    // A live loader is never mistaken for complete content.
    if (!capture.loading && performance.now() - stableSince >= quiet) return {capture, metrics};
    // A short browser timer allows real rendering/lazy-load callbacks to execute.
    await new Promise(resolve => setTimeout(resolve, 40));
  }
  // Do not silently treat a still-busy region as complete.
  throw new Error('Relevant content did not settle before its operation deadline');
}
