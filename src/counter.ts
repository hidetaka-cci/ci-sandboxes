export function increment(count: number): number {
  return count + 1
}

export function decrement(count: number): number {
  return count - 1
}

export function setupCounter(incrementEl: HTMLButtonElement, decrementEl: HTMLButtonElement, displayEl: HTMLElement) {
  let counter = 0
  const render = () => {
    displayEl.textContent = `count is ${counter}`
  }
  incrementEl.addEventListener('click', () => {
    counter = increment(counter)
    render()
  })
  decrementEl.addEventListener('click', () => {
    counter = decrement(counter)
    render()
  })
  render()
}
