import { useEffect } from "react";

export default function Root({ children }) {
  useEffect(() => {
    const html = document.documentElement;

    const syncScrollState = () => {
      if (window.scrollY > 8) {
        html.setAttribute("data-nav-scrolled", "true");
      } else {
        html.setAttribute("data-nav-scrolled", "false");
      }
    };

    syncScrollState();
    window.addEventListener("scroll", syncScrollState, { passive: true });

    return () => {
      window.removeEventListener("scroll", syncScrollState);
    };
  }, []);

  return children;
}
