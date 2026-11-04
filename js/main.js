/* ============================================================
   Sunny Smile Trading PLC — main.js
   Handles: nav, scroll effects, reveal animations, portfolio
   filtering, counters, skill bars, and demo form handling.
   ============================================================ */

(function () {
  "use strict";

  /* ---------- Header scroll state ---------- */
  const header = document.querySelector(".site-header");
  const onScroll = () => {
    if (header) header.classList.toggle("scrolled", window.scrollY > 12);
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- Mobile navigation ---------- */
  const toggle = document.querySelector(".nav-toggle");
  const scrim = document.querySelector(".nav-scrim");

  const closeNav = () => {
    document.body.classList.remove("nav-open");
    if (toggle) toggle.classList.remove("open");
    if (scrim) scrim.classList.remove("show");
  };

  if (toggle) {
    toggle.addEventListener("click", () => {
      const open = document.body.classList.toggle("nav-open");
      toggle.classList.toggle("open", open);
      if (scrim) scrim.classList.toggle("show", open);
    });
  }
  if (scrim) scrim.addEventListener("click", closeNav);
  document.querySelectorAll(".nav-links a").forEach((a) => a.addEventListener("click", closeNav));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeNav();
  });

  /* ---------- Highlight current page in nav ---------- */
  const path = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  document.querySelectorAll(".nav-links a[data-page]").forEach((a) => {
    if (a.dataset.page.toLowerCase() === path) a.classList.add("active");
  });

  /* ---------- Reveal on scroll ---------- */
  const revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    revealEls.forEach((el, i) => {
      el.style.setProperty("--delay", `${(i % 4) * 0.08}s`);
      io.observe(el);
    });
  } else {
    revealEls.forEach((el) => el.classList.add("visible"));
  }

  /* ---------- Animated counters ---------- */
  const counters = document.querySelectorAll("[data-count]");
  if (counters.length && "IntersectionObserver" in window) {
    const cio = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const el = entry.target;
          const target = parseFloat(el.dataset.count);
          const suffix = el.dataset.suffix || "";
          const decimals = el.dataset.decimals ? parseInt(el.dataset.decimals, 10) : 0;
          const duration = 1400;
          const start = performance.now();

          const tick = (now) => {
            const p = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - p, 3);
            el.textContent = (target * eased).toFixed(decimals) + suffix;
            if (p < 1) requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
          cio.unobserve(el);
        });
      },
      { threshold: 0.5 }
    );
    counters.forEach((el) => cio.observe(el));
  }

  /* ---------- Skill bars ---------- */
  const skills = document.querySelectorAll(".skill-bar i[data-level]");
  if (skills.length && "IntersectionObserver" in window) {
    const sio = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.style.width = entry.target.dataset.level + "%";
            sio.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.4 }
    );
    skills.forEach((el) => sio.observe(el));
  } else {
    skills.forEach((el) => (el.style.width = el.dataset.level + "%"));
  }

  /* ---------- Portfolio filtering ---------- */
  const filterBar = document.querySelector(".filter-bar");
  if (filterBar) {
    const items = document.querySelectorAll(".work-item");
    filterBar.addEventListener("click", (e) => {
      const btn = e.target.closest(".pill");
      if (!btn) return;

      filterBar.querySelectorAll(".pill").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");

      const filter = btn.dataset.filter;
      items.forEach((item) => {
        const show = filter === "all" || item.dataset.category === filter;
        item.classList.toggle("hidden", !show);
        if (show) {
          item.style.animation = "none";
          void item.offsetWidth;
          item.style.animation = "fadeUp 0.45s cubic-bezier(0.22,1,0.36,1) both";
        }
      });

      const url = new URL(location.href);
      if (filter === "all") url.searchParams.delete("category");
      else url.searchParams.set("category", filter);
      history.replaceState(null, "", url);
    });

    const params = new URLSearchParams(location.search);
    const initial = params.get("category");
    if (initial) {
      const target = filterBar.querySelector(`.pill[data-filter="${initial}"]`);
      if (target) target.click();
    }
  }

  const style = document.createElement("style");
  style.textContent =
    "@keyframes fadeUp{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}";
  document.head.appendChild(style);

  /* ---------- Toast helper ---------- */
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.setAttribute("role", "status");
  document.body.appendChild(toast);

  let toastTimer;
  function showToast(message) {
    toast.textContent = message;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 4200);
  }

  /* ---------- Form validation helper ---------- */
  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const PHONE_RE = /^[+()\-\s\d]{7,20}$/;

  function validateField(input) {
    const field = input.closest(".field");
    if (!field) return true;

    const value = input.value.trim();
    let valid = true;

    if (input.required && !value) valid = false;
    if (valid && input.type === "email" && value && !EMAIL_RE.test(value)) valid = false;
    if (valid && input.type === "tel" && value && !PHONE_RE.test(value)) valid = false;

    field.classList.toggle("error", !valid);
    return valid;
  }

  /* ---------- Forms (demo submit — wire to your backend/Formspree) ---------- */
  document.querySelectorAll("form[data-demo-form]").forEach((form) => {
    form.setAttribute("novalidate", "");

    form.querySelectorAll("input, select, textarea").forEach((input) => {
      input.addEventListener("blur", () => validateField(input));
      input.addEventListener("input", () => {
        const field = input.closest(".field");
        if (field && field.classList.contains("error")) validateField(input);
      });
    });

    form.addEventListener("submit", (e) => {
      e.preventDefault();

      let firstInvalid = null;
      form.querySelectorAll("input, select, textarea").forEach((input) => {
        if (!validateField(input) && !firstInvalid) firstInvalid = input;
      });

      if (firstInvalid) {
        firstInvalid.focus();
        showToast("Please check the highlighted fields and try again.");
        return;
      }

      const btn = form.querySelector('button[type="submit"]');
      const original = btn ? btn.textContent : "";
      if (btn) {
        btn.disabled = true;
        btn.textContent = "Sending…";
      }

      setTimeout(() => {
        form.reset();
        if (btn) {
          btn.disabled = false;
          btn.textContent = original;
        }
        showToast(form.dataset.successMessage || "Thank you! Your message has been sent.");
      }, 900);
    });
  });

  /* ---------- Floating WhatsApp button ---------- */
  const WA_NUMBER = "251940088463";
  document.querySelectorAll("[data-wa]").forEach((el) => {
    const msg = encodeURIComponent(el.dataset.wa || "Hi! I found you online and I'd like a design quote.");
    el.href = `https://wa.me/${WA_NUMBER}?text=${msg}`;
    el.target = "_blank";
    el.rel = "noopener";
  });

  /* ---------- Footer year ---------- */
  document.querySelectorAll("[data-year]").forEach((el) => {
    el.textContent = new Date().getFullYear();
  });
})();
