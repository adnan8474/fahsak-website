(function () {
  var lang = document.documentElement.lang === 'en' ? 'en' : 'ar';
  function t(ar, en) { return lang === 'en' ? en : ar; }
  // conventional -> SI factor and SI unit label. Creatinine uses umol/L.
  var A = {
    glucose:      { ar: 'سكر الدم (الغلوكوز)', en: 'Glucose', conv: 'mg/dL', si: 'mmol/L', f: 0.0555 },
    cholesterol:  { ar: 'الكوليسترول (كلي/LDL/HDL)', en: 'Cholesterol (total/LDL/HDL)', conv: 'mg/dL', si: 'mmol/L', f: 0.02586 },
    triglycerides:{ ar: 'الدهون الثلاثية', en: 'Triglycerides', conv: 'mg/dL', si: 'mmol/L', f: 0.01129 },
    creatinine:   { ar: 'الكرياتينين', en: 'Creatinine', conv: 'mg/dL', si: 'µmol/L', f: 88.4 },
    // Urea and BUN are different numbers for the same test: urea mg/dL is
    // about 2.14 times BUN mg/dL, so each needs its own factor.
    urea:         { ar: 'اليوريا (Urea)', en: 'Urea', conv: 'mg/dL', si: 'mmol/L', f: 0.1665 },
    bun:          { ar: 'نتروجين اليوريا (BUN)', en: 'Blood urea nitrogen (BUN)', conv: 'mg/dL', si: 'mmol/L', f: 0.357 }
  };
  function decimals(unit) { return unit === 'µmol/L' ? 0 : 2; }
  function calc() {
    var key = document.getElementById('lu-analyte').value;
    var val = parseFloat(document.getElementById('lu-value').value);
    var dir = (document.querySelector('input[name="lu-dir"]:checked') || {}).value || 'toSI';
    var out = document.getElementById('lu-result');
    var a = A[key];
    if (!a || isNaN(val) || val < 0) { out.style.display = 'none'; return; }
    var res, fromU, toU;
    if (dir === 'toSI') { res = val * a.f; fromU = a.conv; toU = a.si; }
    else { res = val / a.f; fromU = a.si; toU = a.conv; }
    var d = dir === 'toSI' ? decimals(a.si) : 2;
    out.querySelector('.tool-big').textContent = res.toFixed(d);
    out.querySelector('.tool-unit').textContent = toU;
    out.querySelector('.tool-sub').textContent = t(
      val + ' ' + fromU + ' يساوي ' + res.toFixed(d) + ' ' + toU + ' في تحليل ' + a.ar + '.',
      val + ' ' + fromU + ' equals ' + res.toFixed(d) + ' ' + toU + ' for ' + a.en + '.'
    );
    out.style.display = 'block';
  }
  ['lu-analyte'].forEach(function (id) { var e = document.getElementById(id); if (e) e.addEventListener('change', calc); });
  var pre = document.querySelector('[data-lu-preset]');
  if (pre) { var sel = document.getElementById('lu-analyte'); if (sel && A[pre.getAttribute('data-lu-preset')]) sel.value = pre.getAttribute('data-lu-preset'); }
  var btn = document.getElementById('lu-calc');
  if (btn) btn.addEventListener('click', calc);
  var v = document.getElementById('lu-value');
  if (v) v.addEventListener('keyup', function (ev) { if (ev.key === 'Enter') calc(); });
})();
