/* Sihtak article search. Filters a prebuilt index client-side: no backend,
   no third-party search, and it works on the Arabic and English hubs alike. */
(function () {
  var box = document.getElementById('artSearch');
  if (!box) return;
  var results = document.getElementById('artResults');
  var none = document.getElementById('artNone');
  var deflt = document.getElementById('artDefault');
  var index = null, ready = false;

  var base = location.pathname.indexOf('/en/') === 0 ? '/en/articles/' : '/articles/';

  function load() {
    if (ready) return Promise.resolve();
    return fetch(base + 'search-index.json')
      .then(function (r) { return r.json(); })
      .then(function (j) { index = j; ready = true; });
  }

  /* Strip Arabic diacritics and normalise alef/ya/ta-marbuta so that a search
     for "امراض" still matches "أمراض". */
  function norm(s) {
    return (s || '')
      .toLowerCase()
      .replace(/[\u064B-\u0652\u0670\u0640]/g, '')
      .replace(/[\u0622\u0623\u0625\u0671]/g, '\u0627')
      .replace(/\u0649/g, '\u064A')
      .replace(/\u0629/g, '\u0647');
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (m) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
    });
  }

  function render(list) {
    results.innerHTML = list.map(function (a) {
      return '<a class="art-card visible" href="' + a.u + '">' +
        '<span class="art-chip">' + esc(a.c) + '</span>' +
        '<h3>' + esc(a.t) + '</h3>' +
        '<p>' + esc(a.d) + '</p></a>';
    }).join('');
  }

  function run() {
    var q = norm(box.value.trim());
    if (q.length < 2) {
      results.hidden = true; none.hidden = true; deflt.hidden = false;
      return;
    }
    load().then(function () {
      var terms = q.split(/\s+/);
      var hits = index.filter(function (a) {
        var hay = norm(a.t + ' ' + a.d + ' ' + a.c + ' ' + a.k);
        return terms.every(function (t) { return hay.indexOf(t) !== -1; });
      }).slice(0, 40);
      deflt.hidden = true;
      render(hits);
      results.hidden = hits.length === 0;
      none.hidden = hits.length !== 0;
    });
  }

  var timer;
  box.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(run, 120);
  });
  box.addEventListener('focus', load);

  var pre = new URLSearchParams(location.search).get('q');
  if (pre) { box.value = pre; run(); }
})();
