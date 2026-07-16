// Dark / light mode toggle
const themeToggle = document.getElementById('themeToggle');

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    document.documentElement.classList.toggle('dark');
  });
}

// Task checkbox toggle (front-end only for now — wire up to backend later)
document.querySelectorAll('.task-check').forEach((box) => {
  box.addEventListener('click', () => {
    box.classList.toggle('done');
  });
});