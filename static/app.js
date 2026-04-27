document.querySelectorAll('button.copy').forEach(btn => {
  btn.addEventListener('click', async () => {
    const link = btn.dataset.link;
    try {
      await navigator.clipboard.writeText(link);
      const original = btn.textContent;
      btn.textContent = 'Copied ✓';
      btn.classList.add('copied');
      setTimeout(() => {
        btn.textContent = original;
        btn.classList.remove('copied');
      }, 1500);
    } catch {
      window.prompt('Copy this link:', link);
    }
  });
});
