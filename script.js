const reveals = document.querySelectorAll(".reveal");
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) entry.target.classList.add("visible");
  });
}, { threshold: 0.12 });
reveals.forEach(item => observer.observe(item));

document.querySelectorAll('a[href^="#"]').forEach(link => {
  link.addEventListener("click", event => {
    const target = document.querySelector(link.getAttribute("href"));
    if (!target) return;
    event.preventDefault();
    target.scrollIntoView({ behavior: "smooth" });
    const counters = document.querySelectorAll(".counter");

counters.forEach(counter => {

  const updateCounter = () => {

    const target = +counter.getAttribute("data-target");

    const current = +counter.innerText;

    const increment = target / 60;

    if (current < target) {

      counter.innerText =
        Math.ceil(current + increment);

      setTimeout(updateCounter, 30);

    } else {

      counter.innerText = target;
    }
  };

  updateCounter();
});
  });
});
