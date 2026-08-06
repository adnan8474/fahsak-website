(function () {
  var lang = document.documentElement.lang === 'en' ? 'en' : 'ar';
  function t(ar, en) { return lang === 'en' ? en : ar; }
  var cats = [
    { max: 18.5, ar: 'نقص في الوزن', en: 'Underweight', cls: 'blue' },
    { max: 25,   ar: 'وزن طبيعي',    en: 'Normal weight', cls: 'teal' },
    { max: 30,   ar: 'زيادة في الوزن', en: 'Overweight', cls: 'amber' },
    { max: Infinity, ar: 'سمنة',     en: 'Obesity', cls: 'rose' }
  ];
  function calc() {
    var w = parseFloat(document.getElementById('bmi-weight').value);
    var h = parseFloat(document.getElementById('bmi-height').value);
    var out = document.getElementById('bmi-result');
    if (!w || !h || w <= 0 || h <= 0 || h > 260 || w > 500) { out.style.display = 'none'; return; }
    var m = h / 100;
    var bmi = w / (m * m);
    var c = cats.filter(function (x) { return bmi < x.max; })[0];
    out.querySelector('.tool-big').textContent = bmi.toFixed(1);
    var cat = out.querySelector('.tool-cat');
    cat.textContent = t(c.ar, c.en);
    cat.className = 'tool-cat tool-' + c.cls;
    out.style.display = 'block';
  }
  var btn = document.getElementById('bmi-calc');
  if (btn) btn.addEventListener('click', calc);
  ['bmi-weight', 'bmi-height'].forEach(function (id) {
    var e = document.getElementById(id);
    if (e) e.addEventListener('keyup', function (ev) { if (ev.key === 'Enter') calc(); });
  });
})();
