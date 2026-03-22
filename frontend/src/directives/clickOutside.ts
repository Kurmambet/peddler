// frontend/src/directives/clickOutside.ts

import type { Directive, DirectiveBinding } from "vue";

interface ClickOutsideElement extends HTMLElement {
  _clickOutsideHandler?: (event: MouseEvent) => void;
}

export const vClickOutside: Directive = {
  mounted(el: ClickOutsideElement, binding: DirectiveBinding) {
    el._clickOutsideHandler = (event: MouseEvent) => {
      const target = event.target as Node;
      if (!(el === target || el.contains(target))) {
        binding.value(event);
      }
    };
    // Небольшая задержка, чтобы не сработало сразу при открытии
    setTimeout(() => {
      document.addEventListener("click", el._clickOutsideHandler!);
    }, 0);
  },

  unmounted(el: ClickOutsideElement) {
    if (el._clickOutsideHandler) {
      document.removeEventListener("click", el._clickOutsideHandler);
    }
  },
};
