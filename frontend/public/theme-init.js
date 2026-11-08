(() => {
  const match = document.cookie.match(/(?:^|; )evitrack-theme=(dark|light)/);
  if (match?.[1] === 'dark') document.documentElement.classList.add('dark');
})();
