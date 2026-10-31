// Capture several finite viewports through one CLI process or MCP request.
async (page, request, inspectSource, settleSource) => {
  // Evaluate only version-controlled inspection source with JSON-encoded arguments.
  const probe = async arguments => await page.evaluate('(' + inspectSource + ')(' + JSON.stringify(arguments) + ')');
  // Run the shared readiness function entirely inside the current page.
  const stable = async arguments => await page.evaluate('(' + settleSource + ')((' + inspectSource + '),' + JSON.stringify(arguments) + ')');
  // Preserve ordered source, geometry, and screenshot evidence for Python consumption.
  const views = [];
  // Keep one command bounded so Stop and progress publication remain responsive.
  for (let index = 0; index < request.batchSize; index++) {
    // The first cached viewport advances only when the Python collector requested movement.
    const shouldAdvance = request.advance || index > 0;
    // Move after the previous viewport has already been captured.
    if (shouldAdvance) {
      // Visible execution must use genuine pointer and wheel input.
      if (request.headful) {
        // Resolve a point inside the exact requested content panel.
        const point = await probe({mode:'scroll_target',scope:request.scope,target:request.container,direction:'down'});
        // Measure before input so an intercepted wheel can be detected.
        const before = await probe({mode:'measure',target:request.container});
        // Move the real browser pointer along a short visible trajectory.
        await page.mouse.move(point.x,point.y,{steps:4});
        // Send the wheel event to that same concrete panel location.
        await page.mouse.wheel(0,point.delta);
        // Allow Chrome to commit asynchronous native scrolling.
        await page.waitForTimeout(120);
        // Measure the requested panel rather than trusting event dispatch.
        const after = await probe({mode:'measure',target:request.container});
        // Recover only a wheel consumed by an overlay or scroll latch.
        if (after.top === before.top && !after.bottom) await probe({mode:'scroll',target:request.container,direction:'down'});
      }
      // Headless execution needs no visible animation.
      else {
        // Advance deterministically by the same overlapping viewport distance.
        await probe({mode:'scroll',target:request.container,direction:'down'});
      }
    }
    // Capture rendered source after the normal quiet interval.
    let result = await stable({scope:request.scope,container:request.container,bottom:false});
    // Track whether the measured end also survives delayed-growth verification.
    let stableBottom = false;
    // An apparent bottom receives the longer lazy-content grace interval.
    if (result.metrics.bottom) {
      // Recheck source and height after delayed loaders have had time to run.
      const finalResult = await stable({scope:request.scope,container:request.container,bottom:true});
      // A finite end requires the same height and a real bottom after that grace interval.
      stableBottom = finalResult.metrics.bottom && finalResult.metrics.height === result.metrics.height;
      // Preserve content revealed during the final grace interval.
      result = finalResult;
    }
    // Save the exact viewport corresponding to this source capture.
    await page.screenshot({path:request.paths[index],fullPage:false,scale:'css'});
    // Tell Python that this screenshot followed the full delayed-growth bottom check.
    result.capture.stable_bottom = stableBottom;
    // Bind the immutable image to its matching structured capture.
    result.capture.screenshot_path = request.paths[index];
    // Retain typed evidence in actual traversal order.
    views.push(result);
    // Stop batching once a verified finite bottom is reached.
    if (stableBottom) break;
  }
  // Return source data only; task completion remains a Python evidence decision.
  return {views};
}
