"use strict";
const menuButton = document.querySelector(".menu-toggle");
const navigation = document.getElementById("navigation");
if (menuButton && navigation) {
  const closeMenu = () => {
    menuButton.setAttribute("aria-expanded", "false");
    navigation.classList.remove("is-open");
  };
  menuButton.addEventListener("click", () => {
    const isOpen = menuButton.getAttribute("aria-expanded") === "true";
    menuButton.setAttribute("aria-expanded", String(!isOpen));
    navigation.classList.toggle("is-open", !isOpen);
  });
  navigation.querySelectorAll("a").forEach(link => link.addEventListener("click", closeMenu));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && menuButton.getAttribute("aria-expanded") === "true") {
      closeMenu();
      menuButton.focus();
    }
  });
  window.matchMedia("(min-width: 761px)").addEventListener("change", event => {
    if (event.matches) closeMenu();
  });
}
