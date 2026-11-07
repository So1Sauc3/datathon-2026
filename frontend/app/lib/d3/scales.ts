import { scaleBand, scaleLinear, scaleTime } from 'd3'

export function linearScale(
  domain: [number, number],
  length: number,
  options?: { vertical?: boolean },
) {
  const range: [number, number] = options?.vertical ? [length, 0] : [0, length]
  return scaleLinear().domain(domain).range(range)
}

export function bandScale(
  domain: Iterable<string>,
  length: number,
  padding = 0.1,
) {
  return scaleBand<string>().domain(domain).range([0, length]).padding(padding)
}

export function timeScale(domain: [Date, Date], length: number) {
  return scaleTime().domain(domain).range([0, length])
}
