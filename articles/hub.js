/* Sihtak article library: search, topic filter and sort for the hub.

   Every card is already in the page, so nothing is fetched and nothing is
   re-rendered. Filtering toggles [hidden] on cards that exist, which keeps the
   markup, the links and the crawlable state identical whether or not this file
   ever runs. With JS off the reader still gets the full list plus chips that
   behave as ordinary links to the category pages. */
(function () {
  var grid = document.getElementById('hubGrid');
  if (!grid) return;

  var box = document.getElementById('artSearch');
  var none = document.getElementById('artNone');
  var countEl = document.getElementById('hubCount');
  var clearBtn = document.getElementById('hubClear');
  var heading = document.getElementById('hubHeading');
  var bar = document.getElementById('hubBar');
  var chips = [].slice.call(document.querySelectorAll('.hub-chip'));
  var sorts = [].slice.call(document.querySelectorAll('.hub-sort'));

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

  /* Read every card once. The haystack is built from what is already on the
     card plus the keyword list the builder attached, so the page carries no
     duplicate copy of its own text. */
  var items = [].slice.call(grid.children).map(function (el, i) {
    var h = el.querySelector('h3');
    var p = el.querySelector('p');
    var c = el.querySelector('.art-chip');
    return {
      el: el,
      i: i,
      cat: el.getAttribute('data-cat') || '',
      title: h ? h.textContent.trim() : '',
      hay: norm([h && h.textContent, p && p.textContent, c && c.textContent,
                 el.getAttribute('data-k')].join(' '))
    };
  });
  var total = items.length;
  var allLabel = heading ? heading.textContent : '';
  var lang = document.documentElement.lang || 'en';
  var state = { cat: '', q: '', sort: 'new' };

  function tpl(s, n, t) {
    return String(s || '').replace('{n}', n).replace('{t}', t);
  }

  function paint() {
    var terms = state.q ? state.q.split(/\s+/) : [];
    var shown = 0;
    for (var i = 0; i < total; i++) {
      var it = items[i];
      var ok = !state.cat || it.cat === state.cat;
      for (var j = 0; ok && j < terms.length; j++) {
        if (it.hay.indexOf(terms[j]) === -1) ok = false;
      }
      it.el.hidden = !ok;
      if (ok) shown++;
    }

    var filtered = !!(state.cat || state.q);
    if (none) none.hidden = shown !== 0;
    if (countEl) {
      countEl.textContent = filtered
        ? tpl(countEl.getAttribute('data-tpl-some'), shown, total)
        : tpl(countEl.getAttribute('data-tpl-all'), total, total);
    }
    if (clearBtn) clearBtn.hidden = !filtered;
    if (heading) {
      var on = state.cat ? grid.ownerDocument.querySelector(
        '.hub-chip[data-cat="' + state.cat + '"]') : null;
      heading.textContent = on ? on.getAttribute('data-name') : allLabel;
    }
    sync();
  }

  function applySort() {
    var order = items.slice();
    if (state.sort === 'az') {
      order.sort(function (a, b) { return a.title.localeCompare(b.title, lang); });
    } else {
      order.sort(function (a, b) { return a.i - b.i; });
    }
    var frag = document.createDocumentFragment();
    order.forEach(function (it) { frag.appendChild(it.el); });
    grid.appendChild(frag);
  }

  /* Keep the address bar in step so a filtered view can be shared or
     reloaded. replaceState, not pushState: the back button should leave the
     hub, not walk back through every keystroke. */
  function sync() {
    if (!window.history || !history.replaceState) return;
    var p = [];
    if (state.cat) p.push('cat=' + encodeURIComponent(state.cat));
    if (box && box.value.trim()) p.push('q=' + encodeURIComponent(box.value.trim()));
    if (state.sort !== 'new') p.push('sort=' + state.sort);
    history.replaceState(null, '', location.pathname + (p.length ? '?' + p.join('&') : ''));
  }

  /* The chip strip scrolls sideways, so an active chip arriving from a ?cat=
     link can be off screen. Nudge the strip, never the page. */
  function revealChip(el) {
    if (!el) return;
    var run = function () {
      var strip = document.getElementById('hubFilters');
      if (!strip) return;
      var er = el.getBoundingClientRect(), sr = strip.getBoundingClientRect();
      if (er.left < sr.left) strip.scrollLeft -= (sr.left - er.left) + 16;
      else if (er.right > sr.right) strip.scrollLeft += (er.right - sr.right) + 16;
    };
    run();
    /* Chip widths only settle once the web font has swapped in. Measuring
       once against fallback metrics stops the strip short of the chip, so
       measure again when the fonts have finished either way. */
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(run);
  }

  function setCat(cat) {
    state.cat = cat;
    var active = null;
    chips.forEach(function (c) {
      var on = (c.getAttribute('data-cat') || '') === cat;
      c.classList.toggle('hub-chip--on', on);
      c.setAttribute('aria-pressed', on ? 'true' : 'false');
      if (on) active = c;
    });
    revealChip(active);
  }

  function setSort(s) {
    state.sort = s;
    sorts.forEach(function (b) {
      var on = b.getAttribute('data-sort') === s;
      b.classList.toggle('hub-sort--on', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    applySort();
  }

  chips.forEach(function (chip) {
    chip.addEventListener('click', function (ev) {
      /* Modified clicks keep their normal meaning: open the real category
         page in a tab. */
      if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
      ev.preventDefault();
      setCat(chip.getAttribute('data-cat') || '');
      paint();
      var top = grid.getBoundingClientRect().top;
      var off = window.innerWidth <= 640 ? 170 : 200;
      if (top < off) window.scrollTo(0, window.pageYOffset + top - off);
    });
  });

  sorts.forEach(function (b) {
    b.addEventListener('click', function () {
      setSort(b.getAttribute('data-sort'));
      sync();
    });
  });

  if (box) {
    var timer;
    box.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        var v = norm(box.value.trim());
        state.q = v.length < 2 ? '' : v;
        paint();
      }, 120);
    });
    /* Escape clears the box the way a search field is expected to. */
    box.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && box.value) {
        box.value = ''; state.q = ''; paint();
      }
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', function () {
      if (box) box.value = '';
      state.q = '';
      setCat('');
      paint();
      if (box) box.focus();
    });
  }

  /* Shadow under the bar only once it is actually stuck to the nav. */
  if (bar) {
    var ticking = false;
    var onScroll = function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        var navH = window.innerWidth <= 640 ? 56 : 64;
        bar.classList.toggle('hub-toolbar--stuck',
          bar.getBoundingClientRect().top <= navH + 1);
        ticking = false;
      });
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  var u = new URLSearchParams(location.search);
  var c0 = u.get('cat') || '';
  var q0 = u.get('q') || '';
  if (c0 && chips.some(function (c) { return c.getAttribute('data-cat') === c0; })) setCat(c0);
  if (q0 && box) { box.value = q0; state.q = norm(q0.trim()); }
  if (u.get('sort') === 'az') setSort('az');
  paint();
})();
