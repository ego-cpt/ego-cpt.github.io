/* Small, dependency-free interactions; no analytics or third-party scripts. */
"use strict";

document.querySelectorAll(".image-comparison input").forEach((slider) => {
  slider.addEventListener("input", () => {
    slider.closest(".image-comparison").style.setProperty("--split", `${slider.value}%`);
    slider.setAttribute("aria-valuetext", `${slider.value} percent vanilla retargeting, ${100 - Number(slider.value)} percent EgoCPT`);
  });
});

const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const videos = [...document.querySelectorAll(".auto-video")];
const visible = new Set();
const userPaused = new WeakSet();
const programPaused = new WeakSet();

function loadVideo(video) {
  const source = video.querySelector("source[data-src]");
  if (source) {
    source.src = source.dataset.src;
    source.removeAttribute("data-src");
    video.load();
  }
}

function pauseVideo(video) {
  if (!video.paused) {
    programPaused.add(video);
    video.pause();
  }
}

function updateVideo(video) {
  if (visible.has(video) && !document.hidden) {
    loadVideo(video);
    if (!reducedMotion.matches && !userPaused.has(video)) {
      video.play().catch(() => { /* Native controls remain available. */ });
    }
  } else {
    pauseVideo(video);
  }
}

videos.forEach((video) => {
  // Let the observer manage playback, including reduced-motion preferences.
  video.autoplay = false;
  if (reducedMotion.matches) pauseVideo(video);
  video.addEventListener("pause", () => {
    if (programPaused.has(video)) programPaused.delete(video);
    else if (!video.ended) userPaused.add(video);
  });
  video.addEventListener("play", () => userPaused.delete(video));
});

if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(({target, isIntersecting}) => {
      if (isIntersecting) visible.add(target);
      else visible.delete(target);
      updateVideo(target);
    });
  }, { threshold: 0.15 });
  videos.forEach((video) => observer.observe(video));
} else {
  videos.forEach((video) => { loadVideo(video); video.controls = true; });
}

document.addEventListener("visibilitychange", () => videos.forEach(updateVideo));
reducedMotion.addEventListener("change", () => {
  videos.forEach((video) => {
    if (reducedMotion.matches) pauseVideo(video);
    else updateVideo(video);
  });
});

document.getElementById("copy-bibtex").addEventListener("click", async () => {
  const code = document.getElementById("bibtex-code");
  const status = document.getElementById("copy-status");
  try {
    if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable");
    await navigator.clipboard.writeText(code.textContent);
    status.textContent = "Citation copied.";
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(code);
    selection.removeAllRanges();
    selection.addRange(range);
    status.textContent = "Citation selected. Press Ctrl+C or ⌘C to copy.";
  }
});
