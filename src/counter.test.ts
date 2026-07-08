import { describe, it, expect } from 'vitest'
import { increment, decrement } from './counter'

describe('increment', () => {
  it('0 から 1 に増える', () => {
    expect(increment(0)).toBe(1)
  })

  it('任意の値から 1 増える', () => {
    expect(increment(5)).toBe(6)
  })
})

describe('decrement', () => {
  it('1 から 0 に減る', () => {
    expect(decrement(1)).toBe(0)
  })

  it('任意の値から 1 減る', () => {
    expect(decrement(5)).toBe(4)
  })

  it('負の値にもなれる', () => {
    expect(decrement(0)).toBe(-1)
  })
})
