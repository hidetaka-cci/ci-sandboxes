import { describe, it, expect } from 'vitest'

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

describe('slow suite', () => {
  it('runs for about nine seconds', async () => {
    await sleep(9000)
    expect(true).toBe(true)
  }, 15000)
})
