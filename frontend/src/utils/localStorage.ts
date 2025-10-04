export type NumberKeys = `room:${number}:last_seq`

export function getNumberFromLocalStorage(
  key: NumberKeys,
  defaultValue: number | null,
): number | null {
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

export function setNumberToLocalStorage(key: NumberKeys, value: number): void {
  localStorage.setItem(key, String(value))
}
