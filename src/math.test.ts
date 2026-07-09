import { describe, it, expect } from 'vitest'
import { multiply, add } from './math'

describe('multiply', () => {
  it('multiplies two positive numbers', () => {
    expect(multiply(3, 4)).toBe(12)
  })

  it('multiplies by zero', () => {
    expect(multiply(5, 0)).toBe(0)
  })

  it('multiplies negative numbers', () => {
    expect(multiply(-2, 3)).toBe(-6)
  })
})

describe('add', () => {
  it('adds two numbers', () => {
    expect(add(2, 3)).toBe(5)
  })
})
