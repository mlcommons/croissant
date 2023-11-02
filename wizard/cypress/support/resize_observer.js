Cypress.Commands.add("ignore_resize_observer", () => {
    const resizeObserverLoopErrRe = /ResizeObserver loop limit exceeded/

    // consensus was that this exception didn't matter mostly, and was intermittent when running tests.
    // https://stackoverflow.com/questions/63653605/resizeobserver-loop-limit-exceeded-api-is-never-used
    Cypress.on('uncaught:exception', err => {
      if (resizeObserverLoopErrRe.test(err.message)) {
        return false
      }
    })
})