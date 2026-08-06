(function () {
  var lang = document.documentElement.lang === 'en' ? 'en' : 'ar';
  function t(ar, en) { return lang === 'en' ? en : ar; }
  // eAG(mg/dL) = 28.7 * A1c - 46.7 ; mmol/L = eAG / 18.0
  function calc() {
    var a1c = parseFloat(document.getElementById('a1c-value').value);
    var out = document.getElementById('a1c-result');
    if (!a1c || a1c < 3 || a1c > 20) { out.style.display = 'none'; return; }
    var mgdl = 28.7 * a1c - 46.7;
    var mmol = mgdl / 18.0;
    out.querySelector('.tool-big').textContent = Math.round(mgdl);
    out.querySelectorAll('.tool-val')[0].textContent = Math.round(mgdl) + ' mg/dL';
    out.querySelectorAll('.tool-val')[1].textContent = mmol.toFixed(1) + ' mmol/L';
    // rough band note
    var band = a1c < 5.7 ? t('ضمن المعدل الطبيعي عموماً', 'generally within the normal range')
      : a1c < 6.5 ? t('ضمن نطاق ما قبل السكري عموماً', 'generally within the prediabetes range')
      : t('ضمن نطاق السكري عموماً', 'generally within the diabetes range');
    out.querySelector('.tool-sub').textContent = t(
      'قيمة A1c هذه ' + band + '. هذا تقدير عام والطبيب هو من يفسر نتيجتك.',
      'This A1c value is ' + band + '. This is a general estimate and your doctor interprets your result.'
    );
    out.style.display = 'block';
  }
  var btn = document.getElementById('a1c-calc');
  if (btn) btn.addEventListener('click', calc);
  var e = document.getElementById('a1c-value');
  if (e) e.addEventListener('keyup', function (ev) { if (ev.key === 'Enter') calc(); });
})();
