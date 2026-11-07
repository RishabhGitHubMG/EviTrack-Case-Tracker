document.addEventListener('DOMContentLoaded', () => {
  const password = document.getElementById('id_password1');
  const toggle = document.getElementById('togglePassword1Btn');
  const icon = document.getElementById('togglePassword1Icon');
  const bar = document.getElementById('strengthBar');
  const text = document.getElementById('strengthText');
  const rules = [
    [document.getElementById('rule-length'), value => value.length >= 8],
    [document.getElementById('rule-cases'), value => /[A-Z]/.test(value) && /[a-z]/.test(value)],
    [document.getElementById('rule-number'), value => /[0-9]/.test(value)],
    [document.getElementById('rule-special'), value => /[^A-Za-z0-9]/.test(value)],
  ];

  if (toggle && password) {
    toggle.addEventListener('click', () => {
      const visible = password.type === 'password';
      password.type = visible ? 'text' : 'password';
      icon.className = visible ? 'bi bi-eye-slash' : 'bi bi-eye';
    });
  }

  if (!password || !bar || !text) return;
  password.addEventListener('input', () => {
    const value = password.value;
    let score = 0;
    rules.forEach(([element, passes]) => {
      const passed = passes(value);
      if (passed) score += 25;
      updateRule(element, passed);
    });
    bar.style.width = `${score}%`;
    const levels = [
      [25, 'Weak', 'bg-danger', 'text-danger'],
      [50, 'Moderate', 'bg-warning', 'text-warning'],
      [75, 'Good', 'bg-info', 'text-info'],
      [100, 'Strong', 'bg-success', 'text-success'],
    ];
    const [limit, label, barClass, textClass] = levels.find(([limit]) => score <= limit);
    bar.className = `progress-bar ${barClass}`;
    text.textContent = label;
    text.className = `small ${textClass} fw-semibold`;
  });

  function updateRule(element, passed) {
    if (!element) return;
    element.className = passed ? 'text-success fw-medium' : 'text-muted';
  }
});
