
// utils/debounce.ts
export function debounce<T extends (...args: any[]) => void>(// eslint-disable-line @typescript-eslint/no-explicit-any
  func: T,
  delay = 200
) {
  let timer: ReturnType<typeof setTimeout> | null = null;

  const debounced = (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      func(...args);
    }, delay);
  };

  debounced.cancel = () => {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  };

  return debounced as T & { cancel: () => void };
}
