export type NumberKeys = `room:${number}:last_seq`

export const getNumberFromLocalStorage: (
  key: NumberKeys,
  defaultValue: number | null,
) => number | null = (key, defaultValue) => {
  const value = localStorage.getItem(key)
  if (value === null) {
    return defaultValue
  }
  const n = Number(value)
  if (Number.isNaN(n)) {
    return defaultValue
  }
  return n
}
