import { useMemo, useSyncExternalStore } from "react";

export function useMediaQuery(query: string): boolean {
  // Based on @eps1lon's example at
  // https://github.com/reactwg/react-18/discussions/86#discussioncomment-1435358

  const [getSnapshot, subscribe] = useMemo(() => {
    const mediaQueryList = window.matchMedia(query);

    return [
      () => mediaQueryList.matches,
      (notify: () => void) => {
        if (mediaQueryList.addEventListener) {
          mediaQueryList.addEventListener("change", notify);
          return () => mediaQueryList.removeEventListener("change", notify);
        } else {
          // For Safari <= 13.1 (2020)
          mediaQueryList.addListener(notify);
          return () => mediaQueryList.removeListener(notify);
        }
      },
    ];
  }, [query]);

  return useSyncExternalStore(subscribe, getSnapshot);
}

export enum ScreenSize {
  XS = 1,
  SM,
  MD,
  LG,
}

export function useScreenSize(): ScreenSize {
  // This should be kept in sync with Bootstrap media queries. See
  // _variables.scss and _responsive-utilities.scss.
  const atLeastLG = useMediaQuery("(min-width: 1200px)");
  const atLeastMD = useMediaQuery("(min-width: 992px)");
  const atLeastSM = useMediaQuery("(min-width: 768px)");
  if (atLeastLG) return ScreenSize.LG;
  if (atLeastMD) return ScreenSize.MD;
  if (atLeastSM) return ScreenSize.SM;
  return ScreenSize.XS;
}

export const underXS = (size: ScreenSize) => size <= ScreenSize.XS;
export const underSM = (size: ScreenSize) => size <= ScreenSize.SM;
export const underMD = (size: ScreenSize) => size <= ScreenSize.MD;
