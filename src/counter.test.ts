import { describe, it, expect } from 'vitest'
import { increment, decrement, multiply } from './counter'

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

describe('multiply', () => {
  it('0 に何を掛けても 0 になる', () => {
    expect(multiply(0, 5)).toBe(0)
  })

  it('任意の値に 1 を掛けると変わらない', () => {
    expect(multiply(5, 1)).toBe(5)
  })

  it('任意の値に倍数を掛けた結果を返す', () => {
    expect(multiply(3, 4)).toBe(12)
  })

  it('負の倍数を掛けると符号が反転する', () => {
    expect(multiply(5, -2)).toBe(-10)
  })
})
